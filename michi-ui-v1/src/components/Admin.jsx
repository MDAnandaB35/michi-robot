import React, { useState, useEffect } from "react";
import { Plus, Edit, Trash2, Search, UserPlus, Save, X } from "lucide-react";
import { adminService } from "../API/adminApi";
import { robotsApi } from "../API/robotsApi";

const Admin = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [formData, setFormData] = useState({
    userName: "",
    password: "",
  });
  const [message, setMessage] = useState({ type: "", text: "" });

  // Robot management state
  const [robots, setRobots] = useState([]);
  const [robotsLoading, setRobotsLoading] = useState(true);
  const [robotSearch, setRobotSearch] = useState("");
  const [showRobotCreateForm, setShowRobotCreateForm] = useState(false);
  const [editingRobot, setEditingRobot] = useState(null);
  const [robotForm, setRobotForm] = useState({ robotId: "", robotName: "" });
  const [robotMessage, setRobotMessage] = useState({ type: "", text: "" });

  useEffect(() => {
    fetchUsers();
    fetchRobots();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);

      // Debug: Check if we have a token
      const token = localStorage.getItem("jwt_token");
      console.log(
        "Current token:",
        token ? token.substring(0, 20) + "..." : "No token found"
      );

      const usersData = await adminService.getUsers();
      setUsers(usersData);
    } catch (error) {
      console.error("Error in fetchUsers:", error);
      setMessage({
        type: "error",
        text: "Failed to fetch users: " + error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: "", text: "" }), 5000);
  };

  const showRobotToast = (type, text) => {
    setRobotMessage({ type, text });
    setTimeout(() => setRobotMessage({ type: "", text: "" }), 5000);
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await adminService.createUser(formData);
      showMessage("success", "User created successfully!");
      setFormData({ userName: "", password: "" });
      setShowCreateForm(false);
      fetchUsers(); // Refresh the users list
    } catch (error) {
      showMessage("error", "Error creating user: " + error.message);
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const updateData = { userName: formData.userName };
      if (formData.password && formData.password.trim() !== "") {
        updateData.password = formData.password;
      }

      await adminService.updateUser(editingUser._id, updateData);
      showMessage("success", "User updated successfully!");
      setEditingUser(null);
      setFormData({ userName: "", password: "" });
      fetchUsers(); // Refresh the users list
    } catch (error) {
      showMessage("error", "Error updating user: " + error.message);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm("Are you sure you want to delete this user?")) {
      try {
        await adminService.deleteUser(userId);
        showMessage("success", "User deleted successfully!");
        fetchUsers(); // Refresh the users list
      } catch (error) {
        showMessage("error", "Error deleting user: " + error.message);
      }
    }
  };

  const startEdit = (user) => {
    setEditingUser(user);
    setFormData({ userName: user.userName, password: "" });
  };

  const cancelEdit = () => {
    setEditingUser(null);
    setFormData({ userName: "", password: "" });
  };

  const filteredUsers = users.filter((user) =>
    user.userName.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // ROBOTS: API helpers
  const fetchRobots = async () => {
    try {
      setRobotsLoading(true);
      const list = await robotsApi.listAll();
      setRobots(list);
    } catch (error) {
      console.error("Error in fetchRobots:", error);
      showRobotToast(
        "error",
        "Failed to fetch robots: " +
          (error.response?.data?.message || error.message)
      );
    } finally {
      setRobotsLoading(false);
    }
  };

  const handleRobotInputChange = (e) => {
    setRobotForm({ ...robotForm, [e.target.name]: e.target.value });
  };

  const handleCreateRobot = async (e) => {
    e.preventDefault();
    try {
      await robotsApi.create({
        robotId: robotForm.robotId.trim(),
        robotName: robotForm.robotName.trim(),
      });
      showRobotToast("success", "Robot created successfully!");
      setRobotForm({ robotId: "", robotName: "" });
      setShowRobotCreateForm(false);
      fetchRobots();
    } catch (error) {
      showRobotToast(
        "error",
        "Error creating robot: " +
          (error.response?.data?.message || error.message)
      );
    }
  };

  const startEditRobot = (robot) => {
    setEditingRobot(robot);
    setRobotForm({ robotId: robot.robotId, robotName: robot.robotName });
  };

  const cancelEditRobot = () => {
    setEditingRobot(null);
    setRobotForm({ robotId: "", robotName: "" });
  };

  const handleUpdateRobot = async (e) => {
    e.preventDefault();
    try {
      await robotsApi.update(editingRobot._id, {
        robotName: robotForm.robotName.trim(),
      });
      showRobotToast("success", "Robot updated successfully!");
      setEditingRobot(null);
      setRobotForm({ robotId: "", robotName: "" });
      fetchRobots();
    } catch (error) {
      showRobotToast(
        "error",
        "Error updating robot: " +
          (error.response?.data?.message || error.message)
      );
    }
  };

  const handleDeleteRobot = async (id) => {
    if (window.confirm("Are you sure you want to delete this robot?")) {
      try {
        await robotsApi.remove(id);
        showRobotToast("success", "Robot deleted successfully!");
        fetchRobots();
      } catch (error) {
        showRobotToast(
          "error",
          "Error deleting robot: " +
            (error.response?.data?.message || error.message)
        );
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          User Management
        </h1>
        <p className="text-gray-600">Manage system users and their access</p>
      </div>

      {/* Message Display */}
      {message.text && (
        <div
          className={`mb-4 p-4 rounded-lg ${
            message.type === "success"
              ? "bg-green-50 border border-green-200 text-green-700"
              : "bg-red-50 border border-red-200 text-red-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Debug Information */}
      <div className="mb-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <h4 className="font-semibold text-gray-700 mb-2">Debug Information</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <div>
            Token available: {localStorage.getItem("jwt_token") ? "Yes" : "No"}
          </div>
          <div>
            Token length: {localStorage.getItem("jwt_token")?.length || 0}
          </div>
          <div>API Base URL: {adminService.baseURL}</div>
          <div>Current user: {JSON.stringify(window.user || "Not set")}</div>
        </div>
      </div>

      {/* Search and Create */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
        >
          <UserPlus className="h-5 w-5 mr-2" />
          Add User
        </button>
      </div>

      {/* Create User Form */}
      {showCreateForm && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Create New User
          </h3>
          <form onSubmit={handleCreateUser} className="space-y-4">
            <div>
              <label
                htmlFor="userName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Username
              </label>
              <input
                type="text"
                id="userName"
                name="userName"
                required
                value={formData.userName}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter username"
              />
            </div>
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter password"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
              >
                <Save className="h-5 w-5 mr-2" />
                Create User
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <X className="h-5 w-5 mr-2" />
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit User Form */}
      {editingUser && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Edit User: {editingUser.userName}
          </h3>
          <form onSubmit={handleUpdateUser} className="space-y-4">
            <div>
              <label
                htmlFor="editUserName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Username
              </label>
              <input
                type="text"
                id="editUserName"
                name="userName"
                required
                value={formData.userName}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter username"
              />
            </div>
            <div>
              <label
                htmlFor="editPassword"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                New Password (leave blank to keep current)
              </label>
              <input
                type="password"
                id="editPassword"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter new password"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <Save className="h-5 w-5 mr-2" />
                Update User
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <X className="h-5 w-5 mr-2" />
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Username
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user._id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {user.userName}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">
                      {new Date(user.createdAt).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => startEdit(user)}
                        className="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50 transition-colors"
                        title="Edit user"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user._id)}
                        className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors"
                        title="Delete user"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filteredUsers.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500">No users found</p>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="h-1 w-full my-8 bg-gray-100" />

      {/* ROBOT MANAGEMENT */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Robot Management
        </h1>
        <p className="text-gray-600">Create, update, and delete robots</p>
      </div>

      {/* Message Display */}
      {robotMessage.text && (
        <div
          className={`mb-4 p-4 rounded-lg ${
            robotMessage.type === "success"
              ? "bg-green-50 border border-green-200 text-green-700"
              : "bg-red-50 border border-red-200 text-red-700"
          }`}
        >
          {robotMessage.text}
        </div>
      )}

      {/* Search and Create */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search robots..."
            value={robotSearch}
            onChange={(e) => setRobotSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <button
          onClick={() => setShowRobotCreateForm(true)}
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          Add Robot
        </button>
      </div>

      {/* Create Robot Form */}
      {showRobotCreateForm && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Create New Robot
          </h3>
          <form onSubmit={handleCreateRobot} className="space-y-4">
            <div>
              <label
                htmlFor="robotId"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Robot ID
              </label>
              <input
                type="text"
                id="robotId"
                name="robotId"
                required
                value={robotForm.robotId}
                onChange={handleRobotInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter unique robot ID"
              />
            </div>
            <div>
              <label
                htmlFor="robotName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Robot Name
              </label>
              <input
                type="text"
                id="robotName"
                name="robotName"
                required
                value={robotForm.robotName}
                onChange={handleRobotInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter display name"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors"
              >
                <Save className="h-5 w-5 mr-2" />
                Create Robot
              </button>
              <button
                type="button"
                onClick={() => setShowRobotCreateForm(false)}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <X className="h-5 w-5 mr-2" />
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Edit Robot Form */}
      {editingRobot && (
        <div className="bg-white p-6 rounded-lg border border-gray-200 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Edit Robot: {editingRobot.robotId}
          </h3>
          <form onSubmit={handleUpdateRobot} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Robot ID
              </label>
              <input
                type="text"
                value={robotForm.robotId}
                disabled
                className="w-full px-3 py-2 border border-gray-200 bg-gray-50 rounded-lg"
              />
            </div>
            <div>
              <label
                htmlFor="editRobotName"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Robot Name
              </label>
              <input
                type="text"
                id="editRobotName"
                name="robotName"
                required
                value={robotForm.robotName}
                onChange={handleRobotInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Enter robot name"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <Save className="h-5 w-5 mr-2" />
                Update Robot
              </button>
              <button
                type="button"
                onClick={cancelEditRobot}
                className="inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <X className="h-5 w-5 mr-2" />
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Robots Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Robot ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Owners
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created At
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {(robotsLoading ? [] : robots)
                .filter((r) =>
                  (r.robotId + " " + r.robotName)
                    .toLowerCase()
                    .includes(robotSearch.toLowerCase())
                )
                .map((r) => (
                  <tr key={r._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {r.robotId}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{r.robotName}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {Array.isArray(r.ownerUserIds)
                          ? r.ownerUserIds.length
                          : 0}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {new Date(r.createdAt).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => startEditRobot(r)}
                          className="text-indigo-600 hover:text-indigo-900 p-1 rounded hover:bg-indigo-50 transition-colors"
                          title="Edit robot"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteRobot(r._id)}
                          className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors"
                          title="Delete robot"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        {!robotsLoading &&
          robots.filter((r) =>
            (r.robotId + " " + r.robotName)
              .toLowerCase()
              .includes(robotSearch.toLowerCase())
          ).length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500">No robots found</p>
            </div>
          )}
        {robotsLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
