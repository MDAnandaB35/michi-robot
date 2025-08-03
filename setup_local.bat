@echo off
REM Local Development Setup Script for Michi Robot (Windows)
REM This script helps you set up the project for local development

echo 🚀 Setting up Michi Robot for local development...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

echo ✅ Python and Node.js are installed

REM Set up backend
echo 📦 Setting up backend...
cd server

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Create local environment file if it doesn't exist
if not exist ".env.local" (
    echo 📝 Creating local environment file...
    copy env.local .env.local
    echo ⚠️  Please edit server\.env.local and add your API keys!
)

echo ✅ Backend setup complete

REM Set up frontend
echo 📦 Setting up frontend...
cd ..\michi-ui-v1

REM Install dependencies
echo 📦 Installing Node.js dependencies...
npm install

REM Create local environment file if it doesn't exist
if not exist ".env.local" (
    echo 📝 Creating local environment file...
    copy env.local .env.local
)

echo ✅ Frontend setup complete

REM Go back to root
cd ..

echo.
echo 🎉 Local development setup complete!
echo.
echo Next steps:
echo 1. Edit server\.env.local and add your API keys
echo 2. Start the backend: cd server ^&^& venv\Scripts\activate ^&^& python beta.py
echo 3. Start the frontend: cd michi-ui-v1 ^&^& npm run dev
echo.
echo Your app will be available at:
echo - Frontend: http://localhost:5173
echo - Backend: http://localhost:5000
echo.
echo Happy coding! 🚀
pause 