import pyttsx3
import requests

engine = pyttsx3.init()
spoken_text = "I am in urgent danger, please send emergency help immediately!"
wav_filename = "spoken_danger.wav"

engine.save_to_file(spoken_text, wav_filename)
engine.runAndWait()

print(f"Generated audio file with text: \"{spoken_text}\"")

url = "http://127.0.0.1:8000/api/v1/ivrs/voice-upload"
data = {"caller_phone": "+919876543210", "victim_id": "V-505"}
files = {"audio_file": (wav_filename, open(wav_filename, "rb"), "audio/wav")}

try:
    response = requests.post(url, data=data, files=files)
    print("Response:", response.json())
except Exception as e:
    print("Error:", str(e))
