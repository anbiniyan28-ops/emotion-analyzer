from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
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
    title="Emotion API",
    description="Fast Emotion Detection using Gemini",
    version="4.0"
)

# ----------------------------
# SERVE FRONTEND
# ----------------------------
app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
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
    filename="emotion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------------
# REQUEST MODEL
# ----------------------------
class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=1)

# ----------------------------
# GEMINI CALL
# ----------------------------
def call_gemini(prompt: str):

    for attempt in range(2):

        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )
            return response.text

        except Exception as e:
            logging.error(f"Gemini Attempt {attempt + 1}: {str(e)}")

            if attempt < 1:
                time.sleep(0.5)

    raise HTTPException(
        status_code=503,
        detail="Gemini is currently unavailable."
    )

# ----------------------------
# PROMPT TEMPLATE
# ----------------------------
PROMPT_TEMPLATE = """
Analyze the user's emotion.

Return ONLY JSON:
{
  "emotion": "",
  "confidence": 0,
  "response": ""
}

Rules:
- emotion must be one of: Happy, Sad, Angry, Frustrated, Confused, Neutral
- confidence must be between 0 and 1
- response must be formal, like customer care support
- response must be supportive, polite, helpful
- response must be short (1–3 sentences)
- do NOT mention emotion or analysis
- return ONLY JSON

User:
{question}
"""

# ----------------------------
# JSON PARSER
# ----------------------------
def parse_json(raw: str):

    try:
        cleaned = raw.strip()
        cleaned = cleaned.replace("```json", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        return json.loads(cleaned)

    except Exception as e:

        logging.error(f"JSON Parse Error: {str(e)}")
        logging.error(f"Raw Response: {raw}")

        return {
            "emotion": "Neutral",
            "confidence": 0.5,
            "response": "Sorry, I couldn't process your request right now."
        }

# ----------------------------
# CORE FUNCTION
# ----------------------------
def analyze_emotion(question: str):

    prompt = PROMPT_TEMPLATE.format(question=question)

    raw = call_gemini(prompt)

    return parse_json(raw)

# ----------------------------
# ROUTES
# ----------------------------
@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):

    try:

        result = analyze_emotion(req.question)

        emotion = result.get("emotion", "Neutral")
        confidence = float(result.get("confidence", 0.5))
        response = result.get("response", "")

        logging.info(f"Emotion={emotion} | Question={req.question}")

        return {
            "success": True,
            "emotion": emotion,
            "confidence": confidence,
            "response": response
        }

    except Exception as e:

        logging.error(str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "Emotion API"
    }