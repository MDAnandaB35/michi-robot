# Michi Chatbot

A full-stack AI-powered chatbot and digital tour guide for PT Bintang Toedjoe, featuring:

- **React** frontend (Vite + TailwindCSS)
- **Python Quart** backend (async, OpenAI, ElevenLabs, MongoDB, MQTT, ChromaDB)
- **Node.js Express** backend (authentication, user management)

---

## Project Structure

```
michi-ui/
├── michi-ui-v1/         # Frontend (React + Vite + TailwindCSS)
├── backend/             # Node.js Express backend (auth, user management)
└── server/              # Python Quart backend (AI, audio, RAG)
```

---

## Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (3.9+ recommended)
- **pip** (Python package manager)
- **git**
- **MongoDB** (local or cloud instance)
- (For EC2) Ubuntu 20.04/22.04 LTS
- (For Netlify) Netlify account

---

## 1. Local Development Setup

### 1.1. Clone the Repository

```sh
git clone <your-repo-url>
cd michi-ui
```

### 1.2. Backend Setup

#### Node.js Express Backend (Authentication)

```sh
cd backend
npm install
```

Create a `.env` file in `backend/` with:

```env
MONGODB_URI=mongodb://localhost:27017/michi_chatbot
JWT_SECRET=your_jwt_secret_key_here
PORT=3001
```

#### Python Quart Backend (AI Services)

```sh
cd ../server
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in `server/` with:

```env
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
MONGODB_URI=mongodb://localhost:27017/michi_chatbot
QUART_ENV=development
QUART_DEBUG=true
```

#### Start Both Backends

**Terminal 1 - Node.js Backend:**

```sh
cd backend
npm start
# Backend will run on http://localhost:3001
```

**Terminal 2 - Python Backend:**

```sh
cd server
source venv/bin/activate  # or venv\Scripts\activate on Windows
python beta.py
# Python backend will run on http://localhost:5000
```

### 1.3. Frontend Setup

```sh
cd michi-ui-v1
npm install
```

Create a `.env` file in `michi-ui-v1/` with:

```env
VITE_API_URL=http://localhost:3001
VITE_AI_API_URL=http://localhost:5000
```

#### Start the Frontend

```sh
npm run dev
# Access at http://localhost:5173
```

---

## 2. EC2 Deployment

### 2.1. Launch EC2 Instance

- **AMI**: Ubuntu 24.04 LTS or newer
- **Instance Type**: t2.micro or larger (t2.micro is default free tier)
- **Storage**: 10GB+ (for ChromaDB and dependencies)
- **Security Group**: Open ports 22 (SSH), 3001 (Node.js), 5000 (Python), 80 (HTTP), 443 (HTTPS)

### 2.2. Connect to EC2

```sh
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

OR 

```sh
Connect through the AWS EC2 website CLI
```

### 2.3. Install System Dependencies

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git ffmpeg nginx -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 2.4. Clone and Set Up Project

```sh
git clone <your-repo-url>
cd michi-ui
```

#### Backend Setup

**Node.js Backend:**

```sh
cd backend
npm install
# Add your .env file with production MongoDB URI
```

**Python Backend:**

```sh
cd ../server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add your .env file with production settings
```

#### Frontend Build

```sh
cd ../michi-ui-v1
npm install
npm run build
```

### 2.5. Process Management with PM2

```sh
# Install PM2 globally
sudo npm install -g pm2

# Start Node.js backend
cd backend
pm2 start npm --name "michi-auth" -- start

# Start Python backend
cd ../server
source venv/bin/activate
pm2 start python --name "michi-ai" -- beta.py

# Save PM2 configuration
pm2 save
pm2 startup
```

### 2.6. Nginx Configuration (Optional)

Create `/etc/nginx/sites-available/michi`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /home/ubuntu/michi-ui/michi-ui-v1/dist;
        try_files $uri $uri/ /index.html;
    }

    # Node.js Backend
    location /api/ {
        proxy_pass http://localhost:3001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Python Backend
    location /ai/ {
        proxy_pass http://localhost:5000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```sh
sudo ln -s /etc/nginx/sites-available/michi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 3. Netlify Frontend Deployment (Requires domain)

**Note**: Only the React frontend is deployed through Netlify. The Node.js and Python backends are deployed on EC2 as described in the previous section. Domain is required as modern browser blocks non secure (https) requests unless locally.

### 3.1. Frontend Deployment

1. **Connect Repository:**

   - Go to [Netlify](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub repository
   - Set build directory: `michi-ui-v1`
   - Set build command: `npm run build`
   - Set publish directory: `dist`

2. **Environment Variables:**
   Add these in Netlify dashboard to point to your EC2 backend:

   ```
   VITE_API_URL=https://your-ec2-domain.com/api
   VITE_AI_API_URL=https://your-ec2-domain.com/ai
   ```

3. **Build Settings:**
   - Node version: 18
   - Build command: `cd michi-ui-v1 && npm install && npm run build`
   - Publish directory: `michi-ui-v1/dist`

### 3.2. Netlify Configuration

Create `netlify.toml` in project root:

```toml
[build]
  base = "."
  command = "cd michi-ui-v1 && npm install && npm run build"
  publish = "michi-ui-v1/dist"

[build.environment]
  NODE_VERSION = "18"

# Redirect all routes to index.html for SPA routing
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### 3.3. Backend Communication

Since your backends are running on EC2, ensure:

1. **CORS Configuration**: Your EC2 backends allow requests from your Netlify domain
2. **Environment Variables**: Frontend environment variables point to EC2 backend URLs
3. **SSL**: Both Netlify and EC2 have valid SSL certificates
4. **Domain Setup**: Configure custom domains for both frontend and backend if needed

---

## 4. Environment Variables Reference

### Frontend (.env)

```env
VITE_API_URL=http://localhost:3001          # Local development
VITE_API_URL=https://your-ec2-domain.com/api    # Production (EC2)
VITE_AI_API_URL=http://localhost:5000       # Local development
VITE_AI_API_URL=https://your-ec2-domain.com/ai  # Production (EC2)
```

### Node.js Backend (.env)

```env
MONGODB_URI=mongodb://localhost:27017/michi_chatbot
JWT_SECRET=your_jwt_secret_key_here
PORT=3001
NODE_ENV=development
```

### Python Backend (.env)

```env
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
MONGODB_URI=mongodb://localhost:27017/michi_chatbot
QUART_ENV=production
QUART_DEBUG=false
```

---

## 5. Deployment Checklist

### Local Development

- [ ] MongoDB running locally
- [ ] Node.js backend on port 3001
- [ ] Python backend on port 5000
- [ ] React frontend on port 5173
- [ ] All environment variables set
- [ ] ChromaDB extracted (if using RAG)

### EC2 Deployment

- [ ] Security groups configured
- [ ] MongoDB installed and running
- [ ] PM2 processes running
- [ ] Nginx configured and running
- [ ] SSL certificate (Let's Encrypt)
- [ ] Domain DNS pointing to EC2

### Netlify Frontend Deployment

- [ ] Repository connected
- [ ] Build settings configured
- [ ] Environment variables set (pointing to EC2 backend)
- [ ] Custom domain configured (optional)
- [ ] CORS configured on EC2 backend to allow Netlify domain

---

## 6. Troubleshooting

### Common Issues

**Port not accessible?**

- Check AWS Security Group
- Check local firewall: `sudo ufw allow 3001 5000 5173`
- Verify services are running: `pm2 status` or `netstat -tlnp`

**CORS errors?**

- Ensure backend allows frontend origin
- Check environment variables match
- Verify proxy configuration in Nginx

**Audio not working?**

- Install `ffmpeg`: `sudo apt install ffmpeg`
- Check browser microphone permissions
- Verify ElevenLabs API key

**ChromaDB issues?**

- Extract `chroma_db.tar.gz` before starting backend
- Ensure sufficient disk space
- Check file permissions

**Build failures?**

- Verify Node.js version: `node --version`
- Clear npm cache: `npm cache clean --force`
- Check for missing dependencies

---

## 7. Useful Commands

### Development

```sh
# Start all services locally
cd backend && npm start & cd server && python beta.py & cd michi-ui-v1 && npm run dev

# Check running processes
lsof -i :3001  # Node.js backend
lsof -i :5000  # Python backend
lsof -i :5173  # React dev server
```

### Production

```sh
# PM2 management
pm2 status
pm2 restart michi-auth
pm2 restart michi-ai
pm2 logs

# Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl status nginx

# MongoDB
sudo systemctl status mongod
sudo systemctl restart mongod
```

### Git

```sh
git reset HEAD <file>           # Unstage a file
git rm -r --cached server/chroma_db/  # Remove folder from tracking
git push origin main            # Push commits
```

---

## 8. Performance Optimization

### Frontend

- Enable gzip compression in Nginx
- Use CDN for static assets
- Implement lazy loading for components
- Optimize bundle size with Vite

### Backend

- Use PM2 cluster mode for Node.js
- Implement Redis caching
- Optimize database queries
- Use connection pooling

### Infrastructure

- Enable HTTP/2
- Use CloudFront CDN (AWS)
- Implement auto-scaling groups
- Monitor with CloudWatch

---

## 9. Security Best Practices

- Use environment variables for secrets
- Implement rate limiting
- Enable HTTPS everywhere
- Regular security updates
- Database access control
- API key rotation
- Input validation and sanitization

---

## 10. Credits

- Developed by the Michi Capstone Team
- Powered by OpenAI, ElevenLabs, MongoDB, ChromaDB, MQTT, Vite, and TailwindCSS
- Built with React, Node.js, and Python
