# Environment Variables Documentation

This document describes all the environment variables used in the Michi Robot backend application.

## Required Environment Variables

### Server Configuration
- **PORT**: Port number for the Express server (default: 3000)

### MongoDB Configuration
- **MONGODB_URI**: Complete MongoDB connection string (default: mongodb://localhost:27017/michi-chatbot)
- **DB_NAME**: Database name for MongoDB (default: michi-chatbot)

### Collection Names
- **USERS_COLLECTION**: Collection name for users (default: users)

### JWT Configuration
- **JWT_SECRET**: Secret key for JWT token signing (REQUIRED - change in production!)

### CORS Configuration
- **FRONTEND_URL**: Frontend application URL for CORS (default: http://localhost:5173)

## Setup Instructions

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the values in `.env` according to your environment:
   - Change `JWT_SECRET` to a strong, unique secret key
   - Update `MONGODB_URI` if using a different MongoDB instance
   - Adjust `FRONTEND_URL` if your frontend runs on a different port

3. Never commit `.env` file to version control

## Production Considerations

- Use a strong, unique JWT_SECRET (minimum 32 characters)
- Use environment-specific MongoDB URI
- Configure proper CORS origins for production
- Consider using environment variable services like AWS Parameter Store or Azure Key Vault
