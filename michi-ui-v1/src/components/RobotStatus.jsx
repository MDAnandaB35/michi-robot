// Component for the robot status card on the right
import React from "react";

const RobotStatus = () => {
  // Check circle icon component
  const CheckCircle = (props) => (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );

  return (
    <aside className="bg-green-100 p-4 sm:p-6 flex flex-col items-center justify-between rounded-2xl relative w-full h-full overflow-hidden">

      {/* Status Icon */}
      <div className="absolute top-2 right-2 sm:top-4 sm:right-4 bg-green-500 text-white rounded-full p-1 z-10">
        <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5" />
      </div>

      {/* Main Image */}
      <div className="flex-1 w-full flex items-center justify-center overflow-hidden">
        <img
          src="/michi_render.png"
          alt="Michi Render"
          className="max-h-full max-w-full object-contain transition-transform duration-300 hover:scale-105"
        />
      </div>

      {/* Logo */}
      <div className="w-full flex justify-center">
        <img
          src="/michi_logo.png"
          alt="Robot Icon"
          className="mb-4 max-w-[50%] h-auto object-contain"
        />
      </div>
    </aside>

  );
};

export default RobotStatus;
