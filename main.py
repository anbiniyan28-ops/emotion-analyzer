from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from google import genai
import os
import json
import logging
import time

# ----------------------------
# LOAD ENV
# ----------------------------
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=API_KEY)

# ----------------------------
# APP
# ----------------------------
app = FastAPI(
    title="Emotion API V3",
    description="AI Emotion Detection using Gemini",
    version="3.0"
)

# ----------------------------
# SERVE FRONTEND
# ----------------------------
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# ----------------------------
# CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# LOGGING
# ----------------------------
logging.basicConfig(
    filename="emotion_v3.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------------
# HISTORY FILE
# ----------------------------
HISTORY_FILE = "history.json"


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_history(messages):
    history = load_history()
    history.extend(messages)

    # Keep only last 10 messages
    history = history[-10:]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


# ----------------------------
# MODELS
# ----------------------------
class Message(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class AnalyzeRequest(BaseModel):
    messages: List[Message]
    question: str


# ----------------------------
# GEMINI CALL
# ----------------------------
def call_gemini(prompt: str):

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )

            return response.text

        except Exception as e:

            logging.error(
                f"Gemini Attempt {attempt + 1}: {str(e)}"
            )

            if attempt < 2:
                time.sleep(2)

    raise HTTPException(
        status_code=503,
        detail="Gemini is currently busy. Please try again."
    )


# ----------------------------
# CLEAN JSON
# ----------------------------
def parse_json(raw: str):

    try:
        cleaned = raw.strip()

        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception as e:

        logging.error(
            f"JSON Parse Error: {str(e)}"
        )

        logging.error(
            f"Raw Gemini Response: {raw}"
        )

        return {
            "emotion": "Neutral",
            "confidence": 0.5,
            "summary": "Unable to parse model output.",
            "response": (
                "Sorry, I had trouble understanding that. "
                "Could you try again?"
            )
        }


# ----------------------------
# ANALYZE FUNCTION
# ----------------------------
def analyze_emotion(messages, question):

    history = load_history()

    current = [
        {
            "role": m.role,
            "content": m.content
        }
        for m in messages
    ]

    full_context = (history + current)[-10:]

    conversation = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in full_context
    )

    prompt = f"""
You are an AI emotion analysis system.

Return ONLY valid JSON:

{{
  "emotion": "",
  "confidence": 0.0,
  "summary": "",
  "response": ""
}}

Rules:
- emotion must be one of:
  Happy, Sad, Angry, Frustrated, Confused, Neutral
- confidence must be between 0 and 1
- summary should be short
- response should be casual, helpful, and human-like
- do not be too formal

Conversation:
{conversation}

Question:
{question}

Return ONLY JSON.
"""

    raw = call_gemini(prompt)

    return parse_json(raw)


# ----------------------------
# ROUTES
# ----------------------------

# Open chatbot UI directly
@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.post("/analyze")
def analyze(req: AnalyzeRequest):

    try:
        result = analyze_emotion(
            req.messages,
            req.question
        )

        save_history(
            [m.model_dump() for m in req.messages]
        )

        logging.info(
            f"Emotion={result.get('emotion')} | Question={req.question}"
        )

        return {
            "success": True,
            "emotion": result.get("emotion", "Neutral"),
            "confidence": float(
                result.get("confidence", 0.5)
            ),
            "summary": result.get("summary", ""),
            "response": result.get("response", "")
        }

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=500,
            detail="Gemini returned invalid JSON"
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/history")
def get_history():

    history = load_history()

    return {
        "count": len(history),
        "history": history
    }


@app.delete("/history")
def clear_history():

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

    return {
        "success": True,
        "message": "History cleared"
    }