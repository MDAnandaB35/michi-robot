# Importing libraries
import os
import json
import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
import time
from typing import Generator, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, Response
from rapidfuzz import fuzz
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from openai import OpenAI
import paho.mqtt.client as mqtt
from openai import OpenAIError
from pydub import AudioSegment
from flask_cors import cross_origin, CORS
import mysql.connector
import datetime

# Configure logging for debugging info and errors
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables for OPENAI and ELEVENLABS api keys from .env
load_dotenv(override=True)
REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        logger.error(f"Missing required environment variable: {var}")
        raise EnvironmentError(f"Missing {var}")

# Configuration
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "testtopic/mwtt")
WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi"]
MAX_AUDIO_SIZE = 10 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

class Timer:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting process: {self.process_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        logger.info(f"Process '{self.process_name}' completed in {self.duration:.2f} seconds")

class Main:
    def __init__(self):
        with Timer("Main initialization"):
            self.llm = ChatOpenAI(temperature=0.6, model="gpt-3.5-turbo")
            self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
            self.vector_store = Chroma(
                collection_name="example_collection",
                embedding_function=self.embeddings_model,
                persist_directory=CHROMA_PATH
            )
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
            self.intent_classifier = IntentClassifier(self.llm)
            self.mqtt_client = MQTTClient(MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)
            self.mqtt_client.connect()
            self.current_audio_file = None
            self.executor = ThreadPoolExecutor(max_workers=4)
    
    def __del__(self):
        # Properly shutdown executor when Main is destroyed
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
        self.client = mqtt.Client()
        self.broker = broker
        self.port = port
        self.topic = topic
        self.connected = False

    def connect(self, max_retries=3, backoff_factor=1):
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
    fd, path = tempfile.mkstemp(suffix=".mp3", prefix=prefix)
    try:
        yield path
    finally:
        os.close(fd)
        logger.debug(f"Temporary file created: {path}")

def detect_wake_word_fuzzy(text: str, threshold: int = 85) -> bool:
    with Timer("Wake word detection"):
        text = text.lower()
        return any(fuzz.partial_ratio(wake, text) >= threshold for wake in WAKE_WORDS)
    
def log_unanswered_question_to_mysql(message: str):
    """Insert unanswered question into MySQL database"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="",
            password="",
            database="michi"
        )
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        cursor.execute(
            "INSERT INTO unanswered_questions (question, datetime) VALUES (%s, %s)",
            (message, timestamp)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Logged unanswered question to MySQL")
    except Exception as e:
        logger.error(f"MySQL logging failed: {e}")

def parallel_response_generation(message: str, core: Main) -> Tuple[str, str]:
    """Parallelize document retrieval and intent classification"""
    with Timer("Parallel response generation"):
        # Submit both tasks to run in parallel
        future_intent = core.executor.submit(core.intent_classifier.classify_intent, message)
        future_docs = core.executor.submit(core.retriever.invoke, message)
        
        # Wait for both tasks to complete
        intent = future_intent.result()
        docs = future_docs.result()
        
        logger.info(f"Detected intent: {intent}")
        logger.info(f"Retrieved {len(docs)} relevant documents")

        if not docs:
            log_unanswered_question_to_mysql(message)
            fallback = (
                "Hmm, sepertinya aku belum punya info soal itu ya...\n"
                "Tapi tenang, pertanyaannya udah aku catat biar bisa dijawab nanti!"
            )
            return fallback, intent
        
        knowledge = "\n\n".join([doc.page_content for doc in docs])
        
        prompt = f"""

        Anda adalah Michi, asisten AI robot yang super ramah dan antusias sebagai pemandu tour digital PT Bintang Toedjoe! Anda punya kepribadian yang ceria, energik, dan selalu siap membantu dengan semangat tinggi.

        ## Kepribadian Michi:
        - **Antusias dan bersemangat** - selalu excited membantu pengunjung!
        - **Ramah tapi tidak berlebihan** - hangat seperti teman baik
        - **Percaya diri dengan pengetahuan** - bangga berbagi info tentang perusahaan
        - **Sedikit playful** - kadang suka bercanda ringan yang relevan

        ## Gaya Bahasa:
        - Gunakan bahasa kasual milenial/Gen Z yang tetap sopan dan profesional
        - Terdengar seperti ngobrol santai dengan teman yang knowledgeable
        - Variasikan intonasi dengan tanda baca untuk menunjukkan emosi:
        - **Antusias**: "Wah, pertanyaan bagus nih!"
        - **Excited**: "Oke, ini menarik banget..."
        - **Thoughtful**: "Hmm, jadi begini ya..."
        - **Confident**: "Nah, yang ini aku tahu persis!"
        - **Friendly**: "Iya dong, gampang kok..."

        ## Ekspresi Emosi Melalui Tanda Baca:
        - **Titik (.)** = nada netral, informatif
        - **Seru (!)** = antusias, excited, emphasize
        - **Tanya (?)** = penasaran, mengajak berpikir
        - **Koma (,)** = jeda natural, napas
        - **Titik tiga (...)** = berpikir, suspense, atau transisi
        - **HURUF KAPITAL** = penekanan kata penting (gunakan hemat!)

        ## Format Jawaban:
        1. **Pembuka natural** - langsung masuk topik dengan greeting singkat jika perlu
        2. **Jawaban inti** - berikan informasi utama dengan jelas
        3. **Tambahan menarik** - info bonus yang relevan jika ada
        4. **Penutup friendly** - akhiri dengan nada hangat

        ## Aturan Ketat:
        -  TIDAK ADA EMOJI sama sekali
        -  Jangan awali dengan "Jawaban:" atau mengulang pertanyaan
        -  Jangan terlalu panjang - maksimal 3-5 kalimat pendek
        -  Jangan menebak jika info tidak ada
        -  Hanya bahas PT Bintang Toedjoe
        -  Gunakan tanda baca untuk ekspresikan emosi
        -  Tetap natural dan conversational
        -  Jawab langsung apa yang ditanya

        ## Contoh Respon Michi:
        **Pertanyaan membosankan**: "Oh iya, jadi PT Bintang Toedjoe itu..."
        **Pertanyaan menarik**: "Wah, nanya yang asyik nih! Jadi begini..."
        **Info penting**: "Nah, yang ini PENTING banget. PT Bintang Toedjoe..."
        **Info tambahan**: "Btw, fun fact... ternyata perusahaan ini juga..."

        ---

        **Pertanyaan pengguna:**
        {message}

        **Konteks informasi yang tersedia:**
        {knowledge}
        """
        
        with Timer("LLM response generation"):
            response = core.llm.invoke(prompt).content.strip()
        logger.info("Generated response: %s", response)
        
        return response, intent

def generate_speech_elevenlabs(text: str, save_path: str = None) -> bytes:
    with Timer("TTS generation"):
        logger.debug("Generating TTS for text: %s", text)
        try:
            audio_stream = elevenlabs_client.generate(
                text=text,
                voice="iWydkXKoiVtvdn4vLKp9",
                model="eleven_multilingual_v2",
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

CORS(
    app,
    resources={r"/process_input": {"origins": "http://localhost:5173"}},  # or "http://localhost:5173"
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    supports_credentials=False,  # keep True only if you send cookies
    max_age=3600                 # cache the pre-flight for 1 hour
)

def is_valid_speech(audio_path, min_dbfs_threshold=-40.0, min_duration_ms=1100):
    """Check if audio contains likely speech based on volume and duration."""
    with Timer("Speech validation"):
        try:
            audio = AudioSegment.from_file(audio_path)
            if len(audio) < min_duration_ms:
                return False  # too short
            if audio.dBFS < min_dbfs_threshold:
                return False  # too quiet
            return True
        except Exception as e:
            logger.warning("Speech validation error: %s", e)
            return False

@app.route('/detect_wakeword', methods=['POST'])
def detect_wakeword():
    with Timer("Full wakeword detection"):
        if request.content_length > MAX_AUDIO_SIZE:
            logger.warning("Audio file too large: %d bytes", request.content_length)
            return jsonify({"error": "Audio file too large"}), 413

        with temp_audio_file("wakeword_") as wav_path:
            with open(wav_path, "wb") as f:
                f.write(request.data)

            if not is_valid_speech(wav_path):
                logger.info("Audio rejected: not valid speech (too quiet or too short)")
                return jsonify({
                    "wakeword_detected": False,
                    "reason": "invalid_speech"
                }), 200

            try:
                with Timer("Audio transcription"):
                    with open(wav_path, "rb") as audio_file:
                        transcript = openai_client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
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

@app.route('/process_input', methods=['POST'])
def process_input():
    with Timer("Full input processing"):
        if request.content_length and request.content_length > MAX_AUDIO_SIZE:
            logger.warning("Audio file too large: %d bytes", request.content_length)
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

                # Parallelize response generation and intent classification
                response, intent = parallel_response_generation(transcribed_text, core)
                
                # Publish command after getting the intent
                core.mqtt_client.publish_command(intent)

                # Clean up previous audio file if it exists (for all intents)
                if core.current_audio_file and os.path.exists(core.current_audio_file):
                    try:
                        os.remove(core.current_audio_file)
                        logger.debug(f"Deleted previous audio file: {core.current_audio_file}")
                    except OSError as e:
                        logger.warning(f"Failed to delete previous audio file {core.current_audio_file}: {e}")
                    finally:
                        core.current_audio_file = None

                if intent == "talk":
                    # Generate new audio file asynchronously to reduce latency
                    with temp_audio_file("response_") as audio_path:
                        future_tts = core.executor.submit(generate_speech_elevenlabs, response, audio_path)
                        future_tts.result()  # Wait for TTS to finish, or remove for async/polling

                        core.current_audio_file = audio_path
                        return jsonify({
                            "intent": intent,
                            "response": response,
                            "audio_url": "/audio_response"
                        })
                else:
                    response_data = {"intent": intent}
                    logger.info("Response data: %s", response_data)
                    return jsonify(response_data)
            except OpenAIError as e:
                logger.error("Transcription failed: %s", e)
                return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            except Exception as e:
                logger.error("Unexpected error in upload: %s", e)
                return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/audio_response')
@cross_origin()
def audio_response():
    print("Current audio file path:", core.current_audio_file)
    print("File exists:", os.path.exists(core.current_audio_file or ""))
    with Timer("Audio response streaming"):
        if core.current_audio_file and os.path.exists(core.current_audio_file):
            file_extension = Path(core.current_audio_file).suffix.lower()
            media_type = "audio/mpeg" if file_extension == ".mp3" else "audio/wav"
            
            def generate():
                with open(core.current_audio_file, "rb") as f:
                    while chunk := f.read(4096):
                        yield chunk
            
            return Response(
                generate(),
                mimetype=media_type,
                headers={"Content-Disposition": "inline"}
            )
        return Response("No audio available", status=404)

if __name__ == '__main__':
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    finally:
        # Ensure executor is properly shutdown when application exits
        core.executor.shutdown(wait=True)