# Michi Robot - AI-Powered Voice Assistant

A voice-controlled AI assistant built with React frontend and Quart backend, featuring speech-to-text, text-to-speech, and MQTT communication.

## Features

- 🎤 **Voice Recording**: Real-time audio recording with waveform visualization
- 🤖 **AI Processing**: OpenAI GPT-3.5 for intelligent responses
- 🔊 **Text-to-Speech**: ElevenLabs integration for natural voice synthesis
- 📊 **Chat History**: MongoDB integration for conversation logging
- 🔗 **MQTT Communication**: Real-time communication with IoT devices
- 🌐 **Cross-Platform**: Works on desktop and mobile browsers
- 🔒 **HTTPS Support**: Works with IP addresses using self-signed certificates

## Quick Start

### Local Development

#### Option 1: Automated Setup (Recommended)

**Windows:**

```bash
setup_local.bat
```

**Linux/Mac:**

```bash
chmod +x setup_local.sh
./setup_local.sh
```

#### Option 2: Manual Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd michi-ui
```

2. **Set up backend**

```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env.local .env.local
# Edit .env.local with your API keys
python beta.py
```

3. **Set up frontend**

```bash
cd ../michi-ui-v1
npm install
cp env.local .env.local
npm run dev
```

4. **Access the application**

- Frontend: http://localhost:5173
- Backend: http://localhost:5000

### Production Deployment (IP-Only)

#### EC2/VM Setup

1. **SSH into your server**

```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

2. **Clone and set up the project**

```bash
git clone <repository-url>
cd michi-ui/server
cp env.example .env
# Edit .env with your production API keys
```

3. **Run HTTPS deployment**

```bash
chmod +x deploy_https.sh
./deploy_https.sh
```

The script will automatically:

- Detect your server IP
- Install Nginx and create self-signed certificates
- Configure HTTPS with self-signed certificates
- Set up the Quart server as a systemd service

4. **Configure frontend**

In your Netlify deployment, set environment variables:

```
VITE_API_BASE_URL=your-server-ip
VITE_MQTT_BROKER=broker.emqx.io
VITE_MQTT_WS_PORT=8084
VITE_MQTT_PROTOCOL=wss
VITE_MQTT_TOPIC=testtopic/mwtt
```

## Environment Configuration

### Backend Environment Variables

Create `.env.local` for local development or `.env` for production:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Database
MONGODB_URI=your_mongodb_connection_string
MONGODB_DBNAME=michi_robot
MONGODB_COLLECTION=chat_logs

# CORS (Local: multiple origins, Production: single origin)
ALLOWED_CORS_ORIGINS=https://michi-robot.netlify.app

# MQTT
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=testtopic/mwtt

# SSL (Local: false, Production: handled by Nginx)
USE_SSL=false
```

### Frontend Environment Variables

Create `.env.local` for local development:

```bash
# Local Development
VITE_API_BASE_URL=localhost:5000

# Production
VITE_API_BASE_URL=your-server-ip

# MQTT
VITE_MQTT_BROKER=broker.emqx.io
VITE_MQTT_WS_PORT=8084
VITE_MQTT_PROTOCOL=wss
VITE_MQTT_TOPIC=testtopic/mwtt
```

## API Endpoints

- `POST /detect_wakeword` - Detect wake word in audio
- `POST /process_input` - Process voice input and generate response
- `GET /audio_response` - Stream generated audio response
- `GET /api/chat-logs` - Retrieve chat history

## Architecture

```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────┐
│   React Frontend│ ◄──────────────► │   Quart Backend │
│   (Vite)        │                  │   (Python)      │
└─────────────────┘                  └─────────────────┘
         │                                     │
         │ MQTT                                │
         ▼                                     ▼
┌─────────────────┐                  ┌─────────────────┐
│   MQTT Broker   │                  │   MongoDB       │
│   (EMQX)        │                  │   (Database)    │
└─────────────────┘                  └─────────────────┘
```

## Security Features

- ✅ HTTPS encryption (production with self-signed certificates)
- ✅ CORS protection
- ✅ Security headers
- ✅ Environment variable protection
- ✅ IP-only deployment support

## Important Notes for IP-Only Setup

### Self-Signed Certificate Warnings

When using self-signed certificates:

- Browsers will show security warnings
- Users need to click "Advanced" → "Proceed to your-server-ip (unsafe)"
- This is normal for development/testing environments
- For production, consider getting a domain name for proper SSL certificates

### Accepting Self-Signed Certificate

When accessing your HTTPS server for the first time:

1. Visit `https://your-server-ip` in your browser
2. You'll see a security warning
3. Click "Advanced" or "Show Details"
4. Click "Proceed to your-server-ip (unsafe)"
5. The certificate will be accepted for future requests

## Troubleshooting

### Local Development Issues

**Port already in use:**

```bash
# Check what's using the port
netstat -tulpn | grep :5000
# Kill the process
kill -9 <PID>
```

**API key errors:**

- Ensure your `.env.local` file has valid API keys
- Check that the environment file is in the correct location

### Production Issues

**Service not starting:**

```bash
sudo systemctl status michi-robot
sudo journalctl -u michi-robot -f
```

**SSL certificate issues:**

```bash
# Regenerate self-signed certificate
sudo rm /etc/ssl/certs/nginx-selfsigned.crt /etc/ssl/private/nginx-selfsigned.key
SERVER_IP=$(hostname -I | awk '{print $1}')
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=$SERVER_IP"
sudo systemctl reload nginx
```

**CORS errors:**

- Verify `ALLOWED_CORS_ORIGINS` includes your frontend domain
- Check that requests are using HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally and in production
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the deployment guide in `server/HTTPS_DEPLOYMENT.md`
3. Open an issue on GitHub
