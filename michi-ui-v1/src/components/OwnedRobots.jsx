import React, { useEffect, useState } from "react";
import { robotsApi } from "../API/robotsApi";

const OwnedRobots = ({ onSelectRobot }) => {
  const [robots, setRobots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [robotIdInput, setRobotIdInput] = useState("");
  const [claiming, setClaiming] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      const list = await robotsApi.getMyRobots();
      setRobots(list);
    } catch (e) {
      setError(e.response?.data?.message || "Failed to load robots");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleClaim = async (e) => {
    e.preventDefault();
    if (!robotIdInput.trim()) return;
    try {
      setClaiming(true);
      setError(null);
      await robotsApi.claimRobot(robotIdInput.trim());
      setRobotIdInput("");
      await load();
    } catch (e) {
      setError(e.response?.data?.message || "Failed to claim robot");
    } finally {
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <main className="flex-1 p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Owned Robots</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded">
          {error}
        </div>
      )}

      {robots.length === 0 && (
        <div className="mb-6 p-4 bg-white rounded border">
          <p className="mb-3 text-gray-700">
            You don't own any robots yet. Enter a Robot ID to claim ownership.
          </p>
          <form onSubmit={handleClaim} className="flex gap-2">
            <input
              type="text"
              value={robotIdInput}
              onChange={(e) => setRobotIdInput(e.target.value)}
              placeholder="Enter Robot ID"
              className="text-black flex-1 border rounded px-3 py-2"
            />
            <button
              type="submit"
              disabled={claiming}
              className="px-4 py-2 bg-indigo-600 text-white rounded disabled:opacity-50"
            >
              {claiming ? "Claiming..." : "Claim"}
            </button>
          </form>
        </div>
      )}

      {robots.length > 0 && (
        <div className="grid grid-cols-1 gap-3">
          {robots.map((r) => (
            <button
              key={r._id}
              onClick={() => onSelectRobot?.(r)}
              className="text-left p-4 bg-white rounded border hover:shadow"
            >
              <div className="font-semibold">{r.robotName}</div>
              <div className="text-sm text-gray-500">ID: {r.robotId}</div>
            </button>
          ))}
        </div>
      )}

      {robots.length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 rounded border">
          <p className="mb-3 text-gray-700">
            Want to add another robot? Enter a Robot ID to claim it.
          </p>
          <form onSubmit={handleClaim} className="flex gap-2">
            <input
              type="text"
              value={robotIdInput}
              onChange={(e) => setRobotIdInput(e.target.value)}
              placeholder="Enter Robot ID"
              className="flex-1 border rounded px-3 py-2"
            />
            <button
              type="submit"
              disabled={claiming}
              className="px-4 py-2 bg-indigo-600 text-white rounded disabled:opacity-50"
            >
              {claiming ? "Claiming..." : "Claim"}
            </button>
          </form>
        </div>
      )}
    </main>
  );
};

export default OwnedRobots;
