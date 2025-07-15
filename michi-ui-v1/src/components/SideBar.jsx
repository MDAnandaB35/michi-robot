
import { TestTube2, Wifi, FileText, Sparkles, Database } from "./Icons";// Component for the navigation sidebar on the left
const Sidebar = ({ activeView, setActiveView }) => {
  const navItems = [
    { id: "functionTest", icon: TestTube2, label: "Function Test" },
    { id: "AudioRecorder", icon: Wifi, label: "Audio Recorder" },
    { id: "logDebug", icon: FileText, label: "Chat Log" },
    { id: "funStuff", icon: Sparkles, label: "Fun Stuff (Coming Soon)" },
    { id: "detail", icon: Database, label: "Robot Detail" },
  ];

  return (
    <aside className="w-80 bg-white p-6 flex flex-col rounded-l-2xl border-r border-gray-200 h-full">
      <div className="mb-10">
        <img
          src="/michi_logo.png"
          alt="Robot Icon"
          className="mx-auto mb-4"
        />
        <div class="h-1 w-auto bg-green-300"></div>
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