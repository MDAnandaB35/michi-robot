# Michi UI v1

A React-based frontend for the Michi Chatbot with authentication system.

## Features

- 🔐 **Authentication System**: Login and registration with JWT tokens
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🎨 **Modern UI**: Built with Tailwind CSS and Lucide React icons
- 🔄 **Real-time Updates**: MQTT integration for real-time communication
- 📊 **Chat Logs**: View and manage conversation history
- 🎤 **Audio Recording**: Voice input capabilities

## Setup

### Prerequisites

1. **Backend Server**: Make sure the MongoDB backend is running on port 3000
2. **Node.js**: Version 16 or higher

### Installation

1. **Install Dependencies**:

   ```bash
   npm install
   ```

2. **Start Development Server**:

   ```bash
   npm run dev
   ```

3. **Open Browser**: Navigate to `http://localhost:5173`

## Authentication

The app includes a complete authentication system:

- **Login**: Sign in with username and password
- **Registration**: Create new user accounts
- **JWT Tokens**: Secure authentication with automatic token management
- **Protected Routes**: All main features require authentication

### API Endpoints Used

- `POST /register` - Create new user account
- `POST /login` - Authenticate user
- `GET /me` - Get current user information

## Project Structure

```
src/
├── API/
│   └── authApi.js          # Authentication API service
├── components/
│   ├── Login.jsx           # Login/Registration component
│   ├── SideBar.jsx         # Navigation sidebar
│   ├── FunctionTestView.jsx # Main chat interface
│   ├── AudioRecorder.jsx   # Voice recording component
│   ├── ChatLogs.jsx        # Chat history component
│   └── RobotStatus.jsx     # Robot status display
├── context/
│   └── AuthContext.jsx     # Authentication context
└── App.jsx                 # Main application component
```

## Environment Variables

The frontend connects to the backend at `http://localhost:3000` by default. If you need to change this, update the `API_BASE_URL` in `src/API/authApi.js`.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Technologies Used

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **Lucide React** - Icons
- **MQTT** - Real-time messaging
