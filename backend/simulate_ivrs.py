import requests

URL = "http://127.0.0.1:8000/api/v1/ivrs/webhook"

ivrs_payload = {
    "caller_phone": "+919876543210",
    "victim_id": "V-9901",
    "audio_transcript": "I need urgent help. Someone is outside my house and threatening me."
}

try:
    response = requests.post(URL, json=ivrs_payload)
    if response.status_code == 200:
        print("IVRS Webhook Successfully Triggered!")
        print("Response from server:", response.json())
    else:
        print(f"Failed with status code {response.status_code}:", response.text)
except Exception as e:
    print("Error connecting to FastAPI backend server:", str(e))
