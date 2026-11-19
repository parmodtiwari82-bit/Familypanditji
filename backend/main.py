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

def localized_answer(entry: dict[str, Any], language: str) -> str:
    """Return a reviewed-status draft in the requested language, with Hindi fallback."""
    field = {"hi": "answer", "sa": "answer_sa", "en": "answer_en"}[language]
    return str(entry.get(field) or entry.get("answer", ""))


def normalize_search_text(value: str) -> str:
    """Normalize Unicode and punctuation for Hindi, Sanskrit and English lookup."""
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", normalized)
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def find_curated_answer(question: str) -> dict[str, Any] | None:
    folded = f" {normalize_search_text(question)} "
    matches: list[tuple[int, dict[str, Any]]] = []
    for entry in load_knowledge():
        keywords = entry.get("keywords", [])
        for keyword in keywords:
            normalized_keyword = normalize_search_text(str(keyword))
            if normalized_keyword and f" {normalized_keyword} " in folded:
                matches.append((len(normalized_keyword), entry))
    # Prefer the most specific phrase when a question contains multiple aliases.
    return max(matches, key=lambda item: item[0])[1] if matches else None

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

@app.get("/manifest.webmanifest", include_in_schema=False)
def web_manifest():
    return FileResponse(PROJECT_ROOT / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js", include_in_schema=False)
def service_worker():
    return FileResponse(PROJECT_ROOT / "sw.js", media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/icons/panditji.svg", include_in_schema=False)
def app_icon():
    return FileResponse(PROJECT_ROOT / "icons" / "panditji.svg", media_type="image/svg+xml")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-family-pandit-ji",
        "version": APP_VERSION,
        "ai_configured": bool(AI_API_KEY and AI_MODEL),
    }

@app.get("/api/modules")
def ecosystem_modules():
    """Return the product module catalogue and clearly-labelled implementation status."""
    catalog_path = PROJECT_ROOT / "data" / "ecosystem_modules.json"
    try:
        with catalog_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Ecosystem module catalogue is unavailable.")


@app.get("/api/panchang/overview")
def panchang_overview():
    """Provide a static educational explanation, not live date/location calculations."""
    entry = next((item for item in load_knowledge() if item.get("id") == "panchang-five-limbs"), None)
    if not entry:
        raise HTTPException(status_code=503, detail="Panchang reference is unavailable.")
    limbs = [
        {"id": "tithi", "name_hi": "तिथि", "name_en": "Tithi", "name_sa": "तिथिः", "description_hi": "चन्द्र-सूर्य के कोणीय अन्तर पर आधारित चन्द्र दिवस।", "description_en": "A lunar day based on the angular relationship between the Sun and Moon."},
        {"id": "vara", "name_hi": "वार", "name_en": "Vara", "name_sa": "वारः", "description_hi": "सप्ताह का दिन।", "description_en": "The weekday."},
        {"id": "nakshatra", "name_hi": "नक्षत्र", "name_en": "Nakshatra", "name_sa": "नक्षत्रम्", "description_hi": "चन्द्रमा की नक्षत्र-पथ में स्थिति से सम्बद्ध खण्ड।", "description_en": "The lunar mansion associated with the Moon's position along the nakshatra belt."},
        {"id": "yoga", "name_hi": "योग", "name_en": "Yoga", "name_sa": "योगः", "description_hi": "सूर्य और चन्द्रमा के दीर्घांशों के योग पर आधारित अंग।", "description_en": "A limb calculated from the sum of the Sun's and Moon's longitudes."},
        {"id": "karana", "name_hi": "करण", "name_en": "Karana", "name_sa": "करणम्", "description_hi": "तिथि का आधा भाग।", "description_en": "Half of a Tithi."},
    ]
    return {
        "status": "educational_reference_only",
        "title": entry.get("title", "पंचांग के पाँच अंग"),
        "summary_hi": entry.get("answer", ""),
        "summary_en": entry.get("answer_en", ""),
        "summary_sa": entry.get("answer_sa", ""),
        "limbs": limbs,
        "live_calculation_available": False,
        "review_required": True,
        "note": "यह स्थिर शैक्षिक परिचय है, आज का पंचांग या मुहूर्त गणना नहीं। सटीक विवरण के लिए स्थान, समय-क्षेत्र, सूर्योदय और मान्य गणना-पद्धति आवश्यक हैं।",
    }


@app.get("/api/puja-guides")
def puja_guides(category: str | None = None, q: str | None = None):
    """Return introductory puja/aarti guides, all explicitly marked as drafts."""
    catalog_path = PROJECT_ROOT / "data" / "puja_guides.json"
    try:
        with catalog_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Puja guide catalogue is unavailable.")
    guides = payload.get("guides", [])
    if category:
        wanted = category.strip().casefold()
        guides = [item for item in guides if item.get("category", "").casefold() == wanted]
    if q and q.strip():
        query = normalize_search_text(q)
        guides = [
            item for item in guides
            if query in normalize_search_text(str(item.get("title_hi", "")))
            or query in normalize_search_text(str(item.get("title_en", "")))
            or query in normalize_search_text(str(item.get("summary_hi", "")))
            or query in normalize_search_text(str(item.get("summary_en", "")))
            or any(
                query in normalize_search_text(str(step))
                for step in item.get("steps_hi", []) + item.get("steps_en", [])
            )
        ]
    return {
        "status": payload.get("status", "draft_requires_acharya_review"),
        "note": payload.get("note", ""),
        "count": len(guides),
        "guides": guides,
    }

@app.get("/api/samskaras")
def samskara_catalogue():
    """Return the draft sixteen-samskara reference with explicit acharya review status."""
    catalog_path = PROJECT_ROOT / "data" / "samskaras.json"
    try:
        with catalog_path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Samskara catalogue is unavailable.")


@app.get("/api/mantras")
def mantra_library(q: str | None = None):
    """Expose mantra-category knowledge entries with their review status."""
    entries = [entry for entry in load_knowledge() if entry.get("category") == "mantra"]
    if q and q.strip():
        query = normalize_search_text(q)
        entries = [
            entry for entry in entries
            if query in normalize_search_text(entry.get("title", ""))
            or any(query in normalize_search_text(str(keyword)) for keyword in entry.get("keywords", []))
            or query in normalize_search_text(entry.get("answer", ""))
            or query in normalize_search_text(entry.get("answer_en", ""))
        ]
    return {
        "status": "draft_requires_acharya_review",
        "count": len(entries),
        "mantras": [
            {
                "id": entry.get("id"),
                "title": entry.get("title", ""),
                "keywords": entry.get("keywords", []),
                "text_hi": entry.get("answer", ""),
                "text_en": entry.get("answer_en", ""),
                "text_sa": entry.get("answer_sa", ""),
                "review_required": entry.get("review_required", True),
            }
            for entry in entries
        ],
    }


@app.get("/api/knowledge/topics")
def knowledge_topics(category: str | None = None, q: str | None = None):
    """Expose starter knowledge cards with explicit review status."""
    entries = load_knowledge()
    if category:
        wanted = category.strip().casefold()
        entries = [entry for entry in entries if entry.get("category", "").casefold() == wanted]
    if q and q.strip():
        query = normalize_search_text(q)
        entries = [
            entry for entry in entries
            if query in normalize_search_text(str(entry.get("title", "")))
            or any(query in normalize_search_text(str(keyword)) for keyword in entry.get("keywords", []))
            or query in normalize_search_text(str(entry.get("answer", "")))
            or query in normalize_search_text(str(entry.get("answer_en", "")))
            or query in normalize_search_text(str(entry.get("answer_sa", "")))
        ]
    return {
        "status": "draft_requires_acharya_review",
        "count": len(entries),
        "topics": [
            {
                "id": entry.get("id"),
                "category": entry.get("category", "general"),
                "title": entry.get("title", ""),
                "keywords": entry.get("keywords", []),
                "answer": entry.get("answer", ""),
                "answer_en": entry.get("answer_en", ""),
                "answer_sa": entry.get("answer_sa", ""),
                "review_required": entry.get("review_required", True),
            }
            for entry in entries
        ],
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
        context = f"Topic: {entry.get('title', '')}\nAnswer: {localized_answer(entry, payload.language)}"
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
            answer=localized_answer(entry, payload.language),
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
