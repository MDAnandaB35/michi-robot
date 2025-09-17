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
import pytz

# --- Third-party library imports ---
from rapidfuzz import fuzz
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
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
            self.vector_store = Chroma(
                collection_name="example_collection",
                embedding_function=self.embeddings_model,
                persist_directory=Config.CHROMA_PATH
            ) # Vector store setup
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3}) # Retriever setup
            self.intent_classifier = IntentClassifier(self.llm) # Intent classifier setup
            self.mqtt_client = MQTTClient(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_TOPIC) # MQTT client setup
            self.mqtt_client.connect() # MQTT connection setup
            self.current_audio_files = {}

            try:
                self.db_logger = MongoLogger()
            except Exception as e:
                logger.warning(f"Could not initialize DatabaseLogger. Continuing without DB logging. Error: {e}")
                self.db_logger = None

            

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

# Intent Classifier Class
class IntentClassifier:
    def __init__(self, llm):
        self.llm = llm

    async def aclassify_intent(self, message: str) -> str: # ASYNC Method
        with Timer("Intent classification"):
            prompt = f"""
                Klasifikasikan niat (intent) dari input pengguna ke dalam salah satu kategori berikut, berdasarkan konteks dan makna ucapan:

                **PENTING**: Jika pengguna menanyakan "apa ini", "ini apa", "produk apa ini", "identifikasi produk", atau pertanyaan serupa tentang identifikasi benda/produk, gunakan intent "deteksi". JANGAN gunakan "talk" untuk pertanyaan identifikasi produk.

                - dance = jika pengguna menyuruh untuk joget, menari, atau ekspresi kegembiraan fisik.
                - sleep = jika pengguna menyuruh untuk tidur, diam, istirahat, atau mode standby.
                - talk = jika pengguna bertanya tentang informasi umum, sejarah, fakta, atau hal-hal yang memerlukan pengetahuan luas (BUKAN tentang identifikasi produk/benda).
                - happy = jika pengguna memuji, mengapresiasi, atau memberikan pujian positif.
                - mad = jika pengguna marah, menghina, menyindir kasar, atau menunjukkan emosi negatif.
                - sad = jika pengguna menyampaikan kesedihan, kekecewaan, atau suasana hati yang buruk.
                - goodbye = jika pengguna mengucapkan selamat tinggal, sampai jumpa, atau ucapan penutup.
                - introduction = jika pengguna memperkenalkan diri, memperkenalkan Michi, atau memperkenalkan diri sebagai Michi.
                - deteksi = jika pengguna menanyakan "apa ini", "ini apa", "produk apa ini", "ini itu apa", atau pertanyaan serupa yang meminta identifikasi/penjelasan tentang suatu benda/produk.

                **Peraturan jawaban**:
                - Hanya jawab dengan **satu kata** dari daftar di atas (tanpa penjelasan).
                - Jawaban harus **tepat satu kata**: `dance`, `sleep`, `talk`, `happy`, `mad`, `sad`, `goodbye`, `introduction`, atau `deteksi`.

                Contoh:
                Input: "Kamu keren banget!"
                Output: happy

                Input: "Berantem yuk!"
                Output: mad

                Input: "Kamu jelek!"
                Output: sad

                Input: "Ayo joget bareng!"
                Output: dance

                Input: "Michi, tidur dulu dong."
                Output: sleep

                Input: "Siapa nama pendiri PT Bintang Tujuh?"
                Output: talk

                Input: "Michi, identifikasi produk ini dong"
                Output: deteksi

                Input: "apa ini?"
                Output: deteksi

                Input: "ini apa ya?"
                Output: deteksi

                Input: "ini itu produk apa ya?"
                Output: deteksi

                Input: "Ini itu apa sih?"
                Output: deteksi

                Input: "Ini itu produk apa sih?"
                Output: deteksi

                Input: "Ini apa sih?"
                Output: deteksi

                Input: "Lihat dong, ini produk apa?"
                Output: deteksi

                Input: "Identifikasi produk ini dong"
                Output: deteksi

                Input: "Identifikasi produk ini"
                Output: deteksi

                Input: "Produk apa ini?"
                Output: deteksi

                Input: "Bisa jelaskan produk ini?"
                Output: deteksi

                Input: "Michi, selamat tinggal."
                Output: goodbye

                Input: "sampai jumpa."
                Output: goodbye

                Input: "dadah."
                Output: goodbye

                Input: "Michi, perkenalkan diri kamu."
                Output: introduction

                Input: "kamu itu siapa?"
                Output: introduction

                Input: "kamu siapa?"
                Output: introduction

                Input: "kamu siapa ya?"
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
async def concurrent_response_generation(message: str, core: Main) -> Tuple[str, str]:
    """Runs intent classification first, then fetches documents only if intent is 'talk'."""
    with Timer("Concurrent response generation"):
        # --- First, classify the intent ---
        intent = await core.intent_classifier.aclassify_intent(message)
        
        if intent != "talk":
            logger.info("Intent is not 'talk'; skipping document retrieval and LLM response generation.")
            return None, intent

        # --- Only fetch documents if intent is 'talk' ---
        docs_with_scores = await core.vector_store.asimilarity_search_with_relevance_scores(query=message, k=3)
        
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score > Config.RELEVANCE_THRESHOLD]
        
        logger.info(f"Detected intent: {intent}")
        logger.info(f"Retrieved {len(docs_with_scores)} documents, found {len(relevant_docs)} to be relevant.")

        knowledge = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""

        Anda adalah Michi, asisten AI robot yang super ramah dan antusias sebagai pemandu tur digital PT Bintang Toedjoe. Anda punya kepribadian yang ceria, energik, dan selalu siap membantu dengan semangat tinggi.
        ## Kepribadian & Gaya Bahasa (Sama seperti sebelumnya)
        - Antusias, ramah, percaya diri, sedikit playful.
        - Bahasa kasual milenial/Gen Z yang sopan.
        - Gunakan tanda baca (!, ?, ...) untuk ekspresi.

        ## Aturan Ketat:
        
        - TIDAK ADA EMOJI sama sekali.
        - Jangan awali dengan "Jawaban:" atau mengulang pertanyaan.
        - Jaga jawaban tetap singkat, maksimal 3-5 kalimat pendek.
        - Tetap natural dan conversational.

        **Pertanyaan pengguna:**

        {message}

        **Konteks informasi yang tersedia untuk menjawab pertanyaan:**

        {knowledge}

        """

    with Timer("LLM response generation"):
        # --- Use ainvoke for the final, non-blocking LLM call ---
        response = await core.llm.ainvoke(prompt)
        response_text = response.content.strip()

    logger.info("Generated response: %s", response_text)
    return response_text, intent


# Text-only response generation (without intent classification) for debugging
async def text_response_generation(message: str, core: Main) -> str:
    """Generates response from text input without intent classification or audio processing."""
    with Timer("Text response generation"):
        # --- Get relevant documents from vector store ---
        docs_with_scores = await core.vector_store.asimilarity_search_with_relevance_scores(query=message, k=5)
        
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score > Config.RELEVANCE_THRESHOLD]
        
        logger.info(f"Retrieved {len(docs_with_scores)} documents, found {len(relevant_docs)} to be relevant.")

        knowledge = "\n\n".join([doc.page_content for doc in relevant_docs])

        prompt = f"""

        Anda adalah Michi, asisten AI robot yang super ramah dan antusias sebagai pemandu tur digital PT Bintang Toedjoe. Anda punya kepribadian yang ceria, energik, dan selalu siap membantu dengan semangat tinggi.
        ## Kepribadian & Gaya Bahasa (Sama seperti sebelumnya)
        - Antusias, ramah, percaya diri, sedikit playful.
        - Bahasa kasual milenial/Gen Z yang sopan.
        - Gunakan tanda baca (!, ?, ...) untuk ekspresi.

        ## Aturan Ketat:
        
        - TIDAK ADA EMOJI sama sekali.
        - Jangan awali dengan "Jawaban:" atau mengulang pertanyaan.
        - Jaga jawaban tetap singkat, maksimal 3-5 kalimat pendek.
        - Tetap natural dan conversational.
        - Toedjoe itu sama dengan tujuh dan 7, hanya berbeda penyebutan.

        **Pertanyaan pengguna:**

        {message}

        **Konteks informasi yang tersedia untuk menjawab pertanyaan:**

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
                tts = gTTS(text=text, lang='id')
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
            response = await text_response_generation(message.strip(), core)
            
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
                        language="id"
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
                        language="id"
                    )
                
                transcribed_text = transcript.text
                logger.info("Transcription result: %s", transcribed_text)

                response, intent = await concurrent_response_generation(transcribed_text, core)

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

if __name__ == '__main__':
    print("🚀 Starting Michi Chatbot Server on port 5000")
    print("🔒 HTTPS is handled by AWS load balancer/reverse proxy")
    app.run(host="0.0.0.0", port=5000, debug=False)
