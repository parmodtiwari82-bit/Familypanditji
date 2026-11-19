import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_VERSION = "0.3.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = PROJECT_ROOT / "data" / "knowledge_hi.json"
AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "").strip()
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "25"))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]

app = FastAPI(
    title="AI Family Pandit Ji API",
    description="Multilingual Sanatan guidance API with reviewed-knowledge-first fallback.",
    version=APP_VERSION,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="hi", pattern="^(hi|sa|en)$")

class AskResponse(BaseModel):
    answer: str
    mode: str
    needs_acharya_review: bool = True
    source_status: str
    matched_topic: str | None = None

def load_knowledge() -> list[dict[str, Any]]:
    try:
        with KNOWLEDGE_PATH.open(encoding="utf-8") as handle:
            return json.load(handle).get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []

def find_curated_answer(question: str) -> dict[str, Any] | None:
    folded = question.casefold()
    for entry in load_knowledge():
        keywords = entry.get("keywords", [])
        if any(str(keyword).casefold() in folded for keyword in keywords):
            return entry
    return None

def language_instruction(language: str) -> str:
    return {
        "hi": "उत्तर सरल, सम्मानजनक हिंदी में दें। आवश्यक संस्कृत मंत्र देवनागरी में रखें।",
        "sa": "उत्तर यथासंभव सरल संस्कृत में दें। कठिन विषयों में संक्षिप्त हिंदी स्पष्टीकरण दे सकते हैं।",
        "en": "Answer in clear, respectful English. Preserve Sanskrit mantras in Devanagari and explain them.",
    }[language]

async def ask_ai(question: str, language: str, context: str) -> str | None:
    if not AI_API_KEY or not AI_MODEL:
        return None
    system_prompt = (
        "You are AI Family Pandit Ji, a careful multilingual assistant for Sanatan traditions. "
        "Be respectful and non-sectarian. Traditions differ by sampradaya, region and family; "
        "never present a disputed practice as universal. Do not invent scripture quotations, "
        "mantra wording, citations, Panchang timings, astrological calculations or ritual rules. "
        "Use the supplied knowledge context when relevant, and clearly say when you cannot verify "
        "something. For consequential ritual decisions, recommend confirmation by a qualified acharya. "
        "Do not give medical, legal or financial advice as religious certainty. "
        + language_instruction(language)
    )
    user_prompt = f"Question: {question}\n\nCurated knowledge context (may be draft; do not treat as verified scripture):\n{context or 'No matching curated entry.'}"
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{AI_BASE_URL}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        answer = data["choices"][0]["message"]["content"]
        return answer.strip() if isinstance(answer, str) and answer.strip() else None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return None

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(PROJECT_ROOT / "index.html")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-family-pandit-ji",
        "version": APP_VERSION,
        "ai_configured": bool(AI_API_KEY and AI_MODEL),
    }

@app.get("/api/knowledge")
def knowledge_status():
    entries = load_knowledge()
    return {
        "count": len(entries),
        "status": "draft_requires_acharya_review",
        "categories": sorted({entry.get("category", "general") for entry in entries}),
    }

@app.post("/api/ask", response_model=AskResponse)
async def ask(payload: AskRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question cannot be blank.")

    entry = find_curated_answer(question)
    context = ""
    if entry:
        context = f"Topic: {entry.get('title', '')}\nAnswer: {entry.get('answer', '')}"
    ai_answer = await ask_ai(question, payload.language, context)
    if ai_answer:
        return AskResponse(
            answer=ai_answer,
            mode="ai-provider",
            needs_acharya_review=True,
            source_status="ai_generated_requires_review",
            matched_topic=entry.get("title") if entry else None,
        )

    if entry:
        return AskResponse(
            answer=entry["answer"],
            mode="curated-beta",
            needs_acharya_review=entry.get("review_required", True),
            source_status="draft_requires_acharya_review",
            matched_topic=entry.get("title"),
        )

    fallback = {
        "hi": "आपका प्रश्न प्राप्त हुआ। इस बीटा में सीमित प्रारंभिक ज्ञान-संग्रह उपलब्ध है। कृपया प्रश्न को पूजा, मंत्र, संस्कार, व्रत या पंचांग के संदर्भ में स्पष्ट करें। विशिष्ट धार्मिक निर्णय की पुष्टि योग्य आचार्य से करें।",
        "sa": "अस्मिन् प्रारम्भिक संस्करणे सीमितं ज्ञानसङ्ग्रहं उपलब्धम् अस्ति। कृपया प्रश्नं अधिकं स्पष्टं कुरुत। विशेषधार्मिकनिर्णयाय योग्याचार्यस्य परामर्शं स्वीकरोतु।",
        "en": "Your question was received. This beta has a limited starter knowledge library. Please add context about puja, mantra, samskara, vrata or Panchang. Confirm consequential religious decisions with a qualified acharya.",
    }[payload.language]
    return AskResponse(
        answer=fallback,
        mode="curated-beta-fallback",
        source_status="no_matching_reviewed_source",
    )
