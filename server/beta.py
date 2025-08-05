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
    WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi"]
    MAX_AUDIO_SIZE = 10 * 1024 * 1024
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.7))

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "michi_assistant_db")

    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DBNAME = os.getenv("MONGODB_DBNAME", "michi_robot")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "chat_logs")

    ALLOWED_CORS_ORIGINS = os.getenv("ALLOWED_CORS_ORIGINS", "http://localhost:5173")

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
            self.llm = ChatOpenAI(temperature=0.6, model="gpt-4.1-nano-2025-04-14") # LLM Model
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
            self.current_audio_file = None

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

    async def alog_interaction(self, question: str, answer: str):
        doc = {
            "input": question,
            "response": answer,
            "time": datetime.datetime.now()
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

                - dance = jika pengguna menyuruh untuk joget, menari, atau ekspresi kegembiraan fisik.
                - sleep = jika pengguna menyuruh untuk tidur, diam, istirahat, atau mode standby.
                - talk = jika pengguna mengajak bicara, bertanya sesuatu, atau melakukan percakapan biasa.
                - happy = jika pengguna memuji, mengapresiasi, atau memberikan pujian positif.
                - mad = jika pengguna marah, menghina, menyindir kasar, atau menunjukkan emosi negatif.
                - sad = jika pengguna menyampaikan kesedihan, kekecewaan, atau suasana hati yang buruk.

                **Peraturan jawaban**:
                - Hanya jawab dengan **satu kata** dari daftar di atas (tanpa penjelasan).
                - Jawaban harus **tepat satu kata**: `dance`, `sleep`, `talk`, `happy`, `mad`, atau `sad`.

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

                Input: "{message}"
                Output:
                """

            try:
                # --- ASYNC CHANGE: Use ainvoke for non-blocking LLM call ---
                response = await self.llm.ainvoke(prompt)
                content = response.content.strip().lower()
                return content if content in ["dance", "mad", "sad", "sleep", "happy", "talk"] else "talk"
            except OpenAIError as e:
                logger.error(f"LLM intent classification failed: {e}")
                return "talk"

# MQTT client class for publishing commands
class MQTTClient:
    def __init__(self, broker: str, port: int, topic: str):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.broker = broker
        self.port = port
        self.topic = topic
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

    async def apublish_command(self, intent: str): # ASYNC Method
        if not self.connected:
            logger.warning("MQTT not connected, skipping publish.")
            return

        with Timer("MQTT publish"):
            try:
                payload = json.dumps({"response": intent})
                # --- Run blocking publish call in a separate thread ---
                await asyncio.to_thread(self.client.publish, self.topic, payload)
                logger.info(f"Published to {self.topic}: {payload}")
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
def detect_wake_word_fuzzy(text: str, threshold: int = 85) -> bool:
    """Detects if the input text contains a wake word using fuzzy matching."""
    with Timer("Wake word detection"):
        text = text.lower()
        return any(fuzz.partial_ratio(wake, text) >= threshold for wake in Config.WAKE_WORDS)

# Generating response using OpenAI LLM
async def concurrent_response_generation(message: str, core: Main) -> Tuple[str, str]:
    """Runs intent classification and document retrieval concurrently, then generates a response if intent is 'talk'."""
    with Timer("Concurrent response generation"):
        # --- Schedule intent classification and doc retrieval to run at the same time ---
        intent_task = asyncio.create_task(core.intent_classifier.aclassify_intent(message))
        docs_task = asyncio.create_task(
            core.vector_store.asimilarity_search_with_relevance_scores(query=message, k=3)
        )

        # --- Wait for both concurrent tasks to complete ---
        intent, docs_with_scores = await asyncio.gather(intent_task, docs_task)

        if intent != "talk":
            logger.info("Intent is not 'talk'; skipping LLM response generation.")
            return None, intent

        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score < Config.RELEVANCE_THRESHOLD]
        
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

                # Send Q n A to the database logger
                if core.db_logger is not None:
                    asyncio.create_task(core.db_logger.alog_interaction(transcribed_text, response))
                
                # Publish to MQTT in the background
                asyncio.create_task(core.mqtt_client.apublish_command(intent))

                if core.current_audio_file and os.path.exists(core.current_audio_file):
                    try:
                        os.remove(core.current_audio_file)
                        logger.debug(f"Deleted previous audio file: {core.current_audio_file}")
                    except OSError as e:
                        logger.warning(f"Failed to delete previous audio file: {e}")
                    finally:
                        core.current_audio_file = None

                if intent == "talk":
                    persistent_path = os.path.join(Config.UPLOAD_FOLDER, f"response_{int(time.time())}.mp3")
                    await agenerate_speech_elevenlabs(response, persistent_path)
                    core.current_audio_file = persistent_path
                    
                    return jsonify({
                        "intent": intent,
                        "response": response,
                        "audio_url": "/audio_response"
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
        audio_file = core.current_audio_file
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
    """Endpoint to fetch the last 10 chat logs from the database."""
    with Timer("Fetch chat logs from DB"):
        if core.db_logger is None:
            return jsonify({"error": "Database logger is not available. Cannot fetch chat logs."}), 503

        cursor = core.db_logger.collection.find().sort("time", -1).limit(10)
        chat_logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON
            chat_logs.append(doc)
        return jsonify(chat_logs)

if __name__ == '__main__':
    print("🚀 Starting Michi Chatbot Server on port 5000")
    print("🔒 HTTPS is handled by AWS load balancer/reverse proxy")
    app.run(host="0.0.0.0", port=5000, debug=False)
