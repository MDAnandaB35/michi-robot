# Robot ID Setup Guide

This guide explains how to set up the hardcoded robot identifier system for the Michi chatbot backend.

## Overview

The robot identifier system ensures that:

- Each user can only view their own chat logs
- Chat logs are properly associated with specific users
- The backend knows which robot/user it's logging for

## Setup Steps

### 1. Get User ID from MongoDB

First, you need to get the `_id` of the user from your authentication database:

```bash
# Connect to MongoDB
mongosh

# Switch to your database
use michi_robot

# Find the user (replace 'admin' with the actual username)
db.users.findOne({userName: "admin"})

# Copy the _id value (it looks like: ObjectId("507f1f77bcf86cd799439011"))
```

### 2. Create .env File

Create a `.env` file in the `server/` directory with the following content:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs API Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/michi_robot
MONGODB_DBNAME=michi_robot
MONGODB_COLLECTION=chat_logs

# Robot Identifier (MUST match user's _id from MongoDB)
ROBOT_ID=507f1f77bcf86cd799439011

# File Storage Configuration
UPLOAD_FOLDER=uploads
CHROMA_PATH=chroma_db

# MQTT Configuration
MQTT_BROKER=broker.emqx.io
MQTT_PORT=1883
MQTT_TOPIC=testtopic/mwtt

# AI Model Configuration
RELEVANCE_THRESHOLD=0.6

# Server Configuration
QUART_ENV=development
QUART_DEBUG=true
```

**Important**: Replace `507f1f77bcf86cd799439011` with the actual `_id` from step 1.

### 3. Verify Setup

After setting up the `.env` file:

1. **Start the backend server**:

   ```bash
   cd server
   python beta.py
   ```

2. **Check the logs** - you should see:

   ```
   [INFO] Robot ID configured: 507f1f77bcf86cd799439011
   ```

3. **Test the chat logs endpoint**:
   ```bash
   curl "http://localhost:5000/api/chat-logs?robot_id=507f1f77bcf86cd799439011"
   ```

## How It Works

### Backend Changes

1. **Config Class**: Added `ROBOT_ID` environment variable
2. **MongoLogger**: All chat logs now include `robot_id` field
3. **API Endpoint**: `/api/chat-logs` now requires `robot_id` parameter
4. **Data Filtering**: Users can only see logs with their `robot_id`

### Frontend Changes

1. **ChatLogs Component**: Now uses auth context to get user ID
2. **API Call**: Passes user ID as `robot_id` parameter
3. **Security**: Users can only access their own chat logs

## Security Features

- ✅ **User Isolation**: Each user only sees their own chat logs
- ✅ **Required Parameter**: `robot_id` is mandatory for chat log access
- ✅ **Environment Variable**: Robot ID is stored securely in `.env`
- ✅ **Validation**: Backend validates robot_id before returning data

## Troubleshooting

### Common Issues

1. **"ROBOT_ID environment variable is required"**

   - Check that `.env` file exists in `server/` directory
   - Verify `ROBOT_ID` is set correctly
   - Restart the server after making changes

2. **"robot_id parameter is required"**

   - Frontend is not passing the robot_id parameter
   - Check that user is authenticated
   - Verify the API call includes the robot_id

3. **"No chat logs found"**
   - Robot ID might not match any existing logs
   - Check that the ID in `.env` matches a user in your database
   - Verify the MongoDB connection

### Verification Commands

```bash
# Check if .env file exists
ls -la server/.env

# Verify environment variables are loaded
cd server
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('ROBOT_ID:', os.getenv('ROBOT_ID'))"

# Test MongoDB connection
mongosh "mongodb://localhost:27017/michi_robot" --eval "db.users.findOne()"
```

## Multiple Robots/Users

If you have multiple robots or users:

1. **Option 1**: Use different `.env` files for each robot
2. **Option 2**: Set `ROBOT_ID` as an environment variable when starting the server
3. **Option 3**: Modify the code to accept robot_id as a command line argument

## Example for Multiple Robots

```bash
# Robot 1
ROBOT_ID=507f1f77bcf86cd799439011 python beta.py

# Robot 2
ROBOT_ID=507f1f77bcf86cd799439012 python beta.py
```

This setup ensures complete user isolation and secure access to chat logs.
