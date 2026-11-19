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
