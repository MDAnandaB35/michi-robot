import axios from 'axios';
import { authService } from './authApi';

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || 'http://localhost:3001',
});

api.interceptors.request.use((config) => {
  const token = authService.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const robotsApi = {
  async getMyRobots() {
    const { data } = await api.get('/robots/mine');
    return data;
  },

  async claimRobot(robotId) {
    const { data } = await api.post('/robots/claim', { robotId });
    return data;
  },

  // Admin only
  async listAll() {
    const { data } = await api.get('/admin/robots');
    return data;
  },
  async create(robot) {
    const { data } = await api.post('/admin/robots', robot);
    return data;
  },
  async update(id, update) {
    const { data } = await api.put(`/admin/robots/${id}`, update);
    return data;
  },
  async remove(id) {
    const { data } = await api.delete(`/admin/robots/${id}`);
    return data;
  },
};

export default robotsApi;


