# Michi Chatbot

A full-stack AI-powered chatbot and digital tour guide for PT Bintang Toedjoe, featuring:

- **React** frontend (Vite)
- **Python Quart** backend (async, OpenAI, ElevenLabs, MongoDB, MQTT, ChromaDB)

---

## Project Structure

```
michi-ui/
├── michi-ui-v1/         # Frontend (React + Vite)
└── server/              # Backend (Python, Quart, AI, DB)
```

---

## Prerequisites

- **Node.js** (v16+ recommended)
- **Python** (3.9+ recommended)
- **pip** (Python package manager)
- **git**
- (For EC2) Ubuntu 20.04/22.04 LTS

---

## 1. Local Installation

### 1.1. Clone the Repository

```sh
git clone <your-repo-url>
cd michi-ui
```

### 1.2. Backend Setup

```sh
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in `server/` with:

```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
MONGODB_URI=your_mongodb_uri
# ...other variables as needed
```

#### Start the Backend

```sh
python beta.py
# Or for production:
hypercorn beta:app --bind 0.0.0.0:5000
```

### 1.3. Frontend Setup

```sh
cd ../michi-ui-v1
npm install
```

#### Start the Frontend

```sh
npm run dev -- --host 0.0.0.0
# Access at http://localhost:5173
```

---

## 2. Deploying on AWS EC2 (Ubuntu)

### 2.1. Launch EC2 Instance

- Use Ubuntu 20.04/22.04 LTS
- Open ports: 22 (SSH), 5000 (backend), 5173 (frontend) in Security Group

### 2.2. Connect to EC2

```sh
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 2.3. Install System Dependencies

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git ffmpeg -y
sudo apt install nodejs npm -y
```

### 2.4. Clone and Set Up Project

```sh
git clone <your-repo-url>
cd michi-ui
```

#### Backend

```sh
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Add your .env file as above
python beta.py  # Or use hypercorn for production
```

#### Frontend

```sh
cd ../michi-ui-v1
npm install
npm run build
npm run preview -- --host 0.0.0.0
# Access at http://<EC2_PUBLIC_IP>:4173
```

### 2.5. (Optional) Nginx Reverse Proxy

- Install Nginx: `sudo apt install nginx -y`
- Configure to proxy ports 5000 and 4173 as needed

---

## 3. Environment Variables

- Place all sensitive keys in `.env` (never commit to git)
- Required: `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `MONGODB_URI`, etc.

---

## 4. Troubleshooting

- **Port not accessible?** Check AWS Security Group and local firewall (e.g., `sudo ufw allow 5000 5173 4173`)
- **CORS errors?** Ensure backend allows frontend origin in CORS config
- **Audio not working?** Make sure `ffmpeg` is installed and browser has mic permissions
- **chroma_db too large?** Only commit the compressed `chroma_db.tar.gz` and add `chroma_db/` to `.gitignore`

---

## 7. Uncompressing `chroma_db.tar.gz` for RAG

If you need to use the ChromaDB vector store for Retrieval-Augmented Generation (RAG), you must extract the `chroma_db.tar.gz` archive before running the backend.

### On Linux/macOS

```sh
tar -xzvf server/chroma_db.tar.gz -C server/
```

- This will extract the `chroma_db/` folder into the `server/` directory.

### On Windows (PowerShell)

```powershell
# In PowerShell, from the project root:
cd server
# If you have tar (Windows 10+):
tar -xzvf chroma_db.tar.gz
# Or use 7-Zip/WinRAR to extract the archive via GUI
```

**After extraction, ensure that `server/chroma_db/` exists and contains the vector database files before starting the backend.**

---

## 5. Useful Commands

- **Unstage a file:** `git reset HEAD <file>`
- **Remove folder from git tracking:** `git rm -r --cached server/chroma_db/`
- **Push local commits:** `git push origin master`

---

## 6. Credits

- Developed by the Michi Capstone Team
- Powered by OpenAI, ElevenLabs, MongoDB, ChromaDB, MQTT, and Vite
