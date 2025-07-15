import React, { useState, useRef, useEffect, useCallback } from "react";

// Configuration
const SERVER_ORIGIN = "http://18.141.160.29:5000";      // Flask base URL
const PROCESS_URL   = `${SERVER_ORIGIN}/process_input`;
const SAMPLE_RATE   = 16_000;

// --- SVG Icons for the recorder button ---
const RecordIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <circle cx="12" cy="12" r="10" />
  </svg>
);

const StopIcon = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </svg>
);

// --- Main Audio Recorder Component ---
export default function AudioRecorderPlayer() {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [processedAudios, setProcessedAudios] = useState([]);
  const [statusMessage, setStatusMessage] = useState("Click the button to start recording.");

  // --- Refs for various audio and drawing components ---
  const mediaStreamRef = useRef(null);
  const workletNodeRef = useRef(null);
  const framesRef = useRef([]);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameIdRef = useRef(null);
  const timerIntervalRef = useRef(null);

  /**
   * Helper function to build a WAV file blob in memory from raw PCM samples.
   * This is necessary to create a standard audio file format that can be sent
   * to a server or played back in a browser.
   */
  const buildWavBlob = (samples, sr) => {
    const numFrames = samples.length;
    const bytesPerSample = 2; // Int16
    const blockAlign = bytesPerSample * 1; // mono
    const byteRate = sr * blockAlign;
    const dataSize = numFrames * bytesPerSample;
    const buffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(buffer);
    const writeStr = (off, str) => [...str].forEach((c, i) => view.setUint8(off + i, c.charCodeAt(0)));

    writeStr(0, "RIFF");
    view.setUint32(4, 36 + dataSize, true);
    writeStr(8, "WAVE");
    writeStr(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sr, true);
    view.setUint32(28, byteRate, true);
    view.setUint16(32, blockAlign, true);
    view.setUint16(34, bytesPerSample * 8, true);
    writeStr(36, "data");
    view.setUint32(40, dataSize, true);

    let offset = 44;
    samples.forEach(s => { view.setInt16(offset, s, true); offset += 2; });
    return new Blob([view], { type: "audio/wav" });
  };

  /**
   * Draws the audio waveform on the canvas.
   * This function is called recursively via requestAnimationFrame during recording.
   */
  const drawVisualizer = useCallback(() => {
    if (!analyserRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext("2d");
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    analyserRef.current.getByteTimeDomainData(dataArray);

    canvasCtx.fillStyle = "rgb(229, 231, 235)"; 
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = "rgb(239 68 68)"; // text-red-500
    canvasCtx.beginPath();

    const sliceWidth = (canvas.width * 1.0) / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * canvas.height) / 2;
      if (i === 0) {
        canvasCtx.moveTo(x, y);
      } else {
        canvasCtx.lineTo(x, y);
      }
      x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();

    animationFrameIdRef.current = requestAnimationFrame(drawVisualizer);
  }, []);

  /**
   * Starts the recording process.
   * 1. Gets microphone access.
   * 2. Sets up AudioContext, AudioWorklet, and AnalyserNode.
   * 3. Connects the audio graph.
   * 4. Starts the visualizer and recording timer.
   */
  const startRecording = async () => {
    setStatusMessage("Initializing...");
    framesRef.current = [];
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioCtxRef.current = audioCtx;

      // The AudioWorklet processor captures raw PCM data.
      await audioCtx.audioWorklet.addModule(URL.createObjectURL(new Blob([`
        class PCMRecorder extends AudioWorkletProcessor {
          process(inputs) {
            const channel = inputs[0][0];
            if (channel) {
              const out = new Int16Array(channel.length);
              for (let i = 0; i < channel.length; i++) {
                const s = Math.max(-1, Math.min(1, channel[i]));
                out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
              }
              this.port.postMessage(out);
            }
            return true;
          }
        }
        registerProcessor("pcm-recorder", PCMRecorder);
      `], { type: "text/javascript" })));

      const source = audioCtx.createMediaStreamSource(stream);
      const node = new AudioWorkletNode(audioCtx, "pcm-recorder");
      node.port.onmessage = e => framesRef.current.push(...e.data);
      workletNodeRef.current = node;

      // For visualization
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      analyserRef.current = analyser;

      source.connect(analyser).connect(node).connect(audioCtx.destination);

      setIsRecording(true);
      setStatusMessage("Recording...");
      
      // Start timer
      setRecordingTime(0);
      timerIntervalRef.current = setInterval(() => {
        setRecordingTime(prevTime => prevTime + 1);
      }, 1000);

      // Start visualizer
      animationFrameIdRef.current = requestAnimationFrame(drawVisualizer);

    } catch (err) {
      console.error("Microphone error:", err);
      setStatusMessage("Error: Could not access microphone.");
    }
  };

  /**
   * Stops the recording process.
   * 1. Cleans up audio resources and stops tracks.
   * 2. Stops the visualizer and timer.
   * 3. Builds a WAV blob and sends it to the backend.
   * 4. Handles the response and adds the new audio to the list.
   */
  const stopRecording = async () => {
    setIsRecording(false);
    setStatusMessage("Processing...");

    // Stop timer and visualizer
    clearInterval(timerIntervalRef.current);
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }

    // Clear canvas
    if (canvasRef.current) {
        const canvas = canvasRef.current;
        const canvasCtx = canvas.getContext("2d");
        canvasCtx.fillStyle = "rgb(229, 231, 235)";
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
    }

    try { workletNodeRef.current?.disconnect(); } catch {}
    mediaStreamRef.current?.getTracks().forEach(t => t.stop());
    if (audioCtxRef.current?.state !== 'closed') {
        await audioCtxRef.current?.close();
    }

    const wavBlob = buildWavBlob(Int16Array.from(framesRef.current), SAMPLE_RATE);

    try {
      const res = await fetch(PROCESS_URL, {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/octet-stream" },
        body: wavBlob
      });

      if (!res.ok) throw new Error(`POST failed: ${res.status}`);

      const ct = res.headers.get("Content-Type") || "";
      let audioURL = "";

      if (ct.startsWith("response_audio/")) {
        const blob = await res.blob();
        audioURL = URL.createObjectURL(blob);
      } else {
        const json = await res.json();
        if (json.audio_url) {
          audioURL = new URL(json.audio_url, SERVER_ORIGIN).href;
        } else {
          throw new Error("Response JSON did not contain audio_url.");
        }
      }
      
      const newAudio = {
          url: audioURL,
          name: `Recording ${new Date().toLocaleTimeString()}`
      };
      setProcessedAudios(prev => [newAudio, ...prev]);
      setStatusMessage("Recording complete. Click to record again.");

    } catch (err) {
      console.error("Send/receive error:", err);
      setStatusMessage(`Error: ${err.message}`);
    }
  };

  // Cleanup effect to stop microphone access if the component unmounts.
  useEffect(() => () => {
    mediaStreamRef.current?.getTracks().forEach(t => t.stop());
    clearInterval(timerIntervalRef.current);
    if (animationFrameIdRef.current) {
      cancelAnimationFrame(animationFrameIdRef.current);
    }
  }, []);

  // --- UI Render ---
  return (
    <div className="flex flex-col items-center  min-h-screen text-black font-sans p-4">
      <div className="w-full bg-white rounded-3xl qp-6 space-y-6">
        
        {/* Header and Status */}
        <div className="text-center">
          <h1 className="text-2xl font-bold">Audio Recorder</h1>
          <p className="text-zinc-400 text-sm mt-1">{statusMessage}</p>
        </div>

        {/* Visualizer and Timer */}
        <div className="relative h-54 w-full bg-gray-200 rounded-xl overflow-hidden">
          <canvas ref={canvasRef} className="w-full h-full" />
          {isRecording && (
            <div className="absolute top-2 right-3 bg-red-500 text-white text-xs font-mono px-2 py-1 rounded">
              {String(Math.floor(recordingTime / 60)).padStart(2, '0')}:
              {String(recordingTime % 60).padStart(2, '0')}
            </div>
          )}
        </div>

        {/* Record Button */}
        <div className="flex justify-center">
          <button
            onClick={!isRecording ? startRecording : stopRecording}
            className="w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ease-in-out
                       bg-red-500 hover:bg-red-600 focus:outline-none focus:ring-4 focus:ring-red-500/50
                       disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={isRecording && recordingTime < 1} // Disable stop button for 1s to prevent accidental double-clicks
          >
            {isRecording ? (
              <StopIcon className="w-8 h-8 text-white" />
            ) : (
              <RecordIcon className="w-10 h-10 text-white" />
            )}
          </button>
        </div>

        {/* Audio List */}
        {processedAudios.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-zinc-700/50">
            <h2 className="font-semibold text-lg">Your Recordings</h2>
            <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
              {processedAudios.map((audio, index) => (
                <div key={index} className="bg-gray-200 p-3 rounded-lg flex items-center gap-4">
                  <div className="flex-grow">
                    <p className="font-medium text-sm">{audio.name}</p>
                    <audio src={audio.url} controls autoPlay={index === 0} className="w-full h-10 mt-1" />
                  </div>
                  <a
                    href={audio.url}
                    download={`${audio.name.replace(/\s/g, '_')}.wav`}
                    className="text-zinc-400 hover:text-white transition-colors"
                    title="Download"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <footer className="text-center mt-6 text-zinc-500 text-xs">
        <p>Click the button to start/stop talking to Michi. Connects to {SERVER_ORIGIN}.</p>
      </footer>
    </div>
  );
}
