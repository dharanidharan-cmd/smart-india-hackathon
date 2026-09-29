import wave
import struct
import requests

# 1. Generate a valid 1-second silent WAV file locally
wav_file = "sample.wav"
with wave.open(wav_file, "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    for _ in range(44100):
        f.writeframes(struct.pack("<h", 0))

# 2. Test posting the WAV file to main.py endpoint
url = "http://127.0.0.1:8000/api/v1/ivrs/voice-upload"
data = {"caller_phone": "+919876543210", "victim_id": "V-505"}
files = {"audio_file": ("sample.wav", open("sample.wav", "rb"), "audio/wav")}

try:
    response = requests.post(url, data=data, files=files)
    print("Server Response:", response.json())
except Exception as e:
    print("Error connecting to server:", str(e))
