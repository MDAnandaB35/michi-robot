// app.js - MongoDB/Mongoose version

const express = require('express');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const cors = require('cors');
const { connectDB, User } = require('./models');
require('dotenv').config();

const app = express();

// Enable CORS
app.use(cors({
  origin: 'http://localhost:5173', // Vite dev server default port
  credentials: true
}));

app.use(bodyParser.json());

// Connect to MongoDB
connectDB();

// Register
app.post('/register', async (req, res) => {
    try {
        const { userName, password } = req.body;
        
        // Check if user already exists
        const existingUser = await User.findOne({ userName });
        if (existingUser) {
            return res.status(400).json({ message: 'User already exists' });
        }

        const hashedPassword = await bcrypt.hash(password, 10);
        const user = await User.create({
            userName,
            password: hashedPassword,
        });
        res.status(201).json({ message: 'User created successfully' });
    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({ message: 'Internal server error' });
    }
});

// Login
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const user = await User.findOne({ userName: username });
        if (!user || !(await bcrypt.compare(password, user.password))) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, { expiresIn: '1h' });
        res.json({ token });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ message: 'Internal server error' });
    }
});

app.get('/me', async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) {
        return res.status(401).json({ message: 'Unauthorized, no token provided' });
    }
    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        const user = await User.findById(decoded.userId).select('-password');
        if (!user) {
            return res.status(401).json({ message: 'Unauthorized, invalid token' });
        }
        res.json({ user });
    } catch (error) {
        console.error('Auth error:', error);
        res.status(401).json({ message: 'Unauthorized, invalid token' });
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});