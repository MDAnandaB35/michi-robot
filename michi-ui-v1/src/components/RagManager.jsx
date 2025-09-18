import React, { useEffect, useState } from "react";
import { ragApi } from "../API/ragApi";
import { useAuth } from "../context/AuthContext";
import { Upload, Trash2, FileText, RefreshCw } from "lucide-react";

const RagManager = ({ robot }) => {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [previewItem, setPreviewItem] = useState(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await ragApi.listKnowledge(user?.userName, robot?.robotId);
      setItems(list);
    } catch (e) {
      setError(e.message || "Failed to load knowledge");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file");
      return;
    }
    try {
      setUploading(true);
      setError(null);
      await ragApi.uploadKnowledge({
        userId: user?.userName,
        robotId: robot?.robotId,
        file,
        filename: file.name,
      });
      await load();
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  const handleDelete = async (id) => {
    try {
      setError(null);
      await ragApi.deleteKnowledge(id);
      setItems((prev) => prev.filter((i) => i._id !== id));
    } catch (err) {
      setError(err.message || "Delete failed");
    }
  };

  return (
    <>
      <div className="flex-1 p-6 bg-gray-50 rounded-lg min-h-full">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center mb-6">
            <h2 className="text-3xl font-bold text-gray-900">RAG Knowledge</h2>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-800 border border-red-200 rounded-lg">
              {error}
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-1">
                  Upload PDF
                </h3>
                <p className="text-sm text-gray-500">
                  PDF will be chunked and embedded, then stored.
                </p>
              </div>
              <label className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md cursor-pointer hover:bg-indigo-700">
                <Upload className="h-4 w-4 mr-2" />
                {uploading ? "Uploading..." : "Select PDF"}
                <input
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={handleUpload}
                  disabled={uploading}
                />
              </label>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Uploaded Knowledge
              </h3>
              <button
                onClick={load}
                className="flex items-center px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-md"
              >
                <RefreshCw className="h-4 w-4 mr-1" /> Refresh
              </button>
            </div>

            {loading ? (
              <div className="text-gray-500">Loading...</div>
            ) : items.length === 0 ? (
              <div className="text-gray-500">No knowledge uploaded yet.</div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {items.map((item) => (
                  <li
                    key={item._id}
                    className="py-3 flex items-center justify-between"
                  >
                    <div className="flex items-center">
                      <div className="p-2 bg-indigo-100 rounded mr-3">
                        <FileText className="h-5 w-5 text-indigo-600" />
                      </div>
                      <div>
                        <button
                          type="button"
                          onClick={() => setPreviewItem(item)}
                          className="font-medium text-indigo-600 hover:underline text-left"
                          title="View document content"
                        >
                          {item.filename}
                        </button>
                        <div className="text-xs text-gray-500">
                          {item.chunk_count ?? 0} chunks •{" "}
                          {item.uploaded_at
                            ? new Date(item.uploaded_at).toLocaleString()
                            : ""}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDelete(item._id)}
                      className="flex items-center px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-md"
                    >
                      <Trash2 className="h-4 w-4 mr-1" /> Delete
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {previewItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] mx-4 flex flex-col">
            <div className="px-5 py-3 border-b flex items-center justify-between">
              <div className="font-semibold text-gray-900 truncate pr-4">
                {previewItem.filename}
              </div>
              <button
                onClick={() => setPreviewItem(null)}
                className="px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-md"
              >
                Close
              </button>
            </div>
            <div className="p-5 overflow-auto">
              <div className="text-sm text-gray-800 whitespace-pre-wrap">
                {previewItem.full_text || "No content available."}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default RagManager;
