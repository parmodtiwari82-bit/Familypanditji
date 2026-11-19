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
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
AI_TIMEOUT_SECONDS = float(os.getenv("AI_TIMEOUT_SECONDS", "25"))
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()]


def validate_runtime_config(environment: str, allowed_origins: list[str],
                            ai_base_url: str, timeout_seconds: float) -> None:
    """Fail fast on unsafe or invalid runtime settings, especially in production."""
    if environment not in {"development", "staging", "production"}:
        raise ValueError("APP_ENV must be development, staging or production.")
    if not 1 <= timeout_seconds <= 120:
        raise ValueError("AI_TIMEOUT_SECONDS must be between 1 and 120.")
    if environment == "production":
        if not allowed_origins or "*" in allowed_origins:
            raise ValueError("Production requires explicit ALLOWED_ORIGINS; wildcard is not allowed.")
        if not ai_base_url.startswith("https://"):
            raise ValueError("Production AI_BASE_URL must use HTTPS.")


validate_runtime_config(APP_ENV, ALLOWED_ORIGINS, AI_BASE_URL, AI_TIMEOUT_SECONDS)

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

@app.get("/api/release/readiness")
def release_readiness():
    """Return an honest production checklist; beta code must not self-certify as launched."""
    checks = {
        "production_environment": APP_ENV == "production",
        "ai_provider_configured": bool(AI_API_KEY and AI_MODEL),
        "explicit_cors_origins": bool(ALLOWED_ORIGINS) and "*" not in ALLOWED_ORIGINS,
        "live_panchang_engine": False,
        "validated_jyotish_engine": False,
        "verified_pandit_booking": False,
        "payment_gateway": False,
        "acharya_content_signoff": False,
        "production_voice_service": False,
        "live_hosting_verified": False,
    }
    passed = [name for name, ok in checks.items() if ok]
    pending = [name for name, ok in checks.items() if not ok]
    return {
        "release_status": "production_ready" if not pending else "development_beta_not_production_ready",
        "production_release_ready": not pending,
        "checks_passed": len(passed),
        "checks_total": len(checks),
        "checks": checks,
        "pending": pending,
        "note_hi": "यह स्वचालित कॉन्फ़िगरेशन चेक है, सुरक्षा ऑडिट या आचार्य प्रमाणन नहीं। सभी बाहरी सेवाओं और मानवीय अनुमोदनों के बिना सार्वजनिक लॉन्च न करें।",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ai-family-pandit-ji",
        "version": APP_VERSION,
        "ai_configured": bool(AI_API_KEY and AI_MODEL),
    }

@app.get("/api/trust/status")
def trust_status():
    """Expose implementation and review readiness without overstating product readiness."""
    entries = load_knowledge()
    guides_path = PROJECT_ROOT / "data" / "puja_guides.json"
    samskaras_path = PROJECT_ROOT / "data" / "samskaras.json"
    modules_path = PROJECT_ROOT / "data" / "ecosystem_modules.json"
    try:
        with guides_path.open(encoding="utf-8") as handle:
            guides = json.load(handle).get("guides", [])
    except (OSError, json.JSONDecodeError):
        guides = []
    try:
        with samskaras_path.open(encoding="utf-8") as handle:
            samskaras = json.load(handle).get("samskaras", [])
    except (OSError, json.JSONDecodeError):
        samskaras = []
    try:
        with modules_path.open(encoding="utf-8") as handle:
            modules = json.load(handle).get("modules", [])
    except (OSError, json.JSONDecodeError):
        modules = []

    return {
        "service": "ai-family-pandit-ji",
        "environment": "development_beta",
        "ai_provider_configured": bool(AI_API_KEY and AI_MODEL),
        "content_review": {
            "status": "acharya_review_required",
            "knowledge_entries": len(entries),
            "puja_guides": len(guides),
            "samskara_entries": len(samskaras),
            "all_content_is_draft": True,
        },
        "capabilities": {
            "panchang_live_calculation": False,
            "kundli_calculation": False,
            "verified_pandit_booking": False,
            "commerce_and_payments": False,
            "production_voice_service": False,
        },
        "modules": {
            "beta": sum(1 for item in modules if item.get("status") == "beta"),
            "planned": sum(1 for item in modules if item.get("status") == "planned"),
        },
        "production_release_ready": False,
        "note": "यह स्थिति-पृष्ठ पारदर्शिता के लिए है; यह आचार्य सत्यापन, सुरक्षा ऑडिट या production deployment का प्रमाण नहीं है।",
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
        {"id": "tithi", "name_hi": "तिथि", "name_en": "Tithi", "name_sa": "तिथिः", "description_hi": "चन्द्र-सूर्य के कोणीय अन्तर पर आधारित चन्द्र दिवस।", "description_en": "A lunar day based on the angular relationship between the Sun and Moon.", "description_sa": "सूर्यचन्द्रयोः कोणान्तराधारितः चन्द्रदिवसः।"},
        {"id": "vara", "name_hi": "वार", "name_en": "Vara", "name_sa": "वारः", "description_hi": "सप्ताह का दिन।", "description_en": "The weekday.", "description_sa": "सप्ताहस्य दिनम्।"},
        {"id": "nakshatra", "name_hi": "नक्षत्र", "name_en": "Nakshatra", "name_sa": "नक्षत्रम्", "description_hi": "चन्द्रमा की नक्षत्र-पथ में स्थिति से सम्बद्ध खण्ड।", "description_en": "The lunar mansion associated with the Moon's position along the nakshatra belt.", "description_sa": "चन्द्रस्य स्थित्या सम्बद्धं नक्षत्रम्।"},
        {"id": "yoga", "name_hi": "योग", "name_en": "Yoga", "name_sa": "योगः", "description_hi": "सूर्य और चन्द्रमा के दीर्घांशों के योग पर आधारित अंग।", "description_en": "A limb calculated from the sum of the Sun's and Moon's longitudes.", "description_sa": "सूर्यचन्द्रयोः दीर्घांशयोगेन गणितः पञ्चाङ्गाङ्गविशेषः।"},
        {"id": "karana", "name_hi": "करण", "name_en": "Karana", "name_sa": "करणम्", "description_hi": "तिथि का आधा भाग।", "description_en": "Half of a Tithi.", "description_sa": "तिथेः अर्धभागः।"},
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


@app.get("/api/jyotish/guide")
def jyotish_guide():
    """Describe the consent-based birth details needed for a future verified chart service."""
    return {
        "status": "integration_blueprint_only",
        "calculation_available": False,
        "required_inputs": [
            {"id": "birth_date", "label_hi": "जन्म तिथि", "required": True},
            {"id": "birth_time", "label_hi": "जन्म समय", "required": True, "note": "समय की सटीकता बताना आवश्यक है।"},
            {"id": "birth_place", "label_hi": "जन्म स्थान", "required": True},
            {"id": "timezone", "label_hi": "समय क्षेत्र", "required": True},
        ],
        "privacy": "जन्म विवरण संवेदनशील व्यक्तिगत जानकारी है; स्पष्ट सहमति और सुरक्षित भंडारण के बिना इसे जमा न करें।",
        "limitations": [
            "कोई ग्रह-स्थिति, लग्न, दशा, गुण-मिलान या भविष्यवाणी गणना नहीं की जाती।",
            "गणना इंजन, पंचांग/अयनांश पद्धति और विशेषज्ञ सत्यापन अभी एकीकृत नहीं हैं।",
        ],
        "review_required": True,
    }


@app.get("/api/pandits")
def pandit_directory(status: str = "verified"):
    """Return only real directory records; no fabricated pandit profiles or bookings."""
    if status not in {"verified", "pending", "all"}:
        raise HTTPException(status_code=422, detail="Status must be verified, pending or all.")
    directory_path = PROJECT_ROOT / "data" / "pandit_directory.json"
    try:
        with directory_path.open(encoding="utf-8") as handle:
            records = json.load(handle).get("pandits", [])
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=503, detail="Pandit directory catalogue is unavailable.")
    if status != "all":
        records = [item for item in records if item.get("verification_status") == status]
    return {
        "status": "directory_beta_no_booking",
        "count": len(records),
        "pandits": records,
        "booking_available": False,
        "verification_policy": "किसी प्रोफ़ाइल को verified तभी दिखाया जाएगा जब पहचान और योग्यता की मानवीय जाँच पूरी हो।",
        "note": "अभी कोई सत्यापित पंडित प्रोफ़ाइल उपलब्ध नहीं है; खाली सूची का अर्थ सेवा की उपलब्धता नहीं है।",
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


@app.get("/api/search")
def unified_search(q: str, language: str = "hi", limit: int = 20):
    """Search knowledge, mantra and puja-guide drafts from one endpoint."""
    query = normalize_search_text(q)
    if not query:
        raise HTTPException(status_code=422, detail="Search query cannot be blank.")
    if len(query) > 120:
        raise HTTPException(status_code=422, detail="Search query must be 120 characters or fewer.")
    if language not in {"hi", "sa", "en"}:
        raise HTTPException(status_code=422, detail="Language must be hi, sa or en.")
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 50.")

    results: list[dict[str, Any]] = []

    def add_result(kind: str, item_id: str, title: str, fields: list[str], snippet: str):
        searchable = " ".join(str(value) for value in [title, *fields] if value)
        if query in normalize_search_text(searchable):
            results.append({
                "type": kind,
                "id": item_id,
                "title": title,
                "snippet": snippet[:280],
                "review_required": True,
                "status": "draft_requires_acharya_review",
            })

    for entry in load_knowledge():
        title = str(entry.get("title", ""))
        answer_field = {"hi": "answer", "sa": "answer_sa", "en": "answer_en"}[language]
        snippet = str(entry.get(answer_field) or entry.get("answer", ""))
        add_result("knowledge", str(entry.get("id", "")), title,
                   [*entry.get("keywords", []), entry.get("answer", ""),
                    entry.get("answer_en", ""), entry.get("answer_sa", "")], snippet)

    for entry in load_knowledge():
        if entry.get("category") == "mantra":
            title = str(entry.get("title", ""))
            field = {"hi": "answer", "sa": "answer_sa", "en": "answer_en"}[language]
            add_result("mantra", str(entry.get("id", "")), title,
                       [*entry.get("keywords", []), entry.get("answer", ""),
                        entry.get("answer_en", ""), entry.get("answer_sa", "")],
                       str(entry.get(field) or entry.get("answer", "")))

    guides_path = PROJECT_ROOT / "data" / "puja_guides.json"
    try:
        with guides_path.open(encoding="utf-8") as handle:
            guides = json.load(handle).get("guides", [])
    except (OSError, json.JSONDecodeError):
        guides = []
    for guide in guides:
        title_field = "title_en" if language == "en" else "title_hi"
        summary_field = "summary_en" if language == "en" else "summary_hi"
        title = str(guide.get(title_field) or guide.get("title_hi", ""))
        snippet = str(guide.get(summary_field) or guide.get("summary_hi", ""))
        fields = [guide.get("title_hi", ""), guide.get("title_en", ""),
                  guide.get("summary_hi", ""), guide.get("summary_en", ""),
                  *guide.get("steps_hi", []), *guide.get("steps_en", [])]
        add_result("puja-guide", str(guide.get("id", "")), title, fields, snippet)

    # Prefer exact title matches, then stable source order; never imply scriptural verification.
    results.sort(key=lambda item: 0 if normalize_search_text(item["title"]) == query else 1)
    return {
        "query": q,
        "language": language,
        "count": min(len(results), limit),
        "total_matches": len(results),
        "status": "draft_requires_acharya_review",
        "results": results[:limit],
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
