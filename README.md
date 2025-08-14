# Michi UI - Chatbot Interface

A modern React-based chatbot interface with authentication and user management capabilities.

## Features

- **Authentication System**: Login-only access (no user registration)
- **Admin Panel**: User management with CRUD operations
- **Responsive Design**: Works on both desktop and mobile devices
- **Real-time Chat**: Integration with chatbot backend
- **Audio Recording**: Voice input capabilities
- **Chat Logs**: Conversation history tracking

## Authentication

The system now only allows login - users cannot self-register. Only administrators can create new user accounts.

### Default Admin Account

- **Username**: `admin`
- **Password**: `admin123`

**Important**: Change the default password after first login!

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file with the following variables:

   ```env
   MONGODB_URI=your_mongodb_connection_string
   JWT_SECRET=your_jwt_secret_key
   PORT=3001
   USERS_COLLECTION=users
   ```

4. Create the initial admin user:

   ```bash
   npm run create-admin
   ```

5. Start the backend server:

   ```bash
   npm run dev
   ```

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd michi-ui-v1
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env` file with:

   ```env
   VITE_AUTH_ORIGIN=http://localhost:3001
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication

- `POST /login` - User login
- `GET /me` - Get current user info

### Admin (Admin only)

- `GET /admin/users` - Get all users
- `POST /admin/users` - Create new user
- `PUT /admin/users/:id` - Update user
- `DELETE /admin/users/:id` - Delete user

## User Management

### Creating Users

Only admin users can create new user accounts through the admin panel.

### Access Control

- **Admin users**: Can only access the Admin panel for user management
- **Regular users**: Can access Function Test, Audio Recorder, Chat Log, and Robot Detail
- **FunStuff page**: Removed from the system

### Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Admin-only access to user management
- Token expiration (1 hour)

## Project Structure

```
michi-ui/
├── backend/                 # Express.js backend
│   ├── app.js             # Main server file
│   ├── models/            # Database models
│   ├── createAdmin.js     # Admin user creation script
│   └── package.json
├── michi-ui-v1/           # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── API/          # API services
│   │   ├── context/      # React context
│   │   └── App.jsx       # Main app component
│   └── package.json
└── server/                 # Python chatbot backend
```

## Development

### Backend Development

- Use `npm run dev` for development with auto-reload
- Use `npm start` for production

### Frontend Development

- The React app runs on Vite for fast development
- Hot module replacement enabled
- ESLint configuration included

## Security Notes

1. **Change Default Admin Password**: Always change the default admin password
2. **JWT Secret**: Use a strong, unique JWT secret in production
3. **MongoDB Security**: Ensure MongoDB is properly secured
4. **Environment Variables**: Never commit sensitive environment variables

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**: Check your connection string and ensure MongoDB is running
2. **JWT Errors**: Verify JWT_SECRET is set correctly
3. **Admin Access Denied**: Ensure you're logged in as the admin user
4. **CORS Issues**: Check that the backend CORS configuration matches your frontend URL

### Getting Help

If you encounter issues:

1. Check the console logs in both frontend and backend
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check that MongoDB is accessible

## License

This project is proprietary software. All rights reserved.
