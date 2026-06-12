# Emotion Analysis API 

## Overview

This project is a FastAPI-based Emotion Analysis API that uses Google's Gemini AI to analyze user conversations, detect emotions, and generate context-aware responses.

The API accepts conversation history and a user question, then returns:

* Detected emotion
* Confidence score
* Emotion summary
* Human-like response

The application also stores the last 10 conversation messages for context awareness.

---

#Features

* Emotion Detection
* Confidence Scoring
* Context-Aware Responses
* Gemini AI Integration
* Conversation History Management
* Logging Support
* REST API using FastAPI
* Interactive Swagger Documentation

---

#Technologies Used

* Python
* FastAPI
* Gemini 2.5 Flash
* Pydantic
* Uvicorn
* Python Dotenv

---

## API Endpoints

### GET /

Returns API status.

### GET /health

Returns application health status.

### POST /analyze

Analyzes conversation and returns emotion details.

### GET /history

Returns stored conversation history.

### DELETE /history

Clears conversation history.

---

## Sample Output

{
"success": true,
"emotion": "Frustrated",
"confidence": 0.87,
"summary": "The user appears frustrated due to repeated unsuccessful attempts.",
"response": "I understand your frustration. Let's simplify the problem and solve it step by step."
}

---

## Author

Student Project – AI-Based Emotion Analysis API
