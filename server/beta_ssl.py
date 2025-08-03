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
import ssl

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

    # SSL Configuration
    SSL_CERT_PATH = os.getenv("SSL_CERT_PATH", "/etc/letsencrypt/live/your-domain.com/fullchain.pem")
    SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", "/etc/letsencrypt/live/your-domain.com/privkey.pem")
    USE_SSL = os.getenv("USE_SSL", "true").lower() == "true"

    ALLOWED_CORS_ORIGINS = os.getenv("ALLOWED_CORS_ORIGINS", "https://michi-robot.netlify.app")

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
            self.llm = ChatOpenAI(temperature=0.6, model="gpt-3.5-turbo") # LLM Model
            self.embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large") # Embedding Model
            self.vector_store = Chroma(
                persist_directory=Config.CHROMA_PATH,
                embedding_function=self.embeddings_model
            )
            self.intent_classifier = IntentClassifier(self.llm)
            self.mqtt_client = MQTTClient(Config.MQTT_BROKER, Config.MQTT_PORT, Config.MQTT_TOPIC)
            self.current_audio_file = None
            
            # Initialize database logger if MongoDB URI is provided
            if Config.MONGODB_URI:
                self.db_logger = MongoLogger()
            else:
                self.db_logger = None
                logger.warning("MongoDB URI not provided. Database logging disabled.")

# Initialize Quart app and CORS for different origins
app = Quart(__name__)
app = cors(app, allow_origin=Config.ALLOWED_CORS_ORIGINS, allow_credentials=True)
core = Main()

# Add your existing route handlers here...
# (Copy all the route handlers from beta.py)

if __name__ == '__main__':
    if Config.USE_SSL:
        # Check if SSL certificates exist
        if not os.path.exists(Config.SSL_CERT_PATH) or not os.path.exists(Config.SSL_KEY_PATH):
            logger.error(f"SSL certificates not found at {Config.SSL_CERT_PATH} and {Config.SSL_KEY_PATH}")
            logger.info("Falling back to HTTP mode")
            app.run(host="0.0.0.0", port=5000, debug=False)
        else:
            logger.info("Starting server with SSL")
            app.run(
                host="0.0.0.0", 
                port=443, 
                debug=False,
                cert=Config.SSL_CERT_PATH,
                key=Config.SSL_KEY_PATH
            )
    else:
        logger.info("Starting server without SSL")
        app.run(host="0.0.0.0", port=5000, debug=False) 