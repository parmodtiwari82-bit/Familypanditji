from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_expanded_knowledge_catalogue_has_fifteen_review_labelled_topics():
    response = client.get("/api/knowledge")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 15
    assert {"festival", "jyotish", "mantra", "puja", "vrata"} <= set(payload["categories"])


def test_new_topics_are_retrievable_by_hindi_and_english_aliases():
    cases = [
        ("दीपक का महत्व बताइए", "पूजा में दीपक"),
        ("Ekadashi vrat ke niyam", "एकादशी"),
        ("What is a birth chart?", "जन्मकुंडली"),
        ("Tell me about Navratri", "नवरात्रि"),
        ("मंत्र जाप कैसे करें", "मंत्र-जप"),
    ]
    for question, expected_topic in cases:
        response = client.post("/api/ask", json={"question": question, "language": "hi"})
        assert response.status_code == 200
        assert expected_topic in response.json()["matched_topic"]
        assert response.json()["needs_acharya_review"] is True


def test_new_curated_topics_return_localized_answers():
    cases = [
        ("एकादशी व्रत क्या है", "hi", "एकादशी"),
        ("Explain Navratri", "en", "Navaratri"),
        ("मुहूर्त क्या होता है", "sa", "मुहूर्त"),
    ]
    for question, language, expected in cases:
        response = client.post("/api/ask", json={"question": question, "language": language})
        assert response.status_code == 200
        assert expected in response.json()["answer"]
        assert response.json()["source_status"] == "draft_requires_acharya_review"
