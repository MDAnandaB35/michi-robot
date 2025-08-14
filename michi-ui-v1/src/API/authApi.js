import axios from 'axios';

const API_BASE_URL = (() => {
  const origin = import.meta.env.VITE_AUTH_ORIGIN;
  return origin;
})();

// Create axios instance with base configuration
const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include JWT token
authApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token expiration
authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  // Login user
  login: async (credentials) => {
    const response = await authApi.post('/login', credentials);
    if (response.data.token) {
      localStorage.setItem('jwt_token', response.data.token);
    }
    return response.data;
  },

  // Get current user info
  getCurrentUser: async () => {
    const response = await authApi.get('/me');
    return response.data;
  },

  // Logout user
  logout: () => {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('user');
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('jwt_token');
  },

  // Get stored token
  getToken: () => {
    return localStorage.getItem('jwt_token');
  }
};

export default authApi; 