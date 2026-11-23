from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_expanded_knowledge_catalogue_has_fifteen_topics_without_mandatory_review():
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
        assert response.json()["needs_acharya_review"] is False


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
        assert response.json()["source_status"] == "curated_catalogue_unverified"



def test_curated_matcher_does_not_guess_between_equally_relevant_topics():
    from main import find_curated_answer

    assert find_curated_answer("दीपक और आरती") is None


def test_curated_matcher_prefers_the_most_specific_phrase():
    from main import find_curated_answer

    entry = find_curated_answer("गायत्री मंत्र का अर्थ बताइए")
    assert entry is not None
    assert entry["id"] == "gayatri-mantra"


def test_curated_matcher_normalizes_romanized_hindi_spacing_and_punctuation():
    from main import find_curated_answer

    entry = find_curated_answer("  Ekadashi—vrat ke niyam!!! ")
    assert entry is not None
    assert entry["id"] == "ekadashi-general"



def test_ask_retrieves_puja_guide_content_instead_of_knowledge_only():
    response = client.post("/api/ask", json={
        "question": "दैनिक गृह पूजा की विधि बताइए", "language": "hi"
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_topic"] == "दैनिक गृह पूजा"
    assert "पूजा-स्थान" in payload["answer"]
    assert payload["source_status"] == "draft_requires_acharya_review"


def test_ask_retrieves_samskara_content_with_english_localization():
    response = client.post("/api/ask", json={
        "question": "Explain Namakarana", "language": "en"
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["matched_topic"] == "नामकरण"
    assert "naming ceremony" in payload["answer"].lower()
    assert payload["needs_acharya_review"] is True
