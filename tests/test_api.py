from pathlib import Path
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_reports_service_and_ai_configuration():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "ai-family-pandit-ji"
    assert "ai_configured" in response.json()


def test_security_headers_are_present_and_api_responses_are_not_cached():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(self), geolocation=()"
    assert response.headers["Cache-Control"] == "no-store"

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


def test_question_over_maximum_length_is_rejected():
    response = client.post("/api/ask", json={"question": "x" * 4001, "language": "en"})
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
    assert all(item["description_sa"] for item in payload["limbs"])


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


def test_frontend_prevents_duplicate_chat_requests_and_supports_stopping_voice_input():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert "let isSending=false;" in frontend
    assert "if(isSending)return;" in frontend
    assert "finally{isSending=false;sendButton.disabled=false}" in frontend
    assert "let activeRecognition=null;" in frontend
    assert "if(activeRecognition){activeRecognition.stop();activeRecognition=null}" in frontend
    assert "आपकी बात सुन रहा हूँ" in frontend


def test_frontend_exposes_voice_picker_and_registers_app_shell():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="voiceChoice"' in frontend
    assert "voiceschanged" in frontend
    assert "navigator.serviceWorker.register('/sw.js')" in frontend
    assert 'id="installApp"' in frontend
    assert "beforeinstallprompt" in frontend
    assert 'id="shareAnswer"' in frontend
    assert "navigator.share" in frontend



def test_unified_search_finds_mantra_and_marks_draft_review_status():
    response = client.get("/api/search", params={"q": "Gayatri", "language": "en"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert any(item["type"] == "mantra" and item["id"] == "gayatri-mantra"
               for item in payload["results"])
    assert all(item["review_required"] is True for item in payload["results"])


def test_unified_search_finds_puja_guides_and_knowledge():
    guide = client.get("/api/search", params={"q": "दीप", "language": "hi"})
    knowledge = client.get("/api/search", params={"q": "पञ्चाङ्ग", "language": "sa"})
    assert guide.status_code == knowledge.status_code == 200
    assert any(item["type"] == "puja-guide" for item in guide.json()["results"])
    assert any(item["type"] == "knowledge" for item in knowledge.json()["results"])


def test_unified_search_validates_query_language_and_limit():
    assert client.get("/api/search", params={"q": "   "}).status_code == 422
    assert client.get("/api/search", params={"q": "puja", "language": "fr"}).status_code == 422
    assert client.get("/api/search", params={"q": "puja", "limit": 100}).status_code == 422



def test_frontend_exposes_unified_ecosystem_search():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="globalSearch"' in frontend
    assert "runGlobalSearch" in frontend
    assert "fetch('/api/search?'" in frontend



def test_trust_status_is_transparent_about_beta_and_missing_capabilities():
    response = client.get("/api/trust/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["environment"] == "development"
    assert payload["content_review"]["all_content_is_draft"] is True
    assert payload["content_review"]["status"] == "acharya_review_required"
    assert payload["capabilities"]["panchang_live_calculation"] is False
    assert payload["capabilities"]["kundli_calculation"] is False
    assert payload["production_release_ready"] is False
    assert payload["modules"]["beta"] >= 1



def test_frontend_displays_trust_and_release_status():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="trustStatus"' in frontend
    assert 'id="trustList"' in frontend
    assert "loadTrustStatus();" in frontend
    assert 'id="releaseStatus"' in frontend
    assert 'id="releaseChecklist"' in frontend
    assert "loadReleaseReadiness();" in frontend


def test_runtime_config_rejects_wildcard_origins_in_production():
    from main import validate_runtime_config
    import pytest

    with pytest.raises(ValueError, match="ALLOWED_ORIGINS"):
        validate_runtime_config("production", ["*"], "https://api.example.com/v1", 25)


def test_runtime_config_requires_https_ai_endpoint_in_production():
    from main import validate_runtime_config
    import pytest

    with pytest.raises(ValueError, match="HTTPS"):
        validate_runtime_config("production", ["https://app.example.com"], "http://api.example.com/v1", 25)


def test_runtime_config_rejects_invalid_timeout_and_environment():
    from main import validate_runtime_config
    import pytest

    with pytest.raises(ValueError, match="AI_TIMEOUT_SECONDS"):
        validate_runtime_config("development", ["*"], "https://api.example.com/v1", 0)
    with pytest.raises(ValueError, match="APP_ENV"):
        validate_runtime_config("local", ["*"], "https://api.example.com/v1", 25)


def test_runtime_config_accepts_explicit_production_settings():
    from main import validate_runtime_config

    validate_runtime_config(
        "production", ["https://app.example.com"],
        "https://api.example.com/v1", 25,
    )


def test_jyotish_guide_is_transparent_and_does_not_claim_calculations():
    response = client.get("/api/jyotish/guide")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "integration_blueprint_only"
    assert payload["calculation_available"] is False
    assert {item["id"] for item in payload["required_inputs"]} == {
        "birth_date", "birth_time", "birth_place", "timezone"
    }
    assert "सहमति" in payload["privacy"]


def test_pandit_directory_does_not_fabricate_profiles_or_claim_booking():
    response = client.get("/api/pandits")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "directory_beta_no_booking"
    assert payload["count"] == 0
    assert payload["pandits"] == []
    assert payload["booking_available"] is False


def test_pandit_directory_validates_verification_filter():
    assert client.get("/api/pandits", params={"status": "unverified"}).status_code == 422
    assert client.get("/api/pandits", params={"status": "all"}).status_code == 200


def test_release_readiness_never_claims_beta_is_production_ready():
    response = client.get("/api/release/readiness")
    assert response.status_code == 200
    payload = response.json()
    assert payload["release_status"] == "development_beta_not_production_ready"
    assert payload["production_release_ready"] is False
    assert payload["checks_total"] == 10
    assert "live_panchang_engine" in payload["pending"]
    assert "acharya_content_signoff" in payload["pending"]
    assert "live_hosting_verified" in payload["pending"]


def test_release_readiness_reports_all_check_keys():
    payload = client.get("/api/release/readiness").json()
    assert set(payload["checks"]) == {
        "production_environment", "ai_provider_configured", "explicit_cors_origins",
        "live_panchang_engine", "validated_jyotish_engine", "verified_pandit_booking",
        "payment_gateway", "acharya_content_signoff", "production_voice_service",
        "live_hosting_verified",
    }



def test_privacy_and_terms_pages_are_served_from_app():
    privacy = client.get("/privacy")
    terms = client.get("/terms")
    assert privacy.status_code == terms.status_code == 200
    assert "गोपनीयता सूचना" in privacy.text
    assert "संवेदनशील जानकारी न भेजें" in privacy.text
    assert "उपयोग की शर्तें" in terms.text
    assert "आचार्य" in terms.text


def test_frontend_links_to_privacy_and_terms_pages():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'href="/privacy"' in frontend
    assert 'href="/terms"' in frontend



def test_content_review_policy_defines_source_and_acharya_signoff_workflow():
    response = client.get("/api/content/review-policy")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "workflow_blueprint_only"
    assert payload["approval_enabled"] is False
    assert set(payload["catalogue_counts"]) == {"knowledge", "puja_guides", "samskaras", "mantras"}
    assert all(count is None or count >= 0 for count in payload["catalogue_counts"].values())
    assert {"source_title", "page_or_section", "reviewer_qualification", "reviewed_at"} <= set(payload["required_metadata"])
    assert payload["allowed_decisions"] == ["pending", "approved", "revision_required", "rejected"]
    assert "draft_requires_acharya_review" in payload["publication_rule"]
    assert "admin login" in payload["security_note"]


def test_content_review_policy_is_read_only_and_has_no_public_approval_route():
    response = client.get("/api/content/review-policy")
    assert response.status_code == 200
    assert client.post("/api/content/review-policy", json={"decision": "approved"}).status_code == 405



def test_frontend_has_device_local_sadhana_tracker():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="sadhanaPanel"' in frontend
    assert 'id="sadhanaName"' in frontend
    assert 'id="sadhanaGoal"' in frontend
    assert 'id="sadhanaCount"' in frontend
    assert 'id="sadhanaAdd108"' in frontend
    assert "familyPanditJiSadhanaV1" in frontend
    assert "localStorage.setItem(sadhanaKey" in frontend
    assert "No network requests" in frontend
    assert "दैनिक साधना एवं संकल्प" in frontend



def test_frontend_shows_read_only_acharya_review_policy():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="acharyaReviewPanel"' in frontend
    assert 'id="reviewPolicyStatus"' in frontend
    assert 'id="reviewPolicyList"' in frontend
    assert "loadReviewPolicy();" in frontend
    assert "approval_enabled" in frontend
    assert "केवल read-only blueprint" in frontend


def test_content_review_schema_and_admin_workflow_docs_exist():
    import json
    root = Path(__file__).resolve().parent.parent
    schema = json.loads((root / "schemas" / "content-review.schema.json").read_text(encoding="utf-8"))
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "reviewer_qualification" in schema["required"]
    assert schema["properties"]["decision"]["enum"] == ["pending", "approved", "revision_required", "rejected"]
    workflow = (root / "ADMIN_CONTENT_WORKFLOW.md").read_text(encoding="utf-8")
    assert "no public create, update, approve" in workflow
    assert "author cannot approve own revision" in workflow
    assert "append-only audit" in workflow



def test_sadhana_tracker_allows_user_to_clear_local_data():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="sadhanaClear"' in frontend
    assert "localStorage.removeItem(sadhanaKey)" in frontend
    assert "इस डिवाइस का सेव किया साधना डेटा मिटा दिया गया" in frontend



def test_release_and_trust_endpoints_are_not_cached_or_secret_leaking():
    readiness = client.get("/api/release/readiness")
    trust = client.get("/api/trust/status")
    assert readiness.status_code == trust.status_code == 200
    assert readiness.headers["Cache-Control"] == "no-store"
    assert trust.headers["Cache-Control"] == "no-store"
    serialized = readiness.text + trust.text
    assert "AI_API_KEY" not in serialized
    assert "Bearer " not in serialized


def test_static_privacy_page_has_security_headers():
    response = client.get("/privacy")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"


def test_puja_guides_provide_private_daily_step_checklists():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert "function pujaChecklistKey(id)" in frontend
    assert "function readPujaChecklist(id,count)" in frontend
    assert "function savePujaChecklist(id,values)" in frontend
    assert "familyPanditPuja:" in frontend
    assert "आज की तैयारी:" in frontend
    assert "input.type='checkbox'" in frontend
    assert "localStorage.setItem(pujaChecklistKey(id),JSON.stringify(values))" in frontend
