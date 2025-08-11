// Models User.js - Mongoose User Schema

const mongoose = require('mongoose');
require('dotenv').config();

const userSchema = new mongoose.Schema({
    userName: {
        type: String,
        required: true,
        unique: true,
        trim: true
    },
    password: {
        type: String,
        required: true
    }
}, {
    timestamps: true
});

// Use environment variable for collection name, fallback to 'users'
const collectionName = process.env.USERS_COLLECTION || 'users';

module.exports = mongoose.model('User', userSchema, collectionName);
