import os
import speech_recognition as sr
from pydub import AudioSegment
from fastapi import FastAPI, Depends, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import database

app = FastAPI(title="Victim Distress Monitoring API")

# Enable CORS for local HTML access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize Speech Recognizer
recognizer = sr.Recognizer()

# Pydantic Schemas
class CheckInRequest(BaseModel):
    victim_id: str
    channel: str
    message_text: str

class IVRSWebhookRequest(BaseModel):
    caller_phone: str
    victim_id: str
    audio_transcript: str

# --- ENDPOINTS ---

@app.post("/api/v1/checkin")
def create_checkin(data: CheckInRequest, db: Session = Depends(get_db)):
    score = 15.0
    risk = "Green"
    text_lower = data.message_text.lower()
    
    if any(k in text_lower for k in ["help", "threat", "danger", "attack", "emergency"]):
        score = 90.0
        risk = "Red"

    new_entry = database.CheckInModel(
        victim_id=data.victim_id,
        channel=data.channel,
        message_text=data.message_text,
        distress_score=score,
        risk_level=risk
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

@app.post("/api/v1/ivrs/webhook")
def ivrs_call_webhook(data: IVRSWebhookRequest, db: Session = Depends(get_db)):
    score = 15.0
    risk = "Green"
    text_lower = data.audio_transcript.lower()
    
    if any(k in text_lower for k in ["help", "danger", "threat", "attack", "emergency"]):
        score = 90.0
        risk = "Red"

    new_entry = database.CheckInModel(
        victim_id=data.victim_id,
        channel="ivrs_phone_call",
        message_text=data.audio_transcript,
        distress_score=score,
        risk_level=risk
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {
        "status": "IVRS Log Processed",
        "log_id": new_entry.id,
        "risk_level": new_entry.risk_level
    }

@app.post("/api/v1/ivrs/voice-upload")
async def process_voice_call_file(
    caller_phone: str = Form("Unknown"),
    victim_id: str = Form("V-UNKNOWN"),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    temp_filename = f"temp_{audio_file.filename}"
    wav_filename = f"temp_converted_{audio_file.filename}.wav"

    with open(temp_filename, "wb") as f:
        f.write(await audio_file.read())

    transcript = ""
    try:
        # Convert audio to WAV format if required by SpeechRecognition
        if not temp_filename.endswith(".wav"):
            sound = AudioSegment.from_file(temp_filename)
            sound.export(wav_filename, format="wav")
            target_file = wav_filename
        else:
            target_file = temp_filename

        with sr.AudioFile(target_file) as source:
            audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data)
    except Exception:
        transcript = "[Audio transcription failed or silence detected]"
    finally:
        # Cleanup temporary files
        for path in [temp_filename, wav_filename]:
            if os.path.exists(path):
                os.remove(path)

    # Risk analysis logic
    score = 15.0
    risk = "Green"
    text_lower = transcript.lower()

    if any(k in text_lower for k in ["help", "danger", "threat", "attack", "emergency"]):
        score = 95.0
        risk = "Red"

    # Store entry in SQLite
    new_entry = database.CheckInModel(
        victim_id=victim_id,
        channel=f"ivrs_voice_call ({caller_phone})",
        message_text=transcript,
        distress_score=score,
        risk_level=risk
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return {
        "status": "Voice Call Analyzed",
        "transcript": transcript,
        "risk_level": risk,
        "log_id": new_entry.id
    }

@app.get("/api/v1/admin/checkins")
def get_all_checkins(db: Session = Depends(get_db)):
    return db.query(database.CheckInModel).order_by(database.CheckInModel.id.desc()).all()