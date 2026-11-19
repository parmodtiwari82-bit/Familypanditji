import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="AI Family Pandit Ji API", version="0.2.0")

# Production deployment must replace "*" with the actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_hi.json"

def load_knowledge():
    try:
        with KNOWLEDGE_PATH.open(encoding="utf-8") as handle:
            return json.load(handle).get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="hi", pattern="^(hi|sa|en)$")

class AskResponse(BaseModel):
    answer: str
    mode: str = "curated-beta"
    needs_acharya_review: bool = True
    source_status: str = "draft_requires_acharya_review"

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-family-pandit-ji", "version": "0.2.0"}

@app.get("/api/knowledge")
def knowledge_status():
    entries = load_knowledge()
    return {"count": len(entries), "status": "draft_requires_acharya_review"}

@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    question = payload.question.casefold()
    for entry in load_knowledge():
        if any(keyword.casefold() in question for keyword in entry.get("keywords", [])):
            return AskResponse(
                answer=entry["answer"],
                mode="curated-beta",
                needs_acharya_review=entry.get("review_required", True),
            )
    return AskResponse(
        answer=(
            "आपका प्रश्न प्राप्त हुआ। इस बीटा में अभी सीमित, प्रारंभिक ज्ञान-संग्रह उपलब्ध है। "
            "कृपया प्रश्न को पूजा, मंत्र, संस्कार, व्रत या पंचांग के संदर्भ में स्पष्ट करें। "
            "विशिष्ट धार्मिक निर्णय की पुष्टि योग्य आचार्य से करें।"
        ),
        mode="curated-beta-fallback",
    )
