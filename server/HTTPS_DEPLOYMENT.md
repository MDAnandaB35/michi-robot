# HTTPS Deployment Guide for Michi Robot

This guide will help you set up HTTPS for your Quart server on EC2 to resolve the Mixed Content error, and also includes local development setup.

## Problem

Your frontend at `https://michi-robot.netlify.app` is trying to make requests to `http://18.142.229.32:5000`, which browsers block due to Mixed Content policy.

## Environment Setup

### Local Development Setup

For local development, you can run the server without HTTPS:

#### 1. Create local environment file

```bash
# In server directory
cp env.example .env.local
```

Edit `.env.local`:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Database Configuration
MONGODB_URI=your_mongodb_connection_string_here
MONGODB_DBNAME=michi_robot
MONGODB_COLLECTION=chat_logs

# CORS Configuration (for local development)
ALLOWED_CORS_ORIGINS=http://localhost:5173,http://localhost:3000,https://michi-robot.netlify.app

# MQTT Configuration
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=testtopic/mwtt

# File Storage
UPLOAD_FOLDER=uploads
CHROMA_PATH=chroma_db

# Relevance Threshold
RELEVANCE_THRESHOLD=0.7

# SSL Configuration (disabled for local development)
USE_SSL=false
```

#### 2. Create frontend local environment

```bash
# In michi-ui-v1 directory
cp env.production .env.local
```

Edit `.env.local`:

```bash
# Local development environment variables
VITE_API_BASE_URL=localhost:5000
VITE_MQTT_BROKER=broker.emqx.io
VITE_MQTT_WS_PORT=8084
VITE_MQTT_PROTOCOL=wss
VITE_MQTT_TOPIC=testtopic/mwtt
```

#### 3. Run locally

```bash
# Terminal 1: Start backend
cd server
source venv/bin/activate  # or activate your virtual environment
python beta.py

# Terminal 2: Start frontend
cd michi-ui-v1
npm run dev
```

Your local setup will be available at:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:5000`

### Production Setup (EC2/VM)

#### Option 1: Nginx Reverse Proxy (Recommended)

This is the most common and secure approach for production servers.

##### Step 1: SSH into your server

```bash
ssh -i your-key.pem ubuntu@18.142.229.32
```

##### Step 2: Set up environment

```bash
cd /home/ubuntu/michi-ui/server
cp env.example .env
nano .env
```

Edit `.env` for production:

```bash
# API Keys
OPENAI_API_KEY=your_actual_openai_key
ELEVENLABS_API_KEY=your_actual_elevenlabs_key

# Database Configuration
MONGODB_URI=your_mongodb_connection_string
MONGODB_DBNAME=michi_robot
MONGODB_COLLECTION=chat_logs

# CORS Configuration (production)
ALLOWED_CORS_ORIGINS=https://michi-robot.netlify.app

# MQTT Configuration
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=testtopic/mwtt

# File Storage
UPLOAD_FOLDER=uploads
CHROMA_PATH=chroma_db

# Relevance Threshold
RELEVANCE_THRESHOLD=0.7

# SSL Configuration (disabled - handled by Nginx)
USE_SSL=false
```

##### Step 3: Run the deployment script

```bash
chmod +x deploy_https.sh
nano deploy_https.sh  # Edit email and paths if needed
./deploy_https.sh
```

**Important**: Before running the script, edit it and replace:

- `your-email@example.com` with your actual email
- Update the working directory path if different
- Update the server IP if different

##### Step 4: Update frontend for production

In your Netlify deployment, set environment variables:

```bash
VITE_API_BASE_URL=18.142.229.32
VITE_MQTT_BROKER=broker.emqx.io
VITE_MQTT_WS_PORT=8084
VITE_MQTT_PROTOCOL=wss
VITE_MQTT_TOPIC=testtopic/mwtt
```

#### Option 2: Direct SSL with Quart (Alternative)

If you prefer to handle SSL directly in your Quart application:

##### Step 1: Get SSL certificates

```bash
# Install certbot
sudo apt install certbot

# Get certificate for your IP (Note: This might not work with Let's Encrypt)
sudo certbot certonly --standalone -d 18.142.229.32
```

##### Step 2: Update environment variables

```bash
# Edit your .env file
nano .env

# Add these lines:
USE_SSL=true
SSL_CERT_PATH=/etc/letsencrypt/live/18.142.229.32/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/18.142.229.32/privkey.pem
```

##### Step 3: Use the SSL-enabled server

```bash
python beta_ssl.py
```

## Manual Setup (if script doesn't work)

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/michi-robot`:

```nginx
server {
    listen 80;
    server_name 18.142.229.32;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name 18.142.229.32;

    ssl_certificate /etc/letsencrypt/live/18.142.229.32/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/18.142.229.32/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable the site

```bash
sudo ln -s /etc/nginx/sites-available/michi-robot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Get SSL certificate

```bash
sudo certbot --nginx -d 18.142.229.32
```

### 5. Create systemd service

Create `/etc/systemd/system/michi-robot.service`:

```ini
[Unit]
Description=Michi Robot Quart Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/michi-ui/server
Environment=PATH=/home/ubuntu/michi-ui/server/venv/bin
ExecStart=/home/ubuntu/michi-ui/server/venv/bin/python beta.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 6. Start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable michi-robot
sudo systemctl start michi-robot
```

## Environment Configuration Summary

### Local Development

- **Backend**: `http://localhost:5000`
- **Frontend**: `http://localhost:5173`
- **CORS**: Allows localhost origins
- **SSL**: Disabled

### Production

- **Backend**: `https://18.142.229.32` (via Nginx)
- **Frontend**: `https://michi-robot.netlify.app`
- **CORS**: Only allows Netlify domain
- **SSL**: Enabled via Nginx + Let's Encrypt

## Security Considerations

1. **Firewall**: Ensure ports 80 and 443 are open in your EC2 security group
2. **CORS**: Production server only accepts requests from `https://michi-robot.netlify.app`
3. **SSL Renewal**: Certificates auto-renew with the cron job
4. **Security Headers**: Nginx adds security headers automatically
5. **Environment Files**: Never commit `.env` files to version control

## Troubleshooting

### Check service status

```bash
sudo systemctl status michi-robot
sudo systemctl status nginx
```

### Check logs

```bash
sudo journalctl -u michi-robot -f
sudo tail -f /var/log/nginx/error.log
```

### Test SSL certificate

```bash
curl -I https://18.142.229.32
```

### Renew certificate manually

```bash
sudo certbot renew
```

### Local development issues

```bash
# Check if ports are in use
netstat -tulpn | grep :5000
netstat -tulpn | grep :5173

# Kill processes if needed
kill -9 <PID>
```

## Frontend Configuration

### Local Development

```javascript
// .env.local
VITE_API_BASE_URL=localhost:5000
```

### Production

```javascript
// Netlify environment variables
VITE_API_BASE_URL=18.142.229.32
```

Your frontend code automatically handles the protocol:

```javascript
// This works for both local and production
const response = await fetch(`https://${SERVER_ORIGIN}/api/chat-logs`);
// For local: https://localhost:5000/api/chat-logs
// For production: https://18.142.229.32/api/chat-logs
```

## Verification

### Local Development

- `http://localhost:5000/api/chat-logs`
- `http://localhost:5000/detect_wakeword`
- `http://localhost:5000/process_input`

### Production

- `https://18.142.229.32/api/chat-logs`
- `https://18.142.229.32/detect_wakeword`
- `https://18.142.229.32/process_input`

Your Mixed Content error should be resolved in production, and local development will work seamlessly!
