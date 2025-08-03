# Michi Chatbot Server

A Python-based chatbot server for the Michi AI assistant, built with Quart (async Flask), OpenAI, and ElevenLabs.

## Features

- 🎤 **Audio Processing**: Speech-to-text and text-to-speech capabilities
- 🤖 **AI Chat**: Powered by OpenAI GPT-3.5-turbo
- 🧠 **Knowledge Base**: Vector search using Chroma DB
- 🎯 **Intent Classification**: Classifies user intents (dance, sleep, talk, happy, mad, sad)
- 📡 **MQTT Integration**: Publishes robot commands
- 📊 **Database Logging**: MongoDB integration for chat history
- 🔒 **HTTPS Ready**: Configured to work with AWS HTTPS setup

## Prerequisites

- Python 3.8+
- OpenSSL (for audio processing)
- FFmpeg (for audio conversion)
- MongoDB (optional, for chat logging)

## Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv ffmpeg portaudio19-dev python3-dev build-essential
```

**CentOS/RHEL:**

```bash
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel gcc ffmpeg portaudio-devel
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python requirements
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the server directory:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# MongoDB (optional)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DBNAME=michi_robot
MONGODB_COLLECTION=chat_logs

# MQTT Configuration
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=testtopic/mwtt

# Vector Search
RELEVANCE_THRESHOLD=0.7

# CORS
ALLOWED_CORS_ORIGINS=https://your-frontend-domain.com
```

## Usage

### Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python3 beta.py
```

The server will start on port 5000. HTTPS is handled by your AWS setup (load balancer, reverse proxy, etc.).

### API Endpoints

- `POST /detect_wakeword` - Detect wake words in audio
- `POST /process_input` - Process user audio input and generate response
- `GET /audio_response` - Stream generated audio response
- `GET /api/chat-logs` - Get chat history from database

## AWS Deployment

### Security Group Configuration

Ensure your EC2 security group allows:

- **Port 5000**: For internal server communication
- **Port 80/443**: Handled by AWS load balancer/reverse proxy

### Load Balancer Setup

1. Create an Application Load Balancer (ALB)
2. Configure HTTPS listener on port 443
3. Add HTTP to HTTPS redirect
4. Target group points to EC2 instance on port 5000
5. Configure SSL certificate in AWS Certificate Manager

### Auto Scaling (Optional)

- Set up Auto Scaling Group for high availability
- Configure health checks on `/api/chat-logs` endpoint
- Set minimum/maximum instance counts

## Development

### Project Structure

```
server/
├── beta.py                 # Main server application
├── requirements.txt        # Python dependencies
├── ingest_database.py      # Database ingestion script
├── data/                   # Knowledge base data
├── chroma_db/             # Vector database
├── uploads/               # Audio file storage
├── server_audio/          # Generated audio files
└── venv/                  # Virtual environment
```

### Key Components

- **Main Class**: Handles LLM, embeddings, and vector store initialization
- **IntentClassifier**: Classifies user intents using OpenAI
- **MQTTClient**: Publishes robot commands
- **MongoLogger**: Logs chat interactions to MongoDB
- **Audio Processing**: Handles speech-to-text and text-to-speech

### Adding New Features

1. **New Intent**: Add to intent classification prompt in `IntentClassifier`
2. **New Endpoint**: Add route decorator to Quart app
3. **New AI Model**: Update LLM initialization in `Main` class
4. **New Database**: Add new database client class

## Troubleshooting

### Common Issues

**Import Errors:**

- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Audio Processing Errors:**

- Install FFmpeg: `sudo apt-get install ffmpeg`
- Install PortAudio: `sudo apt-get install portaudio19-dev`

**MongoDB Connection:**

- Check MongoDB URI in `.env`
- Ensure MongoDB service is running
- Check network connectivity

**API Key Errors:**

- Verify API keys in `.env` file
- Check API key permissions and quotas

### Logs

The server uses Python logging. Check console output for:

- Request processing times
- Error messages
- API call results
- Database operations

## Performance Optimization

- **Async Processing**: All I/O operations are async
- **Concurrent Tasks**: Intent classification and document retrieval run in parallel
- **Connection Pooling**: MongoDB and MQTT connections are reused
- **Audio Streaming**: Large audio files are streamed efficiently

## Security Considerations

- API keys stored in environment variables
- CORS configured for specific origins
- Input validation on all endpoints
- File size limits on audio uploads
- HTTPS handled by AWS infrastructure

## Monitoring

- Application logs in console
- MongoDB for chat history
- AWS CloudWatch for infrastructure metrics
- Health check endpoint: `/api/chat-logs`
