import React, { useState, useRef, useEffect } from "react";
import mqtt from "mqtt";

const MQTT_BROKER = import.meta.env.VITE_MQTT_BROKER || "broker.emqx.io";
const MQTT_WS_PORT = import.meta.env.VITE_MQTT_WS_PORT || "8084"; // WSS port!
const MQTT_PROTOCOL = import.meta.env.VITE_MQTT_PROTOCOL || "wss"; // "wss" for secure connections
const MQTT_TOPIC = import.meta.env.VITE_MQTT_TOPIC || "testtopic/mwtt";

const MQTT_BROKER_URL = `${MQTT_PROTOCOL}://${MQTT_BROKER}:${MQTT_WS_PORT}/mqtt`;

function FunctionTestView() {
  const [logs, setLogs] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [camOn, setCamOn] = useState(true);
  const logRef = useRef(null);
  const clientRef = useRef(null);

  useEffect(() => {
    const client = mqtt.connect(MQTT_BROKER_URL);

    client.on("connect", () => {
      setLogs((l) => [...l, `Connected → ${MQTT_BROKER_URL}`]);

      client.subscribe(MQTT_TOPIC, (err) => {
        if (err) {
          setLogs((l) => [...l, `Subscribe error: ${err.message}`]);
        } else {
          setLogs((l) => [...l, `Subscribed to ${MQTT_TOPIC}`]);
          setLogs((l) => [
            ...l,
            `Ready to publish commands! Select any actions from the buttons below.`,
          ]);
        }
      });
    });

    client.on("message", (topic, msg) => {
      setLogs((l) => [...l, `${topic}: ${msg.toString()}`]);
    });

    client.on("error", (err) =>
      setLogs((l) => [...l, `MQTT error: ${err.message}`])
    );

    clientRef.current = client;
    return () => client.end(); // clean-up on unmount
  }, []);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const publish = (action) => {
    const payload = JSON.stringify({ command: `test_${action.toLowerCase()}` });
    setLogs((l) => [...l, `Publishing → ${MQTT_TOPIC}: ${payload}`]);

    if (clientRef.current && clientRef.current.connected) {
      clientRef.current.publish(MQTT_TOPIC, payload, (err) => {
        setLogs((l) =>
          err
            ? [...l, `Publish error: ${err.message}`]
            : [...l, "Publish success"]
        );
      });
    } else {
      setLogs((l) => [...l, "Client not connected"]);
    }
  };

  const publishStop = () => {
    const payload = JSON.stringify({ command: "test_stop" });
    setLogs((l) => [...l, `Publishing → ${MQTT_TOPIC}: ${payload}`]);
    if (clientRef.current && clientRef.current.connected) {
      clientRef.current.publish(MQTT_TOPIC, payload, (err) => {
        setLogs((l) =>
          err
            ? [...l, `Publish error: ${err.message}`]
            : [...l, "Publish success"]
        );
      });
    } else {
      setLogs((l) => [...l, "Client not connected"]);
    }
  };

  const handleDropdownSelect = (state) => {
    let payload;
    if (state === "SLEEP") {
      payload = JSON.stringify({ response: "sleep" });
    } else if (state === "IDLE") {
      payload = JSON.stringify({ command: "idle" });
    } else {
      payload = JSON.stringify({});
    }
    setLogs((l) => [...l, `Publishing → ${MQTT_TOPIC}: ${payload}`]);
    if (clientRef.current && clientRef.current.connected) {
      clientRef.current.publish(MQTT_TOPIC, payload, (err) => {
        setLogs((l) =>
          err
            ? [...l, `Publish error: ${err.message}`]
            : [...l, "Publish success"]
        );
      });
    } else {
      setLogs((l) => [...l, "Client not connected"]);
    }
    setDropdownOpen(false);
  };

  const buttons = ["Hands", "Neck", "Eyes", "Speaker"];

  return (
    <main className="flex-1 p-8 flex flex-col items-center justify-between h-full">
      <div>
        <h1 className="text-3xl font-bold text-center text-black mb-6 md:mb-3">
          Function Test
        </h1>
        <p className="text-gray-500 mb-6 text-center md:block hidden">
          This page allows you to test Michi's individual components or run comprehensive tests.
          Choose any component below to test specific functionality, or use "Test All Components"
          for a complete system test.
        </p>

        {/* Cam Capture Section */}
        <div className="w-full flex flex-col md:flex-row gap-2 justify-center items-center">
          <div className="w-full md:w-1/3 h-64 mb-6 flex justify-center items-center relative">
            {camOn ? (
              <img
                src="http://172.20.10.12:5000/video_feed"
                alt="Camera Feed"
                className="rounded-lg border border-gray-300 w-full h-full object-contain"
                style={{ background: '#222' }}
              />
            ) : (
              <div className="rounded-lg border border-gray-300 w-full h-full flex flex-col items-center justify-center bg-gray-100" style={{ background: '#222' }}>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 text-gray-400 mb-2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-3A2.25 2.25 0 008.25 5.25V9m-3.5 0h14a2.25 2.25 0 012.25 2.25v5.25A2.25 2.25 0 0118.75 18.75H5.25A2.25 2.25 0 013 16.5v-5.25A2.25 2.25 0 015.25 9zm3.5 0V5.25m0 0A2.25 2.25 0 0110.5 3h3a2.25 2.25 0 012.25 2.25V9" />
                  <line x1="4" y1="20" x2="20" y2="4" stroke="currentColor" strokeWidth="2" />
                </svg>
                <span className="text-gray-500 font-semibold text-lg">Camera Closed</span>
              </div>
            )}
            <div className="absolute top-2 right-2 flex gap-2 z-10">
              <button
                onClick={() => setCamOn(true)}
                className={`px-3 py-1 rounded-lg font-semibold border text-xs shadow ${camOn ? 'bg-green-200 text-green-800 border-green-400' : 'bg-white text-black border-gray-300'} transition-colors duration-200`}
              >
                On
              </button>
              <button
                onClick={() => setCamOn(false)}
                className={`px-3 py-1 rounded-lg font-semibold border text-xs shadow ${!camOn ? 'bg-red-200 text-red-800 border-red-400' : 'bg-white text-black border-gray-300'} transition-colors duration-200`}
              >
                Off
              </button>
            </div>
          </div>

          <div
            ref={logRef}
            className="w-full md:w-2/3 h-64 mb-6 overflow-y-auto bg-white border-2 border-purple-300 rounded-lg p-4 flex flex-col justify-start"
          >
            {logs.map((log, i) => (
              <div key={i} className="font-mono text-sm text-gray-700 mb-1">
                <span className="text-green-500 mr-1">&gt;</span>
                {log}
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mb-4">
          {buttons.map((b) => (
            <button
              key={b}
              onClick={() => publish(b)}
              className="bg-green-100 hover:bg-green-200 text-green-800 ring-green-400 font-semibold py-4 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2"
            >
              {`Test ${b}`}
            </button>
          ))}
        </div>
        <button
          onClick={() => publish("All")}
          className="w-full bg-blue-100 hover:bg-blue-200 text-blue-800 ring-blue-400 font-semibold py-4 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 mb-4"
        >
          Test All Components
        </button>
      </div>
      <div className="w-full flex md:flex-row flex-col items-center justify-center gap-4">
        <button
          onClick={publishStop}
          className="w-full md:w-3/4 bg-red-100 hover:bg-red-200 text-red-800 ring-red-400 font-semibold py-4 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2"
        >
          Stop
        </button>
        <div className="relative w-full md:w-1/4">
          <button
            type="button"
            onClick={() => setDropdownOpen((open) => !open)}
            className="inline-flex w-full justify-center gap-x-1.5 rounded-lg bg-white border shadow-md border-gray-100 text-black font-semibold py-4 px-6 transition-colors duration-200 focus:outline-none"
          >
            State
            <svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" className="-mr-1 h-5 w-5 text-gray-400">
              <path d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z" clipRule="evenodd" fillRule="evenodd" />
            </svg>
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 bottom-full mb-2 w-full origin-bottom-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
              <div className="py-1">
                <button
                  onClick={() => handleDropdownSelect("SLEEP")}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  SLEEP
                </button>
                <button
                  onClick={() => handleDropdownSelect("IDLE")}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  IDLE
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
export default FunctionTestView;
