#!/bin/bash

# Local Development Setup Script for Michi Robot
# This script helps you set up the project for local development

echo "🚀 Setting up Michi Robot for local development..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

echo "✅ Python and Node.js are installed"

# Set up backend
echo "📦 Setting up backend..."
cd server

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create local environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating local environment file..."
    cp env.local .env.local
    echo "⚠️  Please edit server/.env.local and add your API keys!"
fi

echo "✅ Backend setup complete"

# Set up frontend
echo "📦 Setting up frontend..."
cd ../michi-ui-v1

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create local environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating local environment file..."
    cp env.local .env.local
fi

echo "✅ Frontend setup complete"

# Go back to root
cd ..

echo ""
echo "🎉 Local development setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit server/.env.local and add your API keys"
echo "2. Start the backend: cd server && source venv/bin/activate && python beta.py"
echo "3. Start the frontend: cd michi-ui-v1 && npm run dev"
echo ""
echo "Your app will be available at:"
echo "- Frontend: http://localhost:5173"
echo "- Backend: http://localhost:5000"
echo ""
echo "Happy coding! 🚀" 