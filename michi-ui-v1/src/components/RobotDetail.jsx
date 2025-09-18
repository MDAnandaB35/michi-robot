import React, { useState } from "react";
import { robotsApi } from "../API/robotsApi";
import {
  Bot,
  ArrowLeft,
  Edit2,
  Trash2,
  Save,
  X,
  AlertTriangle,
} from "lucide-react";

const RobotDetail = ({ robot, onBack, onRobotUpdated, onOwnershipRemoved }) => {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(robot.robotName);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);

  const handleUpdateName = async () => {
    if (!editedName.trim()) {
      setError("Robot name cannot be empty");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const updatedRobot = await robotsApi.updateRobotName(
        robot._id,
        editedName.trim()
      );
      setIsEditingName(false);
      onRobotUpdated?.(updatedRobot);
    } catch (e) {
      setError(e.response?.data?.message || "Failed to update robot name");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveOwnership = async () => {
    try {
      setLoading(true);
      setError(null);
      await robotsApi.removeOwnership(robot._id);
      onOwnershipRemoved?.(robot);
    } catch (e) {
      setError(e.response?.data?.message || "Failed to remove ownership");
    } finally {
      setLoading(false);
    }
  };

  const handleCancelEdit = () => {
    setEditedName(robot.robotName);
    setIsEditingName(false);
    setError(null);
  };

  return (
    <div className="flex-1 p-6 bg-gray-50 rounded-lg min-h-full">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-6">
          <button
            onClick={onBack}
            className="mr-4 p-2 hover:bg-gray-200 rounded-full transition-colors"
          >
            <ArrowLeft className="h-5 w-5 text-gray-600" />
          </button>
          <h2 className="text-3xl font-bold text-gray-900">Robot Details</h2>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 flex items-center bg-red-100 text-red-800 border border-red-200 rounded-lg">
            <AlertTriangle className="h-5 w-5 mr-3 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Robot Information Card */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center">
              <div className="p-3 bg-indigo-100 rounded-full mr-4">
                <Bot className="h-8 w-8 text-indigo-600" />
              </div>
              <div>
                <div className="flex items-center gap-3 mb-2">
                  {isEditingName ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={editedName}
                        onChange={(e) => setEditedName(e.target.value)}
                        className="text-xl font-semibold text-gray-800 border border-gray-300 rounded-md px-3 py-1 focus:ring-indigo-500 focus:border-indigo-500"
                        autoFocus
                      />
                      <button
                        onClick={handleUpdateName}
                        disabled={loading}
                        className="p-1 text-green-600 hover:bg-green-100 rounded transition-colors"
                      >
                        <Save className="h-4 w-4" />
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        disabled={loading}
                        className="p-1 text-gray-600 hover:bg-gray-100 rounded transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <h3 className="text-xl font-semibold text-gray-800">
                      {robot.robotName}
                    </h3>
                  )}
                  {!isEditingName && (
                    <button
                      onClick={() => setIsEditingName(true)}
                      className="p-1 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <p className="text-sm text-gray-500">ID: {robot.robotId}</p>
                <p className="text-sm text-gray-500">
                  Created: {new Date(robot.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Actions</h3>

          {/* Remove Ownership Button */}
          <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg">
            <div>
              <h4 className="font-medium text-red-800">Remove Ownership</h4>
              <p className="text-sm text-red-600 mt-1">
                This will remove your ownership of this robot. You can claim it
                again later if needed.
              </p>
            </div>
            <button
              onClick={() => setShowRemoveConfirm(true)}
              disabled={loading}
              className="flex items-center px-4 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Remove Ownership
            </button>
          </div>
        </div>

        {/* Remove Ownership Confirmation Modal */}
        {showRemoveConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center mb-4">
                <div className="p-2 bg-red-100 rounded-full mr-3">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Remove Ownership
                </h3>
              </div>
              <p className="text-gray-600 mb-6">
                Are you sure you want to remove your ownership of{" "}
                <strong>{robot.robotName}</strong>? You can claim this robot
                again later if needed.
              </p>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowRemoveConfirm(false)}
                  disabled={loading}
                  className="px-4 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-400 disabled:opacity-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRemoveOwnership}
                  disabled={loading}
                  className="flex items-center px-4 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  ) : (
                    <Trash2 className="h-4 w-4 mr-2" />
                  )}
                  {loading ? "Removing..." : "Remove Ownership"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RobotDetail;
