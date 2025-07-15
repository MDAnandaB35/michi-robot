import sounddevice as sd
from scipy.io.wavfile import write
import requests
import tempfile
import os

# Configuration
SERVER_URL = "http://localhost:5000/process_input"  # or "/detect_wakeword"
DURATION_SECONDS = 5  # length of recording
SAMPLE_RATE = 16000  # Whisper prefers 16000 Hz

def record_audio(duration, sample_rate):
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    return audio

def save_temp_wav(audio_data, sample_rate):
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="record_")
    os.close(fd)
    write(path, sample_rate, audio_data)
    return path

def send_audio_to_server(filepath, url):
    with open(filepath, 'rb') as f:
        audio_bytes = f.read()
        headers = {'Content-Type': 'application/octet-stream'}
        print(f"Sending {len(audio_bytes)} bytes to {url}")
        response = requests.post(url, data=audio_bytes, headers=headers)
        print("Response status:", response.status_code)
        try:
            if 'audio/mpeg' in response.headers.get('Content-Type', ''):
                print("Received audio response (TTS)")
                with open("response.mp3", "wb") as f:
                    f.write(response.content)
                print("Saved TTS to response.mp3")
            else:
                print("Response JSON:", response.json())
        except Exception as e:
            print("Failed to parse response:", e)

def main():
    audio_data = record_audio(DURATION_SECONDS, SAMPLE_RATE)
    wav_path = save_temp_wav(audio_data, SAMPLE_RATE)
    try:
        send_audio_to_server(wav_path, SERVER_URL)
    finally:
        os.remove(wav_path)

if __name__ == "__main__":
    main()
