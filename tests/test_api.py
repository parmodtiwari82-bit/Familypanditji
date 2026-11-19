from pathlib import Path
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_reports_service_and_ai_configuration():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-family-pandit-ji"
    assert "ai_configured" in response.json()

def test_knowledge_status_has_categories():
    response = client.get("/api/knowledge")
    assert response.status_code == 200
    assert response.json()["count"] >= 1
    assert "puja" in response.json()["categories"]

def test_curated_gayatri_answer():
    response = client.post("/api/ask", json={"question": "गायत्री मंत्र बताइए", "language": "hi"})
    assert response.status_code == 200
    assert "गायत्री" in response.json()["matched_topic"]
    assert response.json()["mode"] in ["curated-beta", "ai-provider"]

def test_empty_question_rejected():
    response = client.post("/api/ask", json={"question": "   ", "language": "hi"})
    assert response.status_code == 422

def test_invalid_language_rejected():
    response = client.post("/api/ask", json={"question": "hello", "language": "fr"})
    assert response.status_code == 422


def test_ecosystem_module_catalogue_is_explicit_about_status():
    response = client.get("/api/modules")
    assert response.status_code == 200
    payload = response.json()
    ids = {item["id"] for item in payload["modules"]}
    assert {"ai-pandit", "panchang", "jyotish", "pandit-directory", "puja-store"} <= ids
    assert next(item for item in payload["modules"] if item["id"] == "ai-pandit")["status"] == "beta"
    assert next(item for item in payload["modules"] if item["id"] == "panchang")["status"] == "planned"

def test_knowledge_topics_returns_review_labelled_cards():
    response = client.get("/api/knowledge/topics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert payload["count"] >= 5
    assert all(topic["review_required"] is True for topic in payload["topics"])


def test_knowledge_topics_can_filter_by_category():
    response = client.get("/api/knowledge/topics", params={"category": "mantra"})
    assert response.status_code == 200
    topics = response.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["category"] == "mantra"

def test_curated_gayatri_answer_supports_english():
    response = client.post("/api/ask", json={"question": "Tell me the Gayatri mantra", "language": "en"})
    assert response.status_code == 200
    assert "We meditate" in response.json()["answer"]
    assert response.json()["needs_acharya_review"] is True


def test_curated_panchang_answer_supports_sanskrit():
    response = client.post("/api/ask", json={"question": "पंचांग के पांच अंग बताइए", "language": "sa"})
    assert response.status_code == 200
    assert "पञ्चाङ्गस्य पञ्चाङ्गानि" in response.json()["answer"]


def test_knowledge_topics_exposes_localized_drafts():
    response = client.get("/api/knowledge/topics")
    assert response.status_code == 200
    gayatri = next(x for x in response.json()["topics"] if x["id"] == "gayatri-mantra")
    assert "We meditate" in gayatri["answer_en"]
    assert "ॐ भूर्भुवः" in gayatri["answer_sa"]


def test_knowledge_topics_searches_multilingual_keywords():
    response = client.get("/api/knowledge/topics", params={"q": "panchang"})
    assert response.status_code == 200
    topics = response.json()["topics"]
    assert any(topic["id"] == "panchang-five-limbs" for topic in topics)


def test_knowledge_topics_searches_sanskrit_alias():
    response = client.get("/api/knowledge/topics", params={"q": "पञ्चाङ्ग"})
    assert response.status_code == 200
    assert response.json()["topics"][0]["id"] == "panchang-five-limbs"


def test_knowledge_topics_combines_category_and_search_filters():
    response = client.get("/api/knowledge/topics", params={"category": "mantra", "q": "Gayatri"})
    assert response.status_code == 200
    topics = response.json()["topics"]
    assert len(topics) == 1
    assert topics[0]["id"] == "gayatri-mantra"


def test_knowledge_topics_empty_search_keeps_all_drafts():
    response = client.get("/api/knowledge/topics", params={"q": "   "})
    assert response.status_code == 200
    assert response.json()["count"] >= 5


def test_samskara_catalogue_returns_sixteen_review_labelled_drafts():
    response = client.get("/api/samskaras")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert len(payload["samskaras"]) == 16
    assert all(item["review_required"] is True for item in payload["samskaras"])
    assert payload["samskaras"][0]["id"] == "garbhadhana"
    assert payload["samskaras"][-1]["id"] == "antyeshti"


def test_puja_guides_are_review_labelled_and_have_bilingual_steps():
    response = client.get("/api/puja-guides")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert payload["count"] >= 4
    assert all(item["review_required"] is True for item in payload["guides"])
    assert all(item["steps_hi"] and item["steps_en"] for item in payload["guides"])


def test_puja_guides_support_category_and_text_filters():
    response = client.get("/api/puja-guides", params={"category": "aarti", "q": "lamp"})
    assert response.status_code == 200
    guides = response.json()["guides"]
    assert len(guides) == 1
    assert guides[0]["id"] == "aarti-etiquette"


def test_question_lookup_ignores_punctuation_and_extra_spacing():
    response = client.post("/api/ask", json={"question": "  गायत्री-मंत्र   बताइए!!! ", "language": "hi"})
    assert response.status_code == 200
    assert "गायत्री" in response.json()["matched_topic"]


def test_knowledge_lookup_handles_unicode_compatibility_forms():
    response = client.post("/api/ask", json={"question": "पञ्चाङ्ग के पाँच अंग", "language": "sa"})
    assert response.status_code == 200
    assert response.json()["matched_topic"] is not None


def test_knowledge_lookup_prefers_specific_phrase_match():
    response = client.post("/api/ask", json={"question": "गायत्री मंत्र का अर्थ बताइए", "language": "hi"})
    assert response.status_code == 200
    assert "गायत्री" in response.json()["matched_topic"]


def test_panchang_overview_explains_five_limbs_without_claiming_live_calculation():
    response = client.get("/api/panchang/overview")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "educational_reference_only"
    assert payload["live_calculation_available"] is False
    assert payload["review_required"] is True
    assert [item["id"] for item in payload["limbs"]] == [
        "tithi", "vara", "nakshatra", "yoga", "karana"
    ]
    assert payload["summary_en"]
    assert payload["summary_sa"]


def test_mantra_library_returns_review_labelled_multilingual_entries():
    response = client.get("/api/mantras")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert payload["count"] >= 1
    assert all(item["review_required"] is True for item in payload["mantras"])
    assert all(item["text_hi"] and item["text_en"] and item["text_sa"] for item in payload["mantras"])


def test_mantra_library_searches_sanskrit_and_english_aliases():
    sanskrit = client.get("/api/mantras", params={"q": "गायत्री"})
    english = client.get("/api/mantras", params={"q": "Gayatri"})
    assert sanskrit.status_code == english.status_code == 200
    assert sanskrit.json()["count"] == english.json()["count"] == 1
    assert sanskrit.json()["mantras"][0]["id"] == "gayatri-mantra"



def test_knowledge_topics_searches_sanskrit_answer_text():
    response = client.get("/api/knowledge/topics", params={"q": "पञ्चाङ्गस्य"})
    assert response.status_code == 200
    assert any(topic["id"] == "panchang-five-limbs" for topic in response.json()["topics"])


def test_puja_guides_search_ignores_punctuation_and_spacing():
    response = client.get("/api/puja-guides", params={"q": "दीप   प्रज्वलित"})
    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_installable_app_assets_are_served():
    manifest = client.get("/manifest.webmanifest")
    worker = client.get("/sw.js")
    icon = client.get("/icons/panditji.svg")
    assert manifest.status_code == worker.status_code == icon.status_code == 200
    assert manifest.json()["display"] == "standalone"
    assert manifest.json()["start_url"] == "/"
    assert "APP_SHELL" in worker.text
    assert "<svg" in icon.text


def test_frontend_exposes_voice_picker_and_registers_app_shell():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="voiceChoice"' in frontend
    assert "voiceschanged" in frontend
    assert "navigator.serviceWorker.register('/sw.js')" in frontend
    assert 'id="installApp"' in frontend
    assert "beforeinstallprompt" in frontend
