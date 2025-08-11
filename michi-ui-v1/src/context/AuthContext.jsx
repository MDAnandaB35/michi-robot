import React, { createContext, useContext, useState, useEffect } from "react";
import { authService } from "../API/authApi";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const userData = await authService.getCurrentUser();
          setUser(userData.user);
        }
      } catch (error) {
        console.error("Auth check failed:", error);
        authService.logout();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (credentials) => {
    try {
      setError(null);
      const response = await authService.login(credentials);
      const userData = await authService.getCurrentUser();
      setUser(userData.user);
      return response;
    } catch (error) {
      setError(error.response?.data?.message || "Login failed");
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      setError(null);
      const response = await authService.register(userData);
      return response;
    } catch (error) {
      setError(error.response?.data?.message || "Registration failed");
      throw error;
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setError(null);
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
