from fastapi import FastAPI
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, messaging

app = FastAPI()
@app.get("/")
def root():
    return {"status": "Exam Alert Backend Running"}


# ---------------------------
# Firebase setup
# ---------------------------
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging

if not firebase_admin._apps:
    if "FIREBASE_KEY" in os.environ:
        # Running in Railway / Cloud
        cred = credentials.Certificate(
            json.loads(os.environ["FIREBASE_KEY"])
        )
    else:
        # Running locally
        cred = credentials.Certificate("firebase-key.json")

    firebase_admin.initialize_app(cred)


# ---------------------------
# In-memory tracking (demo-safe)
# ---------------------------
focus_counter = {}

# ---------------------------
# Request model
# ---------------------------
class ViolationEvent(BaseModel):
    student_id: str
    exam_id: str
    event_type: str   # "focus_lost"
    device_token: str # invigilator phone token

# ---------------------------
# Helper: Send push notification
# ---------------------------
def send_alert(token, title, body):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token,
        )
        messaging.send(message)
        print("Alert sent successfully")
    except Exception as e:
        print("Alert failed:", e)

# ---------------------------
# Event endpoint
# ---------------------------
@app.post("/event")
def receive_event(event: ViolationEvent):

    key = f"{event.exam_id}:{event.student_id}"
    focus_counter[key] = focus_counter.get(key, 0) + 1
    count = focus_counter[key]

    if count == 2:
        send_alert(
            event.device_token,
            "Exam Warning",
            f"Student {event.student_id} lost focus twice"
        )

    if count >= 3:
        send_alert(
            event.device_token,
            "Exam Flagged",
            f"Student {event.student_id} flagged for cheating"
        )

    return {
        "status": "ok",
        "focus_lost_count": count
    }
