// createAdmin.js - Script to create initial admin user
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const { connectDB, User } = require('./models');
require('dotenv').config();

async function createAdminUser() {
  try {
    // Connect to MongoDB
    await connectDB();
    console.log('Connected to MongoDB');

    // Check if admin user already exists
    const existingAdmin = await User.findOne({ userName: 'admin' });
    if (existingAdmin) {
      console.log('Admin user already exists');
      process.exit(0);
    }

    // Create admin user
    const hashedPassword = await bcrypt.hash('admin123', 10);
    const adminUser = await User.create({
      userName: 'admin',
      password: hashedPassword,
    });

    console.log('Admin user created successfully:', {
      userName: adminUser.userName,
      id: adminUser._id,
      createdAt: adminUser.createdAt
    });

    console.log('Default admin credentials:');
    console.log('Username: admin');
    console.log('Password: admin123');
    console.log('Please change the password after first login!');

    process.exit(0);
  } catch (error) {
    console.error('Error creating admin user:', error);
    process.exit(1);
  }
}

createAdminUser();
