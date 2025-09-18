import React, { useState } from "react";
import { TestTube2, Wifi, FileText, Database } from "./Icons";
import { LogOut, User, Shield, MoreHorizontal, X } from "lucide-react";

const Sidebar = ({
  activeView,
  setActiveView,
  mobile,
  user,
  onLogout,
  selectedRobot,
  onClearSelectedRobot,
}) => {
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  // Define navigation items based on user role
  const getNavItems = () => {
    // Admin users see admin pages only
    if (user?.userName === "admin") {
      return [
        { id: "adminUsers", icon: Shield, label: "Admin Users" },
        { id: "adminRobots", icon: Shield, label: "Admin Robots" },
      ];
    }

    // Regular users see all other pages except FunStuff
    if (!selectedRobot) {
      return [{ id: "ownedRobots", icon: Database, label: "Owned Robots" }];
    }
    return [
      { id: "functionTest", icon: TestTube2, label: "Function Test" },
      { id: "AudioRecorder", icon: Wifi, label: "Audio Recorder" },
      { id: "logDebug", icon: FileText, label: "Chat Log" },
      { id: "detail", icon: Database, label: "Robot Details" },
    ];
  };

  const navItems = getNavItems();

  // User profile component (desktop only)
  const UserProfile = ({ user, onLogout }) => (
    <div>
      {/* Return to Owned Robots */}
      {selectedRobot && activeView !== "ownedRobots" && (
        <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg border border-gray-200 mt-auto mb-3">
          <button
            onClick={onClearSelectedRobot}
            className="mr-2 px-2 py-1 text-xs border rounded text-gray-700 "
          >
            Return to Owned Robots
          </button>
        </div>
      )}
      {/* Log out button */}
      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg border border-gray-200 mt-auto">
        <div className="h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center">
          <User className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {user?.userName}
          </p>
          <p className="text-xs text-gray-500">Logged in</p>
        </div>
        <button
          onClick={onLogout}
          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded-md transition-colors"
          title="Logout"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </div>
  );

  if (mobile) {
    // Bottom nav bar for mobile
    return (
      <>
        <div className="fixed bottom-0 left-0 w-full bg-white border-t border-gray-200 z-50 md:hidden">
          {/* Navigation items */}
          <nav className="flex justify-around items-center h-16">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveView(item.id)}
                  className={`flex flex-col bg-white items-center justify-center px-2 py-1 transition-colors duration-200 focus:outline-none ${
                    isActive
                      ? "text-lime-600"
                      : "text-gray-500 hover:text-lime-500"
                  }`}
                >
                  <Icon className="h-6 w-6 mb-1" />
                  <span className="text-xs leading-none">
                    {item.label.split(" ")[0]}
                  </span>
                </button>
              );
            })}
            {/* More menu button */}
            <button
              onClick={() => setShowMoreMenu(true)}
              className="flex flex-col bg-white items-center justify-center px-2 py-1 transition-colors duration-200 focus:outline-none text-gray-500 hover:text-lime-500"
            >
              <MoreHorizontal className="h-6 w-6 mb-1" />
              <span className="text-xs leading-none">More</span>
            </button>
          </nav>
        </div>

        {/* More Menu Popup */}
        {showMoreMenu && (
          <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-end justify-center z-50 md:hidden">
            <div className="bg-white w-full max-w-sm rounded-t-2xl p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  More Options
                </h3>
                <button
                  onClick={() => setShowMoreMenu(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <X className="h-5 w-5 text-gray-500" />
                </button>
              </div>

              {/* Menu Items */}
              <div className="space-y-3">
                {/* Robot Details - only show if robot is selected */}
                {selectedRobot && (
                  <button
                    onClick={() => {
                      setActiveView("detail");
                      setShowMoreMenu(false);
                    }}
                    className="w-full flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    <Database className="h-5 w-5 text-gray-600" />
                    <span className="text-gray-900">Robot Details</span>
                  </button>
                )}

                {/* Return to Owned Robots - only show if robot is selected */}
                {selectedRobot && activeView !== "ownedRobots" && (
                  <button
                    onClick={() => {
                      onClearSelectedRobot();
                      setShowMoreMenu(false);
                    }}
                    className="w-full flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    <Database className="h-5 w-5 text-gray-600" />
                    <span className="text-gray-900">
                      Return to Owned Robots
                    </span>
                  </button>
                )}

                {/* Logout */}
                <button
                  onClick={() => {
                    onLogout();
                    setShowMoreMenu(false);
                  }}
                  className="w-full flex items-center space-x-3 p-3 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <LogOut className="h-5 w-5 text-red-600" />
                  <span className="text-red-600">Logout</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  }

  // Sidebar for desktop
  return (
    <aside className="w-80 bg-white p-6 flex flex-col rounded-l-2xl border-r border-gray-200 h-full">
      <div className="mb-10">
        <img src="/michi_logo.png" alt="Robot Icon" className="mx-auto mb-4" />
        <div className="h-1 w-auto bg-green-300"></div>
      </div>
      <nav className="flex flex-col space-y-2 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`flex items-center space-x-3 p-3 rounded-lg text-left transition-colors duration-200 ${
                isActive
                  ? "bg-lime-500 text-white"
                  : "text-gray-600 hover:bg-gray-100 bg-white"
              }`}
            >
              <Icon className="h-6 w-6" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>
      {/* User profile at the bottom */}
      <UserProfile user={user} onLogout={onLogout} />
    </aside>
  );
};

export default Sidebar;
