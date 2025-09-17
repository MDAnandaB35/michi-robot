import React, { useState, useMemo, useEffect, useRef } from "react";
import { fetchChatLogs } from "../API/ChatLogsApi";

// --- Mock API & Data ---
const mockChatLogs = [
  {
    id: 1,
    input: "Apa itu PT Bintang Toedjoe?",
    response:
      "PT Bintang Toedjoe adalah perusahaan farmasi ternama di Indonesia yang dikenal dengan produk-produk kesehatan seperti Extra Joss.",
    time: "2025-07-15T09:00:00Z",
  },
  {
    id: 2,
    input: "Kapan PT Bintang Toedjoe didirikan?",
    response: "PT Bintang Toedjoe didirikan pada tahun 1946.",
    time: "2025-07-17T09:01:00Z",
  },
  {
    id: 3,
    input: "Siapa pendiri PT Bintang Toedjoe?",
    response: "Pendiri PT Bintang Toedjoe adalah Tjie Kwik Hwie.",
    time: "2025-07-18T09:02:00Z",
  },
  {
    id: 4,
    input: "Apa produk terkenal dari PT Bintang Toedjoe?",
    response:
      "Produk terkenalnya adalah Extra Joss, Puyer Bintang Toedjoe, dan Komix.",
    time: "2025-07-18T09:03:00Z",
  },
  {
    id: 5,
    input: "Apakah PT Bintang Toedjoe bagian dari Kalbe Group?",
    response:
      "Ya, PT Bintang Toedjoe merupakan anak perusahaan dari Kalbe Group.",
    time: "2025-07-19T09:04:00Z",
  },
  {
    id: 6,
    input: "Dimana kantor pusat PT Bintang Toedjoe?",
    response: "Kantor pusatnya berada di Jakarta, Indonesia.",
    time: "2025-07-19T09:05:00Z",
  },
  {
    id: 7,
    input: "Bagaimana cara melamar kerja di PT Bintang Toedjoe?",
    response:
      "Anda dapat melamar melalui website resmi PT Bintang Toedjoe di bagian karir.",
    time: "2025-07-20T09:06:00Z",
  },
  {
    id: 8,
    input: "Apakah PT Bintang Toedjoe memiliki program CSR?",
    response:
      "Ya, PT Bintang Toedjoe aktif dalam berbagai program Corporate Social Responsibility di bidang kesehatan dan pendidikan.",
    time: "2025-07-20T09:07:00Z",
  },
];

// --- Helper Functions ---

/**
 * Formats an ISO date string into a readable time format (e.g., 10:30 AM).
 * @param {string} dateString - The ISO date string.
 * @returns {string} - The formatted time.
 */
const formatTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

/**
 * Formats an ISO date string into a readable date format (e.g., June 28, 2024).
 * @param {string} dateString - The ISO date string.
 * @returns {string} - The formatted date.
 */
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString([], {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
};

// --- React Components ---

/**
 * Displays a single chat message bubble.
 */
const ChatMessage = ({ text, time, isInput }) => (
  <div className={`flex ${isInput ? "justify-end" : "justify-start"} mb-4`}>
    <div
      className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-3 rounded-2xl shadow-md ${
        isInput
          ? "bg-blue-500 text-white rounded-br-none"
          : "bg-gray-100 text-gray-800 rounded-bl-none"
      }`}
    >
      <p className="text-sm">{text}</p>
      <p
        className={`text-xs mt-1 ${
          isInput ? "text-blue-200" : "text-gray-500"
        } text-right`}
      >
        {formatTime(time)}
      </p>
    </div>
  </div>
);

/**
 * Renders a date separator in the chat log.
 */
const DateSeparator = ({ date }) => (
  <div className="flex items-center justify-center my-6">
    <div className="px-3 py-1 text-sm text-gray-500 bg-gray-100 rounded-full">
      {formatDate(date)}
    </div>
  </div>
);

/**
 * A loading spinner component.
 */
const Loader = () => (
  <div className="flex flex-col items-center justify-center h-full text-gray-500">
    <svg
      className="animate-spin h-10 w-10 text-blue-500"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      ></circle>
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      ></path>
    </svg>
    <p className="mt-4 text-lg">Loading Chat History...</p>
  </div>
);

/**
 * iOS-style Date Picker Component
 */
const IOSDatePicker = ({ isOpen, onClose, onSelect, availableDates }) => {
  const today = new Date();
  const [selectedYear, setSelectedYear] = useState(today.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(today.getMonth());
  const [selectedDay, setSelectedDay] = useState(today.getDate());

  const dateMap = useMemo(() => {
    const map = new Map();
    availableDates.forEach((isoDate) => {
      const date = new Date(isoDate);
      const year = date.getFullYear();
      const month = date.getMonth();
      const day = date.getDate();
      if (!map.has(year)) map.set(year, new Map());
      if (!map.get(year).has(month)) map.get(year).set(month, new Set());
      map.get(year).get(month).add(day);
    });
    return map;
  }, [availableDates]);

  const years = useMemo(
    () => Array.from(dateMap.keys()).sort((a, b) => a - b),
    [dateMap]
  );
  const months = useMemo(() => {
    if (!dateMap.has(selectedYear)) return [];
    return Array.from(dateMap.get(selectedYear).keys()).sort((a, b) => a - b);
  }, [dateMap, selectedYear]);

  const days = useMemo(() => {
    if (
      !dateMap.has(selectedYear) ||
      !dateMap.get(selectedYear).has(selectedMonth)
    )
      return [];
    return Array.from(dateMap.get(selectedYear).get(selectedMonth)).sort(
      (a, b) => a - b
    );
  }, [dateMap, selectedYear, selectedMonth]);

  useEffect(() => {
    if (isOpen) {
      const lastAvailableDate = new Date(availableDates[0] || today);
      setSelectedYear(lastAvailableDate.getFullYear());
      setSelectedMonth(lastAvailableDate.getMonth());
      setSelectedDay(lastAvailableDate.getDate());
    }
  }, [isOpen, availableDates]);

  useEffect(() => {
    if (!months.includes(selectedMonth)) {
      setSelectedMonth(months[0]);
    }
  }, [selectedYear, months]);

  useEffect(() => {
    if (!days.includes(selectedDay)) {
      setSelectedDay(days[0]);
    }
  }, [selectedMonth, days]);

  const handleSelect = () => {
    if (days.length > 0) {
      const selected = new Date(selectedYear, selectedMonth, selectedDay);
      onSelect(selected.toISOString());
    }
    onClose();
  };

  const PickerColumn = ({ values, selectedValue, onSelect, unit }) => {
    const monthNames = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    return (
      <div className="w-1/3 h-48 overflow-y-scroll snap-y snap-mandatory custom-scrollbar">
        <div className="h-full">
          {values.map((value) => {
            const isSelected = selectedValue === value;
            return (
              <div
                key={value}
                onClick={() => onSelect(value)}
                className={`flex items-center justify-center m-2 text-lg snap-center p-0 cursor-pointer 
                                  transition-all duration-300 ease-in-out
                                  ${
                                    isSelected
                                      ? "text-blue-500 font-semibold bg-gray-100 rounded-xl scale-105"
                                      : "text-gray-500 scale-100"
                                  }`}
              >
                {unit === "month" ? monthNames[value] : value}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-opacity-30 backdrop-blur-sm flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-sm rounded-2xl shadow-lg p-4 mx-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center pb-3 border-b">
          <button onClick={onClose} className="text-blue-500">
            Cancel
          </button>
          <h3 className="font-semibold text-gray-800">Select Date</h3>
          <button onClick={handleSelect} className="text-blue-500 font-bold">
            Done
          </button>
        </div>
        <div className="flex justify-center items-center py-4 relative">
          <PickerColumn
            values={months}
            selectedValue={selectedMonth}
            onSelect={setSelectedMonth}
            unit="month"
          />
          <PickerColumn
            values={days}
            selectedValue={selectedDay}
            onSelect={setSelectedDay}
            unit="day"
          />
          <PickerColumn
            values={years}
            selectedValue={selectedYear}
            onSelect={setSelectedYear}
            unit="year"
          />
        </div>
      </div>
    </div>
  );
};

/**
 * Main Application Component
 */
export default function App({ robot }) {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filterDate, setFilterDate] = useState("all");
  const [isPickerOpen, setIsPickerOpen] = useState(false);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when logs change
  useEffect(() => {
    if (chatContainerRef.current && logs.length > 0) {
      const scrollToBottom = () => {
        chatContainerRef.current.scrollTop =
          chatContainerRef.current.scrollHeight;
      };

      // Use setTimeout to ensure DOM is updated before scrolling
      setTimeout(scrollToBottom, 100);
    }
  }, [logs, filterDate]);

  useEffect(() => {
    fetchChatLogs(robot?.robotId)
      .then((data) => {
        setLogs(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error("Fetch Error:", err);
        setError("Failed to load chat logs. Displaying sample data.");
        setLogs(mockChatLogs); // fallback
        setIsLoading(false);
      });
  }, [robot?.robotId]);

  const filteredLogs = useMemo(() => {
    if (filterDate === "all") {
      return logs;
    }
    const selectedDate = new Date(filterDate);
    return logs.filter((log) => {
      const logDate = new Date(log.time);
      return logDate.toDateString() === selectedDate.toDateString();
    });
  }, [logs, filterDate]);

  const availableDates = useMemo(() => {
    const dates = new Set(logs.map((log) => new Date(log.time).toDateString()));
    return Array.from(dates)
      .map((dateStr) => new Date(dateStr).toISOString())
      .sort((a, b) => new Date(b) - new Date(a));
  }, [logs]);

  const groupedLogs = useMemo(() => {
    return filteredLogs.reduce((acc, log) => {
      const date = new Date(log.time).toDateString();
      if (!acc[date]) {
        acc[date] = [];
      }
      // Create separate entries for input and response to treat them as distinct messages
      acc[date].push({ ...log, type: "input", msgId: `${log.id}-input` });
      acc[date].push({ ...log, type: "response", msgId: `${log.id}-response` });
      return acc;
    }, {});
  }, [filteredLogs]);

  const handleDateSelect = (dateISO) => {
    setFilterDate(dateISO);
    setIsPickerOpen(false);
  };

  return (
    <div className="font-sans flex justify-center h-full">
      <div className="w-full mx-4 h-full flex flex-col">
        <div className="p-3 border-b flex flex-wrap gap-2 items-center justify-between bg-gray-200 rounded-2xl">
          <button
            onClick={() => setFilterDate("all")}
            className={`px-4 py-2 text-sm rounded-full transition-all ${
              filterDate === "all"
                ? "bg-blue-500 text-white shadow"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All
          </button>
          <h2 className="hidden md:block text-xl font-bold text-gray-800 mb-2 text-center">
            Michi Chatlogs{" "}
            {error ? (
              <p className="text-sm text-red-500">{error}</p>
            ) : (
              <p className="text-sm text-gray-600">
                Browse conversation history.
              </p>
            )}
          </h2>
          <button
            onClick={() => setIsPickerOpen(true)}
            disabled={availableDates.length === 0}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-full transition-all 
              ${
                filterDate !== "all"
                  ? "bg-blue-500 text-white shadow"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }
              disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="16" y1="2" x2="16" y2="6"></line>
              <line x1="8" y1="2" x2="8" y2="6"></line>
              <line x1="3" y1="10" x2="21" y2="10"></line>
            </svg>
            {filterDate === "all"
              ? "Select Date"
              : new Date(filterDate).toLocaleDateString([], {
                  month: "short",
                  day: "numeric",
                })}
          </button>
          <h2 className="block md:hidden text-xl font-bold text-gray-800 mb-2 text-center">
            Michi Chatlogs{" "}
            {error ? (
              <p className="text-sm text-red-500">{error}</p>
            ) : (
              <p className="text-sm text-gray-600">
                Browse conversation history.
              </p>
            )}
          </h2>
        </div>

        <div ref={chatContainerRef} className="flex-1 p-4 overflow-y-auto">
          {isLoading ? (
            <Loader />
          ) : Object.keys(groupedLogs).length > 0 ? (
            Object.keys(groupedLogs)
              .sort((a, b) => new Date(a) - new Date(b))
              .map((date) => (
                <React.Fragment key={date}>
                  <DateSeparator date={date} />
                  {groupedLogs[date]
                    .sort((a, b) => new Date(a.time) - new Date(b.time))
                    .map((msg) =>
                      msg.type === "input" ? (
                        <ChatMessage
                          key={msg.msgId}
                          text={msg.input}
                          time={msg.time}
                          isInput={true}
                        />
                      ) : (
                        <ChatMessage
                          key={msg.msgId}
                          text={msg.response}
                          time={msg.time}
                          isInput={false}
                        />
                      )
                    )}
                </React.Fragment>
              ))
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-12 w-12 mb-2 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 5.523-4.477 10-10 10S1 17.523 1 12 5.477 2 11 2s10 4.477 10 10z"
                />
              </svg>
              <p className="text-lg font-medium">No chat logs found.</p>
              <p className="text-sm">Try selecting another date or 'All'.</p>
            </div>
          )}
        </div>
        <IOSDatePicker
          isOpen={isPickerOpen}
          onClose={() => setIsPickerOpen(false)}
          onSelect={handleDateSelect}
          availableDates={availableDates}
        />
      </div>
    </div>
  );
}
