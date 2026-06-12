from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from google import genai
import os
import json
import logging

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
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_history(messages):
    history = load_history()
    history.extend(messages)
    history = history[-10:]  # keep last 10 messages

    with open(HISTORY_FILE, "w") as f:
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
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=503, detail="Gemini API error")


# ----------------------------
# CLEAN JSON
# ----------------------------
def parse_json(raw: str):
    cleaned = raw.strip()

    # remove code blocks if any
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    return json.loads(cleaned)


# ----------------------------
# ANALYZE FUNCTION
# ----------------------------
def analyze_emotion(messages, question):

    history = load_history()

    current = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]

    full_context = (history + current)[-10:]

    conversation = "\n".join(
        f"{m['role']}: {m['content']}"
        for m in full_context
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
- emotion: Happy, Sad, Angry, Frustrated, Confused, Neutral
- confidence: 0 to 1
- summary: short reasoning
- response: causal(like a normal human) helpful answer 
- no need to be too formal, be casual and concise

Conversation: 
{conversation}

Question:
{question}

Return ONLY JSON. No explanation.
"""

    raw = call_gemini(prompt)
    return parse_json(raw)


# ----------------------------
# ROUTES
# ----------------------------
@app.get("/")
def home():
    return {"status": "ok", "message": "Emotion API V3 running 🚀"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):

    try:
        result = analyze_emotion(req.messages, req.question)

        save_history([m.dict() for m in req.messages])

        logging.info(
            f"Emotion={result.get('emotion')} | Q={req.question}"
        )

        return {
            "success": True,
            "emotion": result.get("emotion", "Neutral"),
            "confidence": float(result.get("confidence", 0.5)),
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
    return {
        "count": len(load_history()),
        "history": load_history()
    }


@app.delete("/history")
def clear_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

    return {"success": True, "message": "History cleared"}
