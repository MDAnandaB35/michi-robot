import { TestTube2, Wifi, FileText, Sparkles, Database } from "./Icons";

const navItems = [
  { id: "functionTest", icon: TestTube2, label: "Function Test" },
  { id: "AudioRecorder", icon: Wifi, label: "Audio Recorder" },
  { id: "logDebug", icon: FileText, label: "Chat Log" },
  { id: "funStuff", icon: Sparkles, label: "Fun Stuff" },
  { id: "detail", icon: Database, label: "Robot Detail" },
];

const Sidebar = ({ activeView, setActiveView, mobile }) => {
  if (mobile) {
    // Bottom nav bar for mobile
    return (
      <nav className="fixed bottom-0 left-0 w-full bg-white border-t border-gray-200 flex justify-around items-center z-50 h-16 md:hidden">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`flex flex-col items-center justify-center px-2 py-1 transition-colors duration-200 focus:outline-none ${
                isActive ? "text-lime-600" : "text-gray-500 hover:text-lime-500"
              }`}
            >
              <Icon className="h-6 w-6 mb-1" />
              <span className="text-xs leading-none">
                {item.label.split(" ")[0]}
              </span>
            </button>
          );
        })}
      </nav>
    );
  }

  // Sidebar for desktop
  return (
    <aside className="w-80 bg-white p-6 flex flex-col rounded-l-2xl border-r border-gray-200 h-full">
      <div className="mb-10">
        <img src="/michi_logo.png" alt="Robot Icon" className="mx-auto mb-4" />
        <div className="h-1 w-auto bg-green-300"></div>
      </div>
      <nav className="flex flex-col space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`flex items-center space-x-3 p-3 rounded-lg text-left transition-colors duration-200 ${
                isActive
                  ? "bg-lime-500 text-white"
                  : "text-gray-600 hover:bg-gray-100 bg-white"
              }`}
            >
              <Icon className="h-6 w-6" />
              <span className="font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;
