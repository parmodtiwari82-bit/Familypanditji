from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_knowledge_status():
    response = client.get("/api/knowledge")
    assert response.status_code == 200
    assert response.json()["count"] >= 1

def test_gayatri_question_returns_curated_entry():
    response = client.post("/api/ask", json={"question": "गायत्री मंत्र बताइए", "language": "hi"})
    assert response.status_code == 200
    assert "गायत्री" in response.json()["answer"]
    assert response.json()["needs_acharya_review"] is True

def test_empty_question_rejected():
    response = client.post("/api/ask", json={"question": "", "language": "hi"})
    assert response.status_code == 422
