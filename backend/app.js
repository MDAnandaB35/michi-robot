// app.js - MongoDB/Mongoose version

const express = require('express');
const bodyParser = require('body-parser'); // Read incoming requests
const bcrypt = require('bcrypt'); // Hash passwords
const jwt = require('jsonwebtoken'); // Create and verify JWT tokens
const cors = require('cors'); // Enable CORS for all origins
const { connectDB, User, Robot } = require('./models'); // Connect to MongoDB and models
require('dotenv').config();

const app = express();

// Enable CORS
app.use(cors({
  origin: "*", // Vite dev server default port
  credentials: true
}));

app.use(bodyParser.json());

// Test endpoint for ping
app.get('/test', (req, res) => {
  res.json({ message: 'Backend is working!', timestamp: new Date().toISOString() });
});

// Connect to MongoDB
connectDB();

// Debug: Check environment variables
console.log('Environment check:');
console.log('- JWT_SECRET set:', !!process.env.JWT_SECRET);
console.log('- JWT_SECRET length:', process.env.JWT_SECRET ? process.env.JWT_SECRET.length : 'N/A');
console.log('- PORT:', process.env.PORT || 3001);
console.log('- MONGODB_URI set:', !!process.env.MONGODB_URI);

// Middleware to verify user token
const verifyToken = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ message: 'Unauthorized, no token provided' });
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.userId);
    if (!user) return res.status(401).json({ message: 'Unauthorized, invalid token' });
    req.user = user;
    next();
  } catch (error) {
    return res.status(401).json({ message: 'Unauthorized, invalid token' });
  }
};

// Middleware to verify admin token
const verifyAdminToken = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  console.log('Admin middleware - Token received:', token ? token.substring(0, 20) + '...' : 'No token');
  
  if (!token) {
    console.log('Admin middleware - No token provided');
    return res.status(401).json({ message: 'Unauthorized, no token provided' });
  }
  
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    console.log('Admin middleware - Token decoded, userId:', decoded.userId);
    
    const user = await User.findById(decoded.userId);
    console.log('Admin middleware - User found:', user ? user.userName : 'No user');
    
    if (!user) {
      console.log('Admin middleware - User not found');
      return res.status(401).json({ message: 'Unauthorized, invalid token' });
    }
    
    // Check if user is admin (you can add an isAdmin field to your User model)
    if (user.userName !== 'admin') {
      console.log('Admin middleware - User is not admin:', user.userName);
      return res.status(403).json({ message: 'Forbidden, admin access required' });
    }
    
    console.log('Admin middleware - Access granted for admin user:', user.userName);
    req.user = user;
    next();
  } catch (error) {
    console.error('Admin middleware - Token verification error:', error);
    res.status(401).json({ message: 'Unauthorized, invalid token' });
  }
};

// Login
app.post('/login', async (req, res) => {
  const { username, password } = req.body;
  console.log('Login attempt for username:', username);
  
  try {
    const user = await User.findOne({ userName: username });
    if (!user) {
      console.log('Login failed - User not found:', username);
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    
    const passwordValid = await bcrypt.compare(password, user.password);
    if (!passwordValid) {
      console.log('Login failed - Invalid password for user:', username);
      return res.status(401).json({ message: 'Invalid credentials' });
    }
    
    console.log('Login successful for user:', username);
    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, { expiresIn: '1h' });
    console.log('JWT token generated, length:', token.length);
    
    res.json({ token: token, jwt_token: token }); // Send both for compatibility
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Get user information for profile
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

// Robot endpoints

// Get robots owned by current user
app.get('/robots/mine', verifyToken, async (req, res) => {
  try {
    const robots = await Robot.find({ ownerUserIds: req.user._id })
      .select('-__v')
      .sort({ createdAt: -1 });
    res.json(robots);
  } catch (error) {
    console.error('Error fetching user robots:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Claim ownership of a robot by robotId (if exists), else 404
app.post('/robots/claim', verifyToken, async (req, res) => {
  try {
    const { robotId } = req.body;
    if (!robotId) return res.status(400).json({ message: 'robotId is required' });
    const robot = await Robot.findOne({ robotId });
    if (!robot) return res.status(404).json({ message: 'Robot not found' });
    if (!robot.ownerUserIds.some(id => id.toString() === req.user._id.toString())) {
      robot.ownerUserIds.push(req.user._id);
      await robot.save();
    }
    res.json(robot);
  } catch (error) {
    console.error('Error claiming robot:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Admin: CRUD robots
app.get('/admin/robots', verifyAdminToken, async (req, res) => {
  try {
    const robots = await Robot.find({}).select('-__v').sort({ createdAt: -1 });
    res.json(robots);
  } catch (error) {
    console.error('Error fetching robots:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

app.post('/admin/robots', verifyAdminToken, async (req, res) => {
  try {
    const { robotId, robotName } = req.body;
    if (!robotId || !robotName) return res.status(400).json({ message: 'robotId and robotName are required' });
    const existing = await Robot.findOne({ robotId });
    if (existing) return res.status(400).json({ message: 'Robot already exists' });
    const robot = await Robot.create({ robotId, robotName, createdBy: req.user._id, ownerUserIds: [] });
    res.status(201).json(robot);
  } catch (error) {
    console.error('Error creating robot:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

app.put('/admin/robots/:id', verifyAdminToken, async (req, res) => {
  try {
    const { robotName, ownerUserIds } = req.body;
    const update = {};
    if (robotName) update.robotName = robotName;
    if (Array.isArray(ownerUserIds)) update.ownerUserIds = ownerUserIds;
    const robot = await Robot.findByIdAndUpdate(req.params.id, update, { new: true, runValidators: true });
    if (!robot) return res.status(404).json({ message: 'Robot not found' });
    res.json(robot);
  } catch (error) {
    console.error('Error updating robot:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

app.delete('/admin/robots/:id', verifyAdminToken, async (req, res) => {
  try {
    const robot = await Robot.findByIdAndDelete(req.params.id);
    if (!robot) return res.status(404).json({ message: 'Robot not found' });
    res.json({ message: 'Robot deleted successfully' });
  } catch (error) {
    console.error('Error deleting robot:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Admin endpoints for user management

// Get all users
app.get('/admin/users', verifyAdminToken, async (req, res) => {
  try {
    const users = await User.find({}).select('-password').sort({ createdAt: -1 });
    res.json(users);
  } catch (error) {
    console.error('Error fetching users:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Create new user
app.post('/admin/users', verifyAdminToken, async (req, res) => {
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
    
    const userResponse = user.toObject();
    delete userResponse.password;
    
    res.status(201).json(userResponse);
  } catch (error) {
    console.error('Error creating user:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Update user
app.put('/admin/users/:id', verifyAdminToken, async (req, res) => {
  try {
    const { userName, password } = req.body;
    const updateData = { userName };
    
    if (password && password.trim() !== '') {
      updateData.password = await bcrypt.hash(password, 10);
    }
    
    const user = await User.findByIdAndUpdate(
      req.params.id,
      updateData,
      { new: true, runValidators: true }
    ).select('-password');
    
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    res.json(user);
  } catch (error) {
    console.error('Error updating user:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Delete user
app.delete('/admin/users/:id', verifyAdminToken, async (req, res) => {
  try {
    const user = await User.findByIdAndDelete(req.params.id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    res.json({ message: 'User deleted successfully' });
  } catch (error) {
    console.error('Error deleting user:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Start server
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});