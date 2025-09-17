import React, { useEffect, useState } from "react";
import { Plus, Edit, Trash2, Search, Save, X } from "lucide-react";
import { robotsApi } from "../API/robotsApi";

const AdminRobots = () => {
  const [robots, setRobots] = useState([]);
  const [robotsLoading, setRobotsLoading] = useState(true);
  const [robotSearch, setRobotSearch] = useState("");
  const [showRobotCreateForm, setShowRobotCreateForm] = useState(false);
  const [editingRobot, setEditingRobot] = useState(null);
  const [robotForm, setRobotForm] = useState({ robotId: "", robotName: "" });
  const [robotMessage, setRobotMessage] = useState({ type: "", text: "" });

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchRobots();
  }, []);

  const showRobotToast = (type, text) => {
    setRobotMessage({ type, text });
    setTimeout(() => setRobotMessage({ type: "", text: "" }), 5000);
  };

  const fetchRobots = async () => {
    try {
      setRobotsLoading(true);
      const list = await robotsApi.listAll();
      setRobots(list);
    } catch (error) {
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

  // Filter and paginate
  const filtered = robots.filter((r) =>
    (r.robotId + " " + r.robotName)
      .toLowerCase()
      .includes(robotSearch.toLowerCase())
  );
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIdx = (currentPage - 1) * pageSize;
  const pageItems = filtered.slice(startIdx, startIdx + pageSize);

  const Pagination = () => (
    <div className="flex items-center justify-between p-4">
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>Rows per page</span>
        <select
          value={pageSize}
          onChange={(e) => {
            setPageSize(Number(e.target.value));
            setPage(1);
          }}
          className="border rounded px-2 py-1"
        >
          {[5, 10, 20, 50].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
        <span>
          {filtered.length === 0 ? 0 : startIdx + 1}-
          {Math.min(filtered.length, startIdx + pageSize)} of {filtered.length}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button
          disabled={currentPage === 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Prev
        </button>
        <span className="text-sm">
          Page {currentPage} / {totalPages}
        </span>
        <button
          disabled={currentPage === totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="px-3 py-1 border rounded disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Robot Management
        </h1>
        <p className="text-gray-600">Create, update, and delete robots</p>
      </div>

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

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search robots..."
            value={robotSearch}
            onChange={(e) => {
              setRobotSearch(e.target.value);
              setPage(1);
            }}
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
                className="text-black w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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
                className="text-black w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
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
              {pageItems.map((r) => (
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
        {filtered.length === 0 && !robotsLoading && (
          <div className="text-center py-8">
            <p className="text-gray-500">No robots found</p>
          </div>
        )}
        {robotsLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        )}
        {filtered.length > 0 && <Pagination />}
      </div>
    </div>
  );
};

export default AdminRobots;
