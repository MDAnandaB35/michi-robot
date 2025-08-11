// Models index.js - MongoDB/Mongoose configuration

const mongoose = require('mongoose');
require('dotenv').config();

// MongoDB connection
const connectDB = async () => {
    try {
        const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/michi-chatbot';
        const conn = await mongoose.connect(mongoUri);
        console.log(`MongoDB Connected: ${conn.connection.host}`);
        console.log(`Database: ${conn.connection.name}`);
    } catch (error) {
        console.error('Error connecting to MongoDB:', error);
        process.exit(1);
    }
};

const db = {};

db.connectDB = connectDB;
db.mongoose = mongoose;

// Database and collection configuration
db.config = {
    databaseName: process.env.DB_NAME,
    collections: {
        users: process.env.USERS_COLLECTION
    }
};

// Import models
db.User = require('./User.js');

module.exports = db;