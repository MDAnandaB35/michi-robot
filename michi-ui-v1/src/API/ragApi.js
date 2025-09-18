const SERVER_ORIGIN = import.meta.env.VITE_API_BASE_URL; // Python server base (host:port)

export const ragApi = {
  async listKnowledge(userId, robotId) {
    const q = new URLSearchParams();
    if (userId) q.set('user_id', userId);
    if (robotId) q.set('robot_id', robotId);
    const qs = q.toString();
    const url = `http://${SERVER_ORIGIN}/rag/knowledge${qs ? `?${qs}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to list knowledge');
    return await res.json();
  },

  async uploadKnowledge({ userId, robotId, file, filename }) {
    const url = `http://${SERVER_ORIGIN}/rag/knowledge`;
    const form = new FormData();
    form.append('user_id', userId);
    if (robotId) form.append('robot_id', robotId);
    if (filename) form.append('filename', filename);
    form.append('file', file);
    const res = await fetch(url, { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to upload knowledge');
    }
    return await res.json();
  },

  async deleteKnowledge(id) {
    const url = `http://${SERVER_ORIGIN}/rag/knowledge/${encodeURIComponent(id)}`;
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Failed to delete knowledge');
    }
    return await res.json();
  }
};

export default ragApi;


