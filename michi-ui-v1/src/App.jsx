import React, { useState, useEffect, useRef } from "react";
import Sidebar from "./components/SideBar";
import FunctionTestView from "./components/FunctionTestView";
import RobotStatus from "./components/RobotStatus";
import AudioRecorder from "./components/AudioRecorder";
import ChatLogs from "./components/ChatLogs";

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

// Main App component that structures the entire page
export default function App() {
  const [activeView, setActiveView] = useState("functionTest");

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

  // Responsive: Sidebar for desktop, BottomNavBar for mobile
  return (
    <div className="bg-gray-200 h-screen w-screen font-sans">
      <div className="w-full h-full bg-transparent rounded-2xl shadow-2xl flex flex-col md:flex-row overflow-hidden p-3 md:p-0">
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
          <div className="w-full h-170 md:h-auto md:w-3/5 bg-white rounded-2xl overflow-y-auto md:m-3 px-2 py-5 main-content-mobile-padding">
            {renderActiveView()}
          </div>
          {/* RobotStatus - 40%, hidden on mobile */}
          <div className="hidden md:block w-2/5 m-3 max-h-screen">
            <RobotStatus />
          </div>
        </div>
      </div>
    </div>
  );
}
