import React, { useState, useEffect, useRef } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Sidebar from "./components/SideBar";
import FunctionTestView from "./components/FunctionTestView";
import RobotStatus from "./components/RobotStatus";
import AudioRecorder from "./components/AudioRecorder";
import ChatLogs from "./components/ChatLogs";
import Login from "./components/Login";
import { LogOut, User } from "lucide-react";

const PlaceholderView = ({ title }) => (
  <main className="flex-1 p-8">
    <h2 className="text-3xl font-bold text-gray-800 mb-6">{title}</h2>
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <p className="text-gray-500">
        This is a placeholder for the {title} page. Content will be added here.
        <img
          className="w-full h-auto"
          src="https://preview.redd.it/what-is-going-on-with-all-the-teto-is-fat-meme-can-someone-v0-pkb2vpbtp5re1.jpeg?width=216&format=pjpg&auto=webp&s=a95f5136926c1a5b975226b379a9648e252b7a33"
        />
      </p>
    </div>
  </main>
);

// User profile component
const UserProfile = ({ user, onLogout }) => (
  <div className="flex items-center space-x-3 p-4 bg-white rounded-lg shadow-sm">
    <div className="h-10 w-10 bg-indigo-600 rounded-full flex items-center justify-center">
      <User className="h-5 w-5 text-white" />
    </div>
    <div className="flex-1">
      <p className="text-sm font-medium text-gray-900">{user?.userName}</p>
      <p className="text-xs text-gray-500">Logged in</p>
    </div>
    <button
      onClick={onLogout}
      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
      title="Logout"
    >
      <LogOut className="h-5 w-5" />
    </button>
  </div>
);

// Main App component that structures the entire page
const AppContent = () => {
  const [activeView, setActiveView] = useState("functionTest");
  const { user, loading, logout, isAuthenticated } = useAuth();

  const renderActiveView = () => {
    switch (activeView) {
      case "functionTest":
        return <FunctionTestView />;
      case "AudioRecorder":
        return <AudioRecorder />;
      case "logDebug":
        return <ChatLogs />;
      case "funStuff":
        return <PlaceholderView title="Fun Stuff" />;
      case "detail":
        return <PlaceholderView title="Detail" />;
      default:
        return <FunctionTestView />;
    }
  };

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-200 flex items-center justify-center">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="text-gray-600">Loading...</span>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  // Responsive: Sidebar for desktop, BottomNavBar for mobile
  return (
    <div className="bg-gray-200 h-screen w-screen font-sans overflow-y-auto">
      <div className="w-full md:h-full bg-transparent rounded-2xl flex flex-col md:flex-row overflow-hidden p-3 pb-20 md:p-0">
        {/* Sidebar (desktop) */}
        <div className="hidden md:block">
          <Sidebar activeView={activeView} setActiveView={setActiveView} />
        </div>
        {/* Bottom nav bar (mobile) */}
        <div className="block md:hidden w-full">
          <Sidebar
            activeView={activeView}
            setActiveView={setActiveView}
            mobile
          />
        </div>
        {/* Main content area */}
        <div className="flex-grow flex flex-col md:flex-row">
          {/* renderActiveView - 60% */}
          <div className="w-full h-full md:h-auto md:w-3/5 bg-white rounded-2xl md:m-3 px-2 py-5 main-content-mobile-padding">
            {renderActiveView()}
          </div>
          {/* RobotStatus - 40%, hidden on mobile */}
          <div className="hidden md:block w-2/5 m-3 max-h-screen">
            <div className="space-y-3">
              <UserProfile user={user} onLogout={logout} />
              <RobotStatus />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Wrapper component with AuthProvider
export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
