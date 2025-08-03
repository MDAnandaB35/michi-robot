import React, { useState, useRef, useEffect } from "react";
import mqtt from "mqtt";

const MQTT_BROKER = import.meta.env.VITE_MQTT_BROKER || "broker.emqx.io";
const MQTT_WS_PORT = import.meta.env.VITE_MQTT_WS_PORT || "8084"; // WSS port!
const MQTT_PROTOCOL = import.meta.env.VITE_MQTT_PROTOCOL || "wss"; // "wss" for secure connections
const MQTT_TOPIC = import.meta.env.VITE_MQTT_TOPIC || "testtopic/mwtt";

const MQTT_BROKER_URL = `${MQTT_PROTOCOL}://${MQTT_BROKER}:${MQTT_WS_PORT}/mqtt`;

function FunctionTestView() {
  const [logs, setLogs] = useState([]);
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

  const buttons = ["Hands", "Speaker", "Head", "Microphone"];

  return (
    <main className="flex-1 p-8">
      <h1 className="text-3xl font-bold text-center text-black">
        Function Test
      </h1>
      <p className="text-gray-500 mb-6 text-center">
        This page should test Michi's functionalities. Feel free to choose any
        of the actions below to test the components.
      </p>

      <div
        ref={logRef}
        className="h-48 mb-6 overflow-y-auto bg-white border-2 border-purple-300 rounded-lg p-4"
      >
        {logs.map((log, i) => (
          <div key={i} className="font-mono text-sm text-gray-700 mb-1">
            <span className="text-green-500 mr-1">&gt;</span>
            {log}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        {buttons.map((b) => (
          <button
            key={b}
            onClick={() => publish(b)}
            className="bg-green-100 hover:bg-green-200 text-green-800 font-semibold py-4 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-400"
          >
            {b}
          </button>
        ))}
      </div>
    </main>
  );
}
export default FunctionTestView;
