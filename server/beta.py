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
    WAKEWORD_FOLDER = os.getenv("WAKEWORD_FOLDER", "wakeword_audio")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "chroma_db")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "testtopic/mwtt")
    WAKE_WORDS = ["michi", "hai michi", "halo michi", "robot michi", "halo"]
    MAX_AUDIO_SIZE = 10 * 1024 * 1024
    RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", 0.6))
    
    # File saving configuration
    SAVE_WAKEWORD = os.getenv("SAVE_WAKEWORD", "NO").upper() == "YES"
    SAVE_RESPONSES = os.getenv("SAVE_RESPONSES", "NO").upper() == "YES"

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
os.makedirs(Config.WAKEWORD_FOLDER, exist_ok=True)

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
def detect_wake_word_fuzzy(text, threshold=85):
    text = text.lower()
    for wake in Config.WAKE_WORDS:
        if fuzz.partial_ratio(wake, text) >= threshold:
            return True
    return False

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


# Text-only response generation (without intent classification)
async def text_response_generation(message: str, core: Main) -> str:
    """Generates response from text input without intent classification or audio processing."""
    with Timer("Text response generation"):
        # --- Get relevant documents from vector store ---
        docs_with_scores = await core.vector_store.asimilarity_search_with_relevance_scores(query=message, k=5)
        
        relevant_docs: List[Document] = [doc for doc, score in docs_with_scores if score < Config.RELEVANCE_THRESHOLD]
        
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
                asyncio.create_task(core.db_logger.alog_interaction(message.strip(), response))
            
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

        try:
            # Determine whether to save permanently or use temporary file
            if Config.SAVE_WAKEWORD:
                # Save permanently
                timestamp = int(time.time())
                wakeword_filename = f"wakeword_{timestamp}.wav"
                wakeword_path = os.path.join(Config.WAKEWORD_FOLDER, wakeword_filename)
                
                # Save the received audio as a .wav file
                async with aiofiles.open(wakeword_path, "wb") as f:
                    await f.write(request_data)
                
                logger.info(f"Wakeword audio saved permanently to: {wakeword_path}")
                
                # Use the saved file for transcription
                async with aiofiles.open(wakeword_path, "rb") as audio_file:
                    audio_data = await audio_file.read()
                    
            else:
                # Create a temporary file manually for wakeword detection
                temp_fd, temp_path = tempfile.mkstemp(suffix=".wav", prefix="wakeword_")
                os.close(temp_fd)
                
                try:
                    # Write the audio data to temporary file
                    async with aiofiles.open(temp_path, "wb") as f:
                        await f.write(request_data)
                    
                    logger.info("Wakeword audio saved temporarily")
                    
                    # Read the audio data from temporary file
                    async with aiofiles.open(temp_path, "rb") as audio_file:
                        audio_data = await audio_file.read()
                    
                    wakeword_filename = "temporary_file"
                    
                finally:
                    # Clean up the temporary file
                    try:
                        os.remove(temp_path)
                        logger.debug(f"Temporary wakeword file removed: {temp_path}")
                    except OSError as e:
                        logger.warning(f"Failed to remove temporary wakeword file {temp_path}: {e}")
            
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

            return jsonify({
                "wakeword_detected": wakeword_detected,
                "audio_saved": wakeword_filename,
                "transcription": text
            })
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
                    if Config.SAVE_RESPONSES:
                        # Save response audio permanently
                        persistent_path = os.path.join(Config.UPLOAD_FOLDER, f"response_{int(time.time())}.mp3")
                        await agenerate_speech_elevenlabs(response, persistent_path)
                        core.current_audio_file = persistent_path
                        logger.info(f"Response audio saved permanently to: {persistent_path}")
                    else:
                        # Use temporary file for response audio
                        async with temp_audio_file("response_") as temp_response_path:
                            await agenerate_speech_elevenlabs(response, temp_response_path)
                            core.current_audio_file = temp_response_path
                            logger.info("Response audio saved temporarily")
                    
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

            # Clean up temporary files after streaming (if not saving permanently)
            if not Config.SAVE_RESPONSES and core.current_audio_file:
                try:
                    # Schedule cleanup after response is sent
                    asyncio.create_task(cleanup_temp_response_file(core.current_audio_file))
                    core.current_audio_file = None
                except Exception as e:
                    logger.warning(f"Failed to schedule cleanup of temporary response file: {e}")

            return Response(generate(), mimetype="audio/mpeg", headers={"Content-Disposition": "inline"})
        
        return Response("No audio available or file not found.", status=404)

# Cleanup function for temporary response files
async def cleanup_temp_response_file(file_path: str):
    """Clean up temporary response audio files after a delay."""
    try:
        # Wait a bit to ensure the file is fully streamed
        await asyncio.sleep(2)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temporary response file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary response file {file_path}: {e}")

# Database history endpoint
@app.route('/api/chat-logs', methods=['GET'])
async def get_chat_logs():
    """Endpoint to fetch all chat logs from the database."""
    with Timer("Fetch chat logs from DB"):
        if core.db_logger is None:
            return jsonify({"error": "Database logger is not available. Cannot fetch chat logs."}), 503

        cursor = core.db_logger.collection.find().sort("time", -1)
        chat_logs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string for JSON
            chat_logs.append(doc)
        return jsonify(chat_logs)

if __name__ == '__main__':
    print("🚀 Starting Michi Chatbot Server on port 5000")
    print("🔒 HTTPS is handled by AWS load balancer/reverse proxy")
    print(f"📁 Wakeword audio saving: {'ENABLED' if Config.SAVE_WAKEWORD else 'DISABLED'}")
    print(f"📁 Response audio saving: {'ENABLED' if Config.SAVE_RESPONSES else 'DISABLED'}")
    print(f"📂 Wakeword folder: {Config.WAKEWORD_FOLDER}")
    print(f"📂 Uploads folder: {Config.UPLOAD_FOLDER}")
    app.run(host="0.0.0.0", port=5000, debug=False)
