import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { User, Lock, Mail, Eye, EyeOff } from "lucide-react";

const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    userName: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [mouseX, setMouseX] = useState(0);
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const [mouseDirection, setMouseDirection] = useState("stationary"); // "left", "right", or "stationary"

  // Use refs for values that don't need to trigger re-renders
  const lastMouseX = useRef(0);
  const moveTimeoutId = useRef(null);

  const { login, register, error } = useAuth();

  // This effect now runs only once on mount
  useEffect(() => {
    const handleMouseMove = (e) => {
      const currentX = e.clientX;

      // Always clear the previous timeout
      clearTimeout(moveTimeoutId.current);

      // Determine direction using the ref's value
      if (currentX < lastMouseX.current) {
        setMouseDirection("left");
      } else if (currentX > lastMouseX.current) {
        setMouseDirection("right");
      }

      // Update the state that controls the image's visual position
      setMouseX(currentX);
      // Update the ref for the next move event
      lastMouseX.current = currentX;

      // Set a new timeout to switch to stationary
      moveTimeoutId.current = setTimeout(() => {
        setMouseDirection("stationary");
      }, 150); // Using a slightly shorter delay for better responsiveness
    };

    const handleResize = () => {
      setScreenWidth(window.innerWidth);
    };

    const handleMouseLeave = () => {
      // When mouse leaves, immediately become stationary
      clearTimeout(moveTimeoutId.current);
      setMouseDirection("stationary");
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("resize", handleResize);
    document.body.addEventListener("mouseleave", handleMouseLeave);

    // Cleanup function
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
      clearTimeout(moveTimeoutId.current); // Ensure cleanup on unmount
    };
  }, []); // <-- The empty dependency array is crucial!

  // Determine which image to show based on mouse position and direction
  const isRightHalf = mouseX > screenWidth / 2;

  let currentImage = "/michigreeting.png"; // default

  if (mouseDirection === "left") {
    currentImage = "/michileft.png";
  } else if (mouseDirection === "right") {
    currentImage = "/michiright.png";
  } else if (mouseDirection === "stationary") {
    // If stationary, use the half-screen logic
    currentImage = isRightHalf ? "/michiwave.png" : "/michigreeting.png";
  }

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login({
          username: formData.userName,
          password: formData.password,
        });
      } else {
        await register(formData);
        // After successful registration, switch to login
        setIsLogin(true);
        setFormData({ userName: "", password: "" });
      }
    } catch (error) {
      console.error("Auth error:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({ userName: "", password: "" });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Michi image that follows mouse horizontally */}
      <div
        className="fixed pointer-events-none z-10 transition-transform duration-100 ease-out"
        style={{
          left: `${mouseX - 50}px`, // Center the image on mouse (assuming 100px width)
          top: "50%",
          transform: "translateY(-50%)",
        }}
      >
        <img
          src={currentImage}
          alt="Michi Robot"
          className="w-94 h-94 object-contain"
        />
      </div>

      <div className="max-w-md w-full space-y-8 relative z-20">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
            <User className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900">
            {isLogin ? "お帰りなさい!" : "Create Account"}
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {isLogin
              ? "Welcome back, マスター!"
              : "Join us and start your journey"}
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username Field */}
            <div>
              <label
                htmlFor="userName"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Robot ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="userName"
                  name="userName"
                  type="text"
                  required
                  value={formData.userName}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors text-blue-700"
                  placeholder="Enter your username"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors text-blue-700"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                  )}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {isLogin ? "Signing in..." : "Creating account..."}
                </div>
              ) : isLogin ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* Toggle Mode */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                onClick={toggleMode}
                className="ml-1 font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
              >
                {isLogin ? "Sign up" : "Sign in"}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center">
          <p className="text-xs text-gray-500">
            © 2024 Michi Chatbot. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
