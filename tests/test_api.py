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
    assert len(topics) == 1
    assert topics[0]["id"] == "panchang-five-limbs"


def test_knowledge_topics_searches_sanskrit_alias():
    response = client.get("/api/knowledge/topics", params={"q": "पञ्चाङ्ग"})
    assert response.status_code == 200
    assert response.json()["topics"][0]["id"] == "panchang-five-limbs"
