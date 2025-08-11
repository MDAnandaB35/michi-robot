# Backend - MongoDB Setup

This backend has been converted from MySQL/Sequelize to MongoDB/Mongoose.

## Setup Instructions

1. **Install Dependencies**

   ```bash
   npm install
   ```

2. **Install MongoDB**

   - Download and install MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
   - Or use MongoDB Atlas (cloud service)

3. **Environment Variables**
   Create a `.env` file in the backend directory with:

   ```
   MONGODB_URI=mongodb://localhost:27017/michi-chatbot
   JWT_SECRET=your_jwt_secret_key_here
   PORT=3000
   ```

4. **Start MongoDB**

   - Local: Start MongoDB service
   - Atlas: Use the connection string from your cluster

5. **Run the Server**
   ```bash
   node app.js
   ```

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Login user
- `GET /me` - Get current user info (requires JWT token)

## Database Schema

### User Collection

```javascript
{
  _id: ObjectId,
  userName: String (unique, required),
  password: String (hashed, required),
  createdAt: Date,
  updatedAt: Date
}
```

## Changes Made

- Replaced Sequelize with Mongoose
- Updated User model to use Mongoose Schema
- Modified database queries to use MongoDB syntax
- Added proper error handling
- Updated JWT token to use MongoDB ObjectId
