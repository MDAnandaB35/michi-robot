import React, { useEffect, useState } from "react";
import { robotsApi } from "../API/robotsApi";
import { Bot, Plus, AlertTriangle } from "lucide-react";

// New Component: Card for displaying a single robot
const RobotCard = ({ robot, onSelectRobot }) => (
  <button
    onClick={() => onSelectRobot?.(robot)}
    className="flex items-center w-full text-left p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md hover:border-indigo-500 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
  >
    <div className="p-3 bg-indigo-100 rounded-full mr-4">
      <Bot className="h-6 w-6 text-indigo-600" />
    </div>
    <div>
      <div className="font-semibold text-gray-800">{robot.robotName}</div>
      <div className="text-sm text-gray-500">ID: {robot.robotId}</div>
    </div>
  </button>
);

// New Component: The form for claiming a new robot
const ClaimRobotForm = ({ onSubmit, onCancel, claiming }) => {
  const [robotIdInput, setRobotIdInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!robotIdInput.trim()) return;
    onSubmit(robotIdInput.trim());
  };

  return (
    <div className="p-4 mb-6 bg-gray-50 rounded-lg border border-gray-200">
      <p className="mb-3 font-medium text-gray-700">Claim a new robot</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={robotIdInput}
          onChange={(e) => setRobotIdInput(e.target.value)}
          placeholder="Enter your Robot's unique ID"
          className="text-blackflex-1 border-gray-300 rounded-md px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
          autoFocus
        />
        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={claiming || !robotIdInput.trim()}
            className="px-4 py-2 bg-indigo-600 text-white font-semibold rounded-md disabled:opacity-50 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            {claiming ? "Claiming..." : "Claim Robot"}
          </button>
        </div>
      </form>
    </div>
  );
};

// New Component: A clean empty state when no robots are owned
const EmptyState = ({ onClaimClick }) => (
  <div className="text-center p-8 bg-white rounded-lg border-2 border-dashed">
    <Bot size={48} className="mx-auto text-gray-400 mb-4" />
    <h3 className="text-xl font-semibold text-gray-800">No robots found</h3>
    <p className="text-gray-500 mt-2 mb-6">
      Get started by claiming your first robot.
    </p>
    <button
      onClick={onClaimClick}
      className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-700"
    >
      <Plus size={20} className="mr-2 -ml-1" />
      Claim Your First Robot
    </button>
  </div>
);

// Main Component (Refactored)
const OwnedRobots = ({ onSelectRobot }) => {
  const [robots, setRobots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [showClaimForm, setShowClaimForm] = useState(false);

  const loadRobots = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await robotsApi.getMyRobots();
      setRobots(list);
    } catch (e) {
      setError(e.response?.data?.message || "Failed to load robots");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRobots();
  }, []);

  const handleClaim = async (robotId) => {
    try {
      setClaiming(true);
      setError(null);
      await robotsApi.claimRobot(robotId);
      setShowClaimForm(false); // Hide form on success
      await loadRobots(); // Refresh the list
    } catch (e) {
      setError(
        e.response?.data?.message ||
          "Failed to claim robot. Please check the ID."
      );
    } finally {
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-10">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <main className="flex-1 p-6 bg-gray-50 rounded-lg min-h-full">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">My Robots</h2>
          {robots.length > 0 && !showClaimForm && (
            <button
              onClick={() => setShowClaimForm(true)}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white font-semibold rounded-md hover:bg-indigo-700"
            >
              <Plus size={20} className="mr-2 -ml-1" />
              Add Robot
            </button>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 flex items-center bg-red-100 text-red-800 border border-red-200 rounded-lg">
            <AlertTriangle className="h-5 w-5 mr-3 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {showClaimForm && (
          <ClaimRobotForm
            onSubmit={handleClaim}
            onCancel={() => setShowClaimForm(false)}
            claiming={claiming}
          />
        )}

        {robots.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {robots.map((r) => (
              <RobotCard key={r._id} robot={r} onSelectRobot={onSelectRobot} />
            ))}
          </div>
        ) : (
          !showClaimForm && (
            <EmptyState onClaimClick={() => setShowClaimForm(true)} />
          )
        )}
      </div>
    </main>
  );
};

export default OwnedRobots;
