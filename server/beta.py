# --- Import necessary async libraries ---
import asyncio
import aiofiles
from quart import Quart, request, jsonify, Response 
from motor.motor_asyncio import AsyncIOMotorClient

# --- Standard library imports ---
import os
import json
import logging
import tempfile
from contextlib import asynccontextmanager 
from pathlib import Path
import time
import datetime
from typing import Generator, Tuple, List, AsyncGenerator
import uuid
import pytz

# --- Third-party library imports ---
from rapidfuzz import fuzz
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import fitz  # PyMuPDF for PDF text extraction
from elevenlabs.client import ElevenLabs
# --- Use AsyncOpenAI client ---
from openai import AsyncOpenAI, OpenAIError 
import paho.mqtt.client as mqtt
from pydub import AudioSegment
from quart_cors import cors # Use quart_cors for cross origin server
from gtts import gTTS  # Fallback only for ElevenLabs TTS


# --- Centralized Configuration Class ---
class Config:
    load_dotenv(override=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "testtopic/mwtt")
    WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi", "halo", "michi cantik", "michi pintar", "halo pintar", "hai pintar", "hai", "main yuk", "bermain", "ngobrol"]
    MAX_AUDIO_SIZE = 10 * 1024 * 1024
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.3))
    
    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.8))
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4.1-nano-2025-04-14")

    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "michi_robot")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "chat_logs")
    VECTOR_DB_COLLECTION = os.getenv("VECTOR_DB_COLLECTION", "vector_db")

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Environment Variable Validation ---
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
for var in REQUIRED_ENV_VARS:
    if not getattr(Config, var):
        logger.error(f"Missing required environment variable: {var}")
        raise EnvironmentError(f"Missing required environment variable: {var}")

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Initialize OpenAI and ElevenLabs clients
openai_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)
elevenlabs_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)

# Timer class for measuring execution time
class Timer:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting process: {self.process_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        logger.info(f"Process '{self.process_name}' completed in {duration:.2f} seconds")

# Main application class
class Main:
    def __init__(self):
        with Timer("Main initialization"):
            self.llm = ChatOpenAI(temperature=Config.LLM_TEMPERATURE, model=Config.LLM_MODEL) # LLM Model
            self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large") # Embedding Model
            self.retriever = MongoEmbeddingRetriever(self.embeddings_model) # Retriever backed by MongoDB-stored embeddings
            self.intent_classifier = IntentClassifier(self.llm) # Intent classifier setup
            self.mqtt_client = MQTTClient(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_TOPIC) # MQTT client setup
            self.mqtt_client.connect() # MQTT connection setup
            self.current_audio_files = {}

            try:
                self.db_logger = MongoLogger()
            except Exception as e:
                logger.warning(f"Could not initialize DatabaseLogger. Continuing without DB logging. Error: {e}")
                self.db_logger = None

            try:
                self.knowledge_store = VectorKnowledgeStore()
            except Exception as e:
                logger.warning(f"Could not initialize VectorKnowledgeStore. Continuing without RAG store. Error: {e}")
                self.knowledge_store = None

            

class MongoLogger:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DBNAME]
        self.collection = self.db[Config.MONGODB_COLLECTION]

    async def alog_interaction(self, question: str, answer: str, robot_id: str | None = None):
        # Get current time in Indonesian timezone (UTC+7)
        indonesia_tz = pytz.timezone('Asia/Jakarta')
        current_time = datetime.datetime.now(indonesia_tz)
        
        doc = {
            "input": question,
            "response": answer,
            "time": current_time,
            **({"robot_id": robot_id} if robot_id else {})
        }
        await self.collection.insert_one(doc)

class VectorKnowledgeStore:
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DBNAME]
        self.collection = self.db[Config.VECTOR_DB_COLLECTION]

    async def ainsert_document(self, document: dict) -> str:
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def adelete_document(self, object_id: str) -> int:
        from bson import ObjectId
        result = await self.collection.delete_one({"_id": ObjectId(object_id)})
        return result.deleted_count

    async def aget_document(self, object_id: str) -> dict | None:
        from bson import ObjectId
        doc = await self.collection.find_one({"_id": ObjectId(object_id)})
        return doc

    async def alist_documents(self, user_id: str | None = None, robot_id: str | None = None) -> List[dict]:
        query = {**({"user_id": user_id} if user_id else {}), **({"robot_id": robot_id} if robot_id else {})}
        cursor = self.collection.find(query).sort("uploaded_at", -1)
        docs: List[dict] = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            if "chunks" in doc and isinstance(doc["chunks"], list):
                doc["chunk_count"] = len(doc["chunks"])  # provide count only
                doc.pop("chunks", None)  # remove heavy payload
            docs.append(doc)
        return docs
class MongoEmbeddingRetriever:
    def __init__(self, embeddings_model: OpenAIEmbeddings):
        self.embeddings_model = embeddings_model
        self.client = AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DBNAME]
        self.collection = self.db[Config.VECTOR_DB_COLLECTION]

    async def asearch_with_scores(self, query: str, k: int = 3, robot_id: str | None = None) -> List[Tuple[Document, float]]:
        import numpy as np
        # Compute embedding for query
        query_vec_list = await self.embeddings_model.aembed_query(query)
        query_vec = np.array(query_vec_list, dtype=float)

        # Fetch candidate chunks from MongoDB (filtered by robot_id if provided)
        match_stage = {"$match": {**({"robot_id": robot_id} if robot_id else {})}}
        project_stage = {"$project": {"chunks": 1, "_id": 0}}
        pipeline = [match_stage, project_stage]
        cursor = self.collection.aggregate(pipeline)

        docs_with_scores: List[Tuple[Document, float]] = []
        async for doc in cursor:
            for chunk in (doc.get("chunks") or []):
                emb = np.array(chunk.get("embedding") or [], dtype=float)
                if emb.size == 0 or emb.shape != query_vec.shape:
                    continue
                # cosine similarity
                denom = (np.linalg.norm(query_vec) * np.linalg.norm(emb))
                if denom == 0:
                    continue
                score = float(np.dot(query_vec, emb) / denom)
                docs_with_scores.append((Document(page_content=chunk.get("content", "")), score))

        # Sort by score desc and take top k
        docs_with_scores.sort(key=lambda t: t[1], reverse=True)
        return docs_with_scores[:k]

    async def alist_documents(self, user_id: str | None = None, robot_id: str | None = None) -> List[dict]:
        query = {**({"user_id": user_id} if user_id else {}), **({"robot_id": robot_id} if robot_id else {})}
        cursor = self.collection.find(query).sort("uploaded_at", -1)
        docs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # stringify for JSON
            # reduce payload by excluding embeddings in list view
            if "chunks" in doc and isinstance(doc["chunks"], list):
                doc["chunk_count"] = len(doc["chunks"])
                doc.pop("chunks", None)
            docs.append(doc)
        return docs

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract full text from PDF bytes using PyMuPDF."""
    with Timer("PDF text extraction"):
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texts: List[str] = []
            for page in doc:
                texts.append(page.get_text("text"))
            return "\n".join(texts).strip()
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Naive text chunking by characters with overlap."""
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        if end == text_len:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

# Intent Classifier Class
class IntentClassifier:
    def __init__(self, llm):
        self.llm = llm

    async def aclassify_intent(self, message: str) -> str: # ASYNC Method
        with Timer("Intent classification"):
            prompt = f"""
            Classify the user's intent into one of the following categories, based on context and meaning:

            **IMPORTANT**: If the user asks "what is this", "this is what", "what product is this", "identify this", or any similar request to identify an object/product, always use intent "detect". DO NOT use "talk" for product/object identification.

            - dance = if the user tells the assistant to dance, move, or show joyful physical expression.
            - sleep = if the user tells the assistant to sleep, be quiet, rest, or go into standby mode.
            - talk = if the user asks about general information, knowledge, facts, history, or similar (NOT for product/object identification).
            - happy = if the user gives compliments, appreciation, or positive feedback.
            - mad = if the user is angry, insulting, sarcastic, or shows negative emotions.
            - sad = if the user expresses sadness, disappointment, or a bad mood.
            - goodbye = if the user says farewell, goodbye, see you, or closing phrases.
            - introduction = if the user introduces themselves, asks the assistant to introduce itself, or asks "who are you".
            - detect = if the user asks "what is this", "this is what", "what product is this", "identify this", or similar requests to identify/describe an object or product.

            **Answer rules**:
            - Only answer with **one word** from the list above (no explanation).
            - The answer must be exactly one of: `dance`, `sleep`, `talk`, `happy`, `mad`, `sad`, `goodbye`, `introduction`, `detect`.

            Examples:
            Input: "You are amazing!"
            Output: happy

            Input: "Let’s fight!"
            Output: mad

            Input: "Do a little dance!"
            Output: dance

            Input: "Go to sleep now."
            Output: sleep

            Input: "Who invented the lightbulb?"
            Output: talk

            Input: "Identify this product please."
            Output: detect

            Input: "See you later."
            Output: goodbye

            Input: "Who are you?"
            Output: introduction

            Input: "{message}"
            Output:
        """


            try:
                # --- ASYNC CHANGE: Use ainvoke for non-blocking LLM call ---
                response = await self.llm.ainvoke(prompt)
                content = response.content.strip().lower()
                return content if content in ["dance", "mad", "sad", "sleep", "happy", "talk", "goodbye", "introduction", "deteksi"] else "talk"
            except OpenAIError as e:
                logger.error(f"LLM intent classification failed: {e}")
                return "talk"

# MQTT client class for publishing commands
class MQTTClient:
    def __init__(self, broker: str, port: int, topic_base: str):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.broker = broker
        self.port = port
        self.topic_base = topic_base
        self.connected = False

    def connect(self): # The initial connect can remain blocking
        with Timer("MQTT connection"):
            try:
                self.client.connect(self.broker, self.port, 60)
                self.client.loop_start()
                self.connected = True
            except Exception as e:
                logger.error(f"Initial MQTT connection failed: {e}")
                self.connected = False

    async def apublish_command(self, intent: str, robot_id: str | None): # ASYNC Method
        if not self.connected:
            logger.warning("MQTT not connected, skipping publish.")
            return

        with Timer("MQTT publish"):
            try:
                topic = f"{self.topic_base}/{robot_id}" if robot_id else self.topic_base
                payload = json.dumps({"robot_id": robot_id, "response": intent})
                # --- Run blocking publish call in a separate thread ---
                await asyncio.to_thread(self.client.publish, topic, payload)
                logger.info(f"Published to {topic}: {payload}")
            except Exception as e:
                logger.error(f"MQTT publish failed: {e}")

# Temporary audio file context manager
@asynccontextmanager
async def temp_audio_file(prefix: str) -> AsyncGenerator[str, None]:
    """Async context manager for creating and cleaning up a temporary audio file."""
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix=prefix)
    os.close(fd)
    logger.debug(f"Temporary file created: {path}")
    try:
        yield path
    finally:
        try:
            os.remove(path)
            logger.debug(f"Temporary file removed: {path}")
        except OSError as e:
            logger.error(f"Error removing temporary file {path}: {e}")

# Detecting wake words using fuzzy matching
def detect_wake_word_fuzzy(text, threshold=85):
    text = text.lower()
    for wake in Config.WAKE_WORDS:
        if fuzz.partial_ratio(wake, text) >= threshold:
            return True
    return False

# Generating response using OpenAI LLM
async def concurrent_response_generation(message: str, core: Main, robot_id: str | None = None) -> Tuple[str, str]:
    """Runs intent classification first, then fetches documents only if intent is 'talk'."""
    with Timer("Concurrent response generation"):
        # --- First, classify the intent ---
        intent = await core.intent_classifier.aclassify_intent(message)
        
        if intent != "talk":
            logger.info("Intent is not 'talk'; skipping document retrieval and LLM response generation.")
            return None, intent

        # --- Only fetch documents if intent is 'talk' ---
        docs_with_scores = await core.retriever.asearch_with_scores(query=message, k=3, robot_id=robot_id)
        
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score > Config.RELEVANCE_THRESHOLD]
        
        logger.info(f"Detected intent: {intent}")
        logger.info(f"Retrieved {len(docs_with_scores)} documents, found {len(relevant_docs)} to be relevant.")

        knowledge = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""

        You are Michi, a super friendly and enthusiastic AI robot assistant.
        ## Personality & Style
        - Energetic, friendly, confident, slightly playful.
        - Casual conversational tone, like a polite Gen Z/millennial.
        - Use punctuation (!, ?, ...) for expression.

        ## Strict Rules:
        - NO emojis at all.
        - Do not start with "Answer:" or repeat the question.
        - Keep responses short: maximum 3–5 short sentences.
        - Stay natural and conversational.
        - DO NOT ANSWER any out of context questions, expecially about something specific. If it is a general question, answer it.

        **User question:**

        {message}

        **Available context information to answer the question:**

        {knowledge}

        """

    with Timer("LLM response generation"):
        # --- Use ainvoke for the final, non-blocking LLM call ---
        response = await core.llm.ainvoke(prompt)
        response_text = response.content.strip()

    logger.info("Generated response: %s", response_text)
    return response_text, intent


# Text-only response generation (without intent classification) for debugging
async def text_response_generation(message: str, core: Main, robot_id: str | None = None) -> str:
    """Generates response from text input without intent classification or audio processing."""
    with Timer("Text response generation"):
        # --- Get relevant documents from vector store ---
        docs_with_scores = await core.retriever.asearch_with_scores(query=message, k=5, robot_id=robot_id)
        
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score > Config.RELEVANCE_THRESHOLD]
        
        logger.info(f"Retrieved {len(docs_with_scores)} documents, found {len(relevant_docs)} to be relevant.")

        knowledge = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""

        You are Michi, a super friendly and enthusiastic AI robot assistant.
        ## Personality & Style
        - Energetic, friendly, confident, slightly playful.
        - Casual conversational tone, like a polite Gen Z/millennial.
        - Use punctuation (!, ?, ...) for expression.

        ## Strict Rules:
        - NO emojis at all.
        - Do not start with "Answer:" or repeat the question.
        - Keep responses short: maximum 3–5 short sentences.
        - Stay natural and conversational.
        - DO NOT ANSWER any out of context questions, expecially about something specific. If it is a general question, answer it.

        **User question:**

        {message}

        **Available context information to answer the question:**

        {knowledge}

        """

    with Timer("LLM response generation"):
        # --- Use ainvoke for the final, non-blocking LLM call ---
        response = await core.llm.ainvoke(prompt)
        response_text = response.content.strip()

    logger.info("Generated text response: %s", response_text)
    return response_text


# Generating speech using ElevenLabs TTS with Google TTS fallback
async def agenerate_speech_elevenlabs(text: str, save_path: str) -> None:
    """Generates speech audio from text using ElevenLabs TTS, with Google TTS as a fallback."""
    with Timer("TTS generation"):
        logger.debug("Generating TTS for text: %s", text)
        try:
            # --- Run blocking ElevenLabs call in a separate thread ---
            audio_bytes = await asyncio.to_thread(
                elevenlabs_client.generate,
                text=text,
                voice="iWydkXKoiVtvdn4vLKp9",
                model="eleven_flash_v2_5",
                optimize_streaming_latency=4
            )
            
            # --- Write to file asynchronously ---
            async with aiofiles.open(save_path, "wb") as f:
                if isinstance(audio_bytes, Generator):
                    for chunk in audio_bytes:
                        await f.write(chunk)
                else:
                    await f.write(audio_bytes)

            logger.info("Generated TTS audio and saved to %s", save_path)
        except Exception as e:
            logger.error("ElevenLabs TTS failed: %s. Falling back to Google TTS.", e)
            # Fallback to Google TTS (gTTS)
            try:
                tts = gTTS(text=text, lang='en')
                await asyncio.to_thread(tts.save, save_path)
                logger.info("Generated TTS audio with gTTS and saved to %s", save_path)
            except Exception as gtts_e:
                logger.error("Google TTS (gTTS) also failed: %s", gtts_e)
                raise


# Initialize Quart app and CORS for different origins
app = Quart(__name__)
app = cors(app, allow_origin="*", allow_credentials=False)
core = Main()

@app.route('/', methods=['GET'])
async def root():
    """Root endpoint to handle health checks and basic requests."""
    return jsonify({
        "status": "running",
        "service": "Michi Chatbot Server",
        "timestamp": datetime.datetime.now().isoformat(),
        "endpoints": {
            "text_chat": "/text_chat",
            "detect_wakeword": "/detect_wakeword", 
            "process_input": "/process_input",
            "audio_response": "/audio_response",
            "chat_logs": "/api/chat-logs"
        }
    })

@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return jsonify({"status": "healthy"}), 200

@app.route('/text_chat', methods=['POST'])
async def text_chat():
    """Endpoint to process text input and generate response without audio processing."""
    with Timer("Text chat processing"):
        try:
            # Get JSON data from request
            request_data = await request.get_json()
            
            if not request_data or 'message' not in request_data:
                return jsonify({"error": "Missing 'message' field in request body"}), 400
            
            message = request_data['message']
            robot_id = request_data.get('robot_id') if isinstance(request_data, dict) else None
            if not robot_id or not str(robot_id).strip():
                return jsonify({"error": "robot_id is required"}), 400
            
            if not message or not message.strip():
                return jsonify({"error": "Message cannot be empty"}), 400
            
            # Generate response using text-only function
            response = await text_response_generation(message.strip(), core, robot_id)
            
            # Create response data with timestamp
            response_data = {
                "input": message.strip(),
                "output": response,
                "time": datetime.datetime.now().isoformat()
            }
            
            # Log to MongoDB in the background
            if core.db_logger is not None:
                asyncio.create_task(core.db_logger.alog_interaction(message.strip(), response, robot_id))
            
            logger.info(f"Text chat processed - Input: {message.strip()}, Output: {response}")
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error("Unexpected error in text chat: %s", e, exc_info=True)
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/detect_wakeword', methods=['POST'])
async def detect_wakeword():
    """Endpoint to detect wake word from uploaded audio using speech-to-text and fuzzy matching."""
    with Timer("Full wakeword detection"):
        request_data = await request.get_data()
        # Ensure request_data is bytes
        if isinstance(request_data, str):
            request_data = request_data.encode()
        if len(request_data) > Config.MAX_AUDIO_SIZE:
            logger.warning("Audio file too large: %d bytes", len(request_data))
            return jsonify({"error": "Audio file too large"}), 413

        async with temp_audio_file("wakeword_") as wav_path:
            async with aiofiles.open(wav_path, "wb") as f:
                await f.write(request_data)

            try:
                async with aiofiles.open(wav_path, "rb") as audio_file:
                    audio_data = await audio_file.read()
                with Timer("Audio transcription"):
                    transcript = await openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=("audio.mp3", audio_data),
                        language="en"
                    )
                text = transcript.text
                logger.info("Transcription result: %s", text)

                wakeword_detected = detect_wake_word_fuzzy(text)
                logger.info("Wake word detected: %s", wakeword_detected)

                return jsonify({"wakeword_detected": wakeword_detected})
            except OpenAIError as e:
                logger.error("Transcription failed: %s", e)
                return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            except Exception as e:
                logger.error("Unexpected error in wakeword detection: %s", e)
                return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Receiving audio input
@app.route('/process_input', methods=['POST'])
async def process_input():
    """Endpoint to process user audio input, transcribe, generate response, intent, and TTS if needed."""
    with Timer("Full input processing"):
        request_data = await request.get_data()
        robot_id = request.args.get('robot_id') or request.headers.get('X-Robot-Id')
        if not robot_id or not str(robot_id).strip():
            return jsonify({"error": "robot_id is required"}), 400
        # Ensure request_data is bytes
        if isinstance(request_data, str):
            request_data = request_data.encode()
        if len(request_data) > Config.MAX_AUDIO_SIZE:
            return jsonify({"error": "Audio file too large"}), 413

        async with temp_audio_file("upload_") as wav_path:
            async with aiofiles.open(wav_path, "wb") as f:
                await f.write(request_data)
            
            try:
                # --- Read the file's bytes asynchronously first ---
                async with aiofiles.open(wav_path, "rb") as f:
                    audio_data = await f.read()

                with Timer("Audio transcription"):
                    # --- Pass the raw bytes (in a tuple) to the OpenAI client ---
                    transcript = await openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=("audio.mp3", audio_data), 
                        language="en"
                    )
                
                transcribed_text = transcript.text
                logger.info("Transcription result: %s", transcribed_text)

                response, intent = await concurrent_response_generation(transcribed_text, core, robot_id)

                # Send Q n A to the database logger only when there's a response (intent is "talk")
                if core.db_logger is not None and intent == "talk" and response:
                    asyncio.create_task(core.db_logger.alog_interaction(transcribed_text, response, robot_id))
                
                # Publish to MQTT in the background
                asyncio.create_task(core.mqtt_client.apublish_command(intent, robot_id))

                # Clean previous per-robot audio file
                if robot_id and robot_id in core.current_audio_files:
                    old_path = core.current_audio_files.get(robot_id)
                    if old_path and os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                            logger.debug(f"Deleted previous audio file for {robot_id}: {old_path}")
                        except OSError as e:
                            logger.warning(f"Failed to delete previous audio file for {robot_id}: {e}")
                    core.current_audio_files.pop(robot_id, None)

                if intent == "talk":
                    persistent_path = os.path.join(Config.UPLOAD_FOLDER, f"response_{robot_id or 'default'}_{int(time.time())}.mp3")
                    await agenerate_speech_elevenlabs(response, persistent_path)
                    if robot_id:
                        core.current_audio_files[robot_id] = persistent_path
                    else:
                        core.current_audio_files["default"] = persistent_path
                    
                    return jsonify({
                        "intent": intent,
                        "response": response,
                        "audio_url": f"/audio_response{f'?robot_id={robot_id}' if robot_id else ''}"
                    })
                else:
                    return jsonify({"intent": intent})

            except OpenAIError as e:
                logger.error("Transcription failed: %s", e)
                return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            except Exception as e:
                logger.error("Unexpected error in upload: %s", e, exc_info=True)
                return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

# Sending audio response
@app.route('/audio_response')
async def audio_response():
    """Endpoint to stream the generated audio response file to the client."""
    with Timer("Audio response streaming"):
        robot_id = request.args.get('robot_id')
        if not robot_id or not str(robot_id).strip():
            return Response("robot_id is required", status=400)
        audio_file = None
        if robot_id:
            audio_file = core.current_audio_files.get(robot_id)
        else:
            audio_file = core.current_audio_files.get("default")
        if audio_file and os.path.exists(audio_file):
            
            async def generate():
                async with aiofiles.open(audio_file, "rb") as f:
                    while chunk := await f.read(4096):
                        yield chunk

            return Response(generate(), mimetype="audio/mpeg", headers={"Content-Disposition": "inline"})
        
        return Response("No audio available or file not found.", status=404)

# Database history endpoint
@app.route('/api/chat-logs', methods=['GET'])
async def get_chat_logs():
    """Endpoint to fetch all chat logs from the database."""
    with Timer("Fetch chat logs from DB"):
        if core.db_logger is None:
            return jsonify({"error": "Database logger is not available. Cannot fetch chat logs."}), 503

        try:
            # Require filter by robot_id
            robot_id = request.args.get('robot_id')
            if not robot_id or not str(robot_id).strip():
                return jsonify({"error": "robot_id is required"}), 400
            query = {"robot_id": robot_id}
            # Use ObjectId for more reliable sorting by insertion order
            cursor = core.db_logger.collection.find(query).sort("_id", -1)
            chat_logs = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON
                
                # Format time to Indonesian timezone
                if "time" in doc:
                    try:
                        # Handle different time formats
                        if isinstance(doc["time"], float):
                            # Convert float timestamp to datetime
                            utc_time = datetime.datetime.fromtimestamp(doc["time"], pytz.utc)
                        elif isinstance(doc["time"], datetime.datetime):
                            # Handle datetime objects
                            if doc["time"].tzinfo is None:
                                utc_time = pytz.utc.localize(doc["time"])
                            else:
                                utc_time = doc["time"]
                        else:
                            # Skip if time format is unknown
                            continue
                        
                        # Convert to Indonesian timezone
                        indonesia_time = utc_time.astimezone(pytz.timezone('Asia/Jakarta'))
                        doc["time"] = indonesia_time.isoformat()  # ISO format for frontend Date parsing
                    except Exception as e:
                        logger.warning(f"Could not format time for document {doc.get('_id')}: {e}")
                        # Keep original time if formatting fails
                        pass
                
                chat_logs.append(doc)
            
            logger.info(f"Retrieved {len(chat_logs)} chat logs from database")
            return jsonify(chat_logs)
            
        except Exception as e:
            logger.error(f"Error fetching chat logs: {e}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500

# RAG Knowledge Endpoints
@app.route('/rag/knowledge', methods=['POST'])
async def upload_rag_knowledge():
    """Upload a PDF, generate embeddings per chunk, and store in MongoDB vector_db."""
    if core.knowledge_store is None:
        return jsonify({"error": "Knowledge store is not available"}), 503

    try:
        form = await request.form
        files = await request.files
        user_id = form.get('user_id')
        robot_id = form.get('robot_id')
        filename_override = form.get('filename')
        if not user_id or not str(user_id).strip():
            return jsonify({"error": "user_id is required"}), 400

        file = files.get('file') if files else None
        if file is None:
            return jsonify({"error": "file is required (PDF)"}), 400
        if not (file.filename or '').lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are supported"}), 400

        pdf_bytes = file.read()
        full_text = extract_text_from_pdf_bytes(pdf_bytes)
        if not full_text:
            return jsonify({"error": "Could not extract any text from PDF"}), 400

        texts = chunk_text(full_text, chunk_size=500, overlap=100)
        if not texts:
            return jsonify({"error": "No chunks generated from PDF text"}), 400

        with Timer("Embedding generation"):
            embeddings: List[List[float]] = await core.embeddings_model.aembed_documents(texts)

        now_utc = datetime.datetime.utcnow()
        doc = {
            "user_id": user_id,
            **({"robot_id": robot_id} if robot_id else {}),
            "filename": filename_override or (file.filename or 'document.pdf'),
            "full_text": full_text,
            "chunks": [
                {
                    "chunk_id": str(uuid.uuid4()),
                    "content": content,
                    "embedding": embedding,
                    **({"robot_id": robot_id} if robot_id else {}),
                }
                for content, embedding in zip(texts, embeddings)
            ],
            "uploaded_at": now_utc,
        }

        inserted_id = await core.knowledge_store.ainsert_document(doc)

        return jsonify({"_id": inserted_id, "chunk_count": len(texts)}), 201
    except OpenAIError as e:
        logger.error(f"Embedding generation failed: {e}")
        return jsonify({"error": f"Embedding generation failed: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in RAG upload: {e}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route('/rag/knowledge', methods=['GET'])
async def list_rag_knowledge():
    """List knowledge documents for a user (no embeddings in response)."""
    if core.knowledge_store is None:
        return jsonify({"error": "Knowledge store is not available"}), 503
    try:
        user_id = request.args.get('user_id')
        robot_id = request.args.get('robot_id')
        docs = await core.knowledge_store.alist_documents(user_id=user_id, robot_id=robot_id)
        return jsonify(docs)
    except Exception as e:
        logger.error(f"Error listing RAG knowledge: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@app.route('/rag/knowledge/<object_id>', methods=['DELETE'])
async def delete_rag_knowledge(object_id: str):
    """Delete a knowledge document by its _id and all its vectors (embedded in doc)."""
    if core.knowledge_store is None:
        return jsonify({"error": "Knowledge store is not available"}), 503
    try:
        # Fetch the document to get chroma ids for cleanup
        doc = await core.knowledge_store.aget_document(object_id)
        if doc is None:
            return jsonify({"error": "Document not found"}), 404

        deleted = await core.knowledge_store.adelete_document(object_id)
        return jsonify({"deleted": True})
    except Exception as e:
        logger.error(f"Error deleting RAG knowledge: {e}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

if __name__ == '__main__':
    print("🚀 Starting Michi Chatbot Server on port 5000")
    print("🔒 HTTPS is handled by AWS load balancer/reverse proxy")
    app.run(host="0.0.0.0", port=5000, debug=False)
