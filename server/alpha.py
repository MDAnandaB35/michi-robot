# Importing libraries
import os
import json
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
import time
from typing import Generator, Tuple, List
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, Response
from rapidfuzz import fuzz
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from openai import OpenAI, OpenAIError
import paho.mqtt.client as mqtt
from pydub import AudioSegment
from flask_cors import cross_origin, CORS
import mysql.connector
import datetime
from mysql.connector.pooling import MySQLConnectionPool

# --- CHANGE: Centralized Configuration Class ---
class Config:
    """Centralized configuration for the application."""
    load_dotenv(override=True)

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    # Paths
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")

    # MQTT
    MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "testtopic/mwtt")

    # Application Logic
    WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi"]
    MAX_AUDIO_SIZE = 10 * 1024 * 1024
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.7)) # Crucial for RAG quality

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Validate essential environment variables
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
for var in REQUIRED_ENV_VARS:
    if not getattr(Config, var):
        logger.error(f"Missing required environment variable: {var}")
        raise EnvironmentError(f"Missing required environment variable: {var}")

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)


# Initialize Clients
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
elevenlabs_client = ElevenLabs(api_key=Config.ELEVENLABS_API_KEY)

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

class Main:
    def __init__(self):
        with Timer("Main initialization"):
            self.llm = ChatOpenAI(temperature=0.6, model="gpt-3.5-turbo")
            self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
            self.vector_store = Chroma(
                collection_name="example_collection",
                embedding_function=self.embeddings_model,
                persist_directory=Config.CHROMA_PATH
            )
            # The retriever itself is fine, we will call a different method for relevance search
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self.intent_classifier = IntentClassifier(self.llm)
            self.mqtt_client = MQTTClient(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_TOPIC)
            self.mqtt_client.connect()
            self.current_audio_file = None
            self.executor = ThreadPoolExecutor(max_workers=4)

    def __del__(self):
        self.executor.shutdown(wait=True)

class IntentClassifier:
    def __init__(self, llm):
        self.llm = llm

    def classify_intent(self, message: str) -> str:
        with Timer("Intent classification"):
            prompt = f"""
            Klasifikasi input user menjadi salah satu dari intent berikut:
            - dance (untuk perintah joget/dansa)
            - wave (untuk sapaan/sampai jumpa)
            - talk (untuk percakapan biasa)

            Hanya jawab dengan satu kata: dance, wave, atau talk.
            Jangan gunakan tanda baca atau teks tambahan.

            Input: {message}
            Output: """
            try:
                response = self.llm.invoke(prompt).content.strip().lower()
                return response if response in ["dance", "wave", "talk"] else "talk"
            except OpenAIError as e:
                logger.error(f"LLM intent classification failed: {e}")
                return "talk"

class MQTTClient:
    def __init__(self, broker: str, port: int, topic: str):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.broker = broker
        self.port = port
        self.topic = topic
        self.connected = False

    def connect(self, max_retries=3, backoff_factor=1):
        # ... (rest of the MQTTClient class is unchanged)
        with Timer("MQTT connection"):
            retries = 0
            while retries < max_retries:
                try:
                    self.client.connect(self.broker, self.port, 60)
                    self.client.loop_start()
                    self.connected = True
                    return
                except Exception as e:
                    retries += 1
                    delay = backoff_factor * (2 ** retries)
                    logger.warning(f"MQTT connection failed (attempt {retries}/{max_retries}): {e}")
                    time.sleep(delay)
            logger.error("MQTT connection failed after retries")
            self.connected = False

    def publish_command(self, intent: str):
        if not self.connected:
            logger.warning("MQTT not connected, attempting reconnect")
            self.connect()
        if self.connected:
            try:
                with Timer("MQTT publish"):
                    payload = {"response": intent}
                    self.client.publish(self.topic, json.dumps(payload))
                    logger.info(f"Published to {self.topic}: {payload}")
            except Exception as e:
                logger.error(f"MQTT publish failed: {e}")


@contextmanager
def temp_audio_file(prefix: str) -> Generator[str, None, None]:
    # ... (this context manager is unchanged)
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix=prefix)
    try:
        yield path
    finally:
        os.close(fd)
        logger.debug(f"Temporary file created: {path}")

def detect_wake_word_fuzzy(text: str, threshold: int = 85) -> bool:
    # ... (this function is unchanged)
    with Timer("Wake word detection"):
        text = text.lower()
        return any(fuzz.partial_ratio(wake, text) >= threshold for wake in Config.WAKE_WORDS)

# --- CHANGE: Major revision to implement relevance filtering and improved prompting ---
def parallel_response_generation(message: str, core: Main) -> Tuple[str, str]:
    """
    Parallelizes document retrieval and intent classification,
    and includes relevance filtering to prevent hallucinations.
    """
    with Timer("Parallel response generation"):
        future_intent = core.executor.submit(core.intent_classifier.classify_intent, message)
        
        # Use similarity search that returns relevance scores.
        # Note: Chroma's default is L2 distance, where lower scores are better.
        future_docs_with_scores = core.executor.submit(
            core.vector_store.similarity_search_with_relevance_scores,
            query=message,
            k=3
        )

        intent = future_intent.result()
        docs_with_scores = future_docs_with_scores.result()

        # --- CRITICAL RELEVANCE CHECK ---
        # Filter documents based on the score. Tune RELEVANCE_THRESHOLD in Config.
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score < Config.RELEVANCE_THRESHOLD]
        
        logger.info(f"Detected intent: {intent}")
        logger.info(f"Retrieved {len(docs_with_scores)} documents, found {len(relevant_docs)} to be relevant based on threshold < {Config.RELEVANCE_THRESHOLD}.")


        knowledge = "\n\n".join([doc.page_content for doc in relevant_docs])

        # --- IMPROVED SYSTEM PROMPT ---
        prompt = f"""
        Anda adalah Michi, asisten AI robot yang super ramah dan antusias sebagai pemandu tur digital PT Bintang Toedjoe. Anda punya kepribadian yang ceria, energik, dan selalu siap membantu dengan semangat tinggi.

        ## Kepribadian & Gaya Bahasa (Sama seperti sebelumnya)
        - Antusias, ramah, percaya diri, sedikit playful.
        - Bahasa kasual milenial/Gen Z yang sopan.
        - Gunakan tanda baca (!, ?, ...) untuk ekspresi.

        ## Aturan Ketat:
        - **Prioritas UTAMA:** Jawab pertanyaan HANYA jika informasi yang tersedia di bagian "Konteks" secara eksplisit dan relevan menjawab pertanyaan tersebut.
        - **Jika Konteks Tidak Relevan:** Jika informasi yang diberikan tidak ada hubungannya dengan pertanyaan, JANGAN MENJAWAB pertanyaannya. Sebaliknya, katakan dengan sopan bahwa Anda tidak memiliki informasi tersebut dan pengetahuan Anda terbatas pada PT Bintang Toedjoe.
        - **Jangan Menebak:** DILARANG KERAS menebak atau mengarang jawaban jika tidak ada di konteks.
        - TIDAK ADA EMOJI sama sekali.
        - Jangan awali dengan "Jawaban:" atau mengulang pertanyaan.
        - Jaga jawaban tetap singkat, maksimal 3-5 kalimat pendek.
        - Tetap natural dan conversational.
        - Jangan meminta maaf ketika jawaban berhasil ditemukan.

        ---

        **Pertanyaan pengguna:**
        {message}

        **Konteks informasi yang tersedia untuk menjawab pertanyaan:**
        {knowledge}
        """

    with Timer("LLM response generation"):
        response = core.llm.invoke(prompt).content.strip()

    logger.info("Generated response: %s", response)
    return response, intent


def generate_speech_elevenlabs(text: str, save_path: str = None) -> bytes:
    # ... (this function is unchanged)
    with Timer("TTS generation"):
        logger.debug("Generating TTS for text: %s", text)
        try:
            audio_stream = elevenlabs_client.generate(
                text=text,
                voice="iWydkXKoiVtvdn4vLKp9",
                model="eleven_flash_v2_5",
                optimize_streaming_latency=4
            )
            audio_bytes = b"".join(audio_stream) if isinstance(audio_stream, Generator) else audio_stream
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(audio_bytes)
            logger.info("Generated TTS audio (%d bytes)", len(audio_bytes))
            return audio_bytes
        except Exception as e:
            logger.error("ElevenLabs TTS failed: %s", e)
            raise


# Flask App
app = Flask(__name__)
core = Main()

# --- CHANGE: Using a more specific origin if known ---
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}}, # Be specific if possible
    methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type"],
    supports_credentials=True,
)

def is_valid_speech(audio_path, min_dbfs_threshold=-40.0, min_duration_ms=1100):
    # ... (this function is unchanged)
    with Timer("Speech validation"):
        try:
            audio = AudioSegment.from_file(audio_path)
            if len(audio) < min_duration_ms:
                return False
            if audio.dBFS < min_dbfs_threshold:
                return False
            return True
        except Exception as e:
            logger.warning("Speech validation error: %s", e)
            return False

@app.route('/detect_wakeword', methods=['POST'])
def detect_wakeword():
    # ... (this endpoint logic is mostly unchanged, just uses Config)
    with Timer("Full wakeword detection"):
        if request.content_length > Config.MAX_AUDIO_SIZE:
            return jsonify({"error": "Audio file too large"}), 413
        
        # ... rest of the function ...

@app.route('/process_input', methods=['POST'])
def process_input():
    with Timer("Full input processing"):
        if request.content_length and request.content_length > Config.MAX_AUDIO_SIZE:
            return jsonify({"error": "Audio file too large"}), 413

        with temp_audio_file("upload_") as wav_path:
            with open(wav_path, "wb") as f:
                f.write(request.data)
            try:
                with Timer("Audio transcription"):
                    with open(wav_path, "rb") as audio_file:
                        transcript = openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="id"
                        )
                transcribed_text = transcript.text
                logger.info("Transcription result: %s", transcribed_text)

                response, intent = parallel_response_generation(transcribed_text, core)
                
                core.mqtt_client.publish_command(intent)

                if core.current_audio_file and os.path.exists(core.current_audio_file):
                    try:
                        os.remove(core.current_audio_file)
                        logger.debug(f"Deleted previous audio file: {core.current_audio_file}")
                    except OSError as e:
                        logger.warning(f"Failed to delete previous audio file: {e}")
                    finally:
                        core.current_audio_file = None

                if intent == "talk":
                    with temp_audio_file("response_") as temp_path:
                        # Create a non-temporary path that will persist until the next request
                        persistent_path = temp_path.replace(os.path.basename(temp_path), f"response_{int(time.time())}.mp3")
                        generate_speech_elevenlabs(response, persistent_path)
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


@app.route('/audio_response')
def audio_response():
    # ... (this endpoint is mostly unchanged)
    with Timer("Audio response streaming"):
        audio_file = core.current_audio_file
        if audio_file and os.path.exists(audio_file):
            
            def generate():
                with open(audio_file, "rb") as f:
                    while chunk := f.read(4096):
                        yield chunk

            return Response(generate(), mimetype="audio/mpeg", headers={"Content-Disposition": "inline"})
        
        return Response("No audio available or file not found.", status=404)


if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        core.executor.shutdown(wait=True)