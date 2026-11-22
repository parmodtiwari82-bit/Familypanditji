import pytest
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
    assert next(item for item in payload["modules"] if item["id"] == "panchang")["status"] == "beta"

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
    assert payload["capabilities"]["panchang_calculation_api"] is True
    assert payload["capabilities"]["kundli_calculation_api"] is True
    assert payload["capabilities"]["advanced_jyotish_api"] is True
    assert payload["capabilities"]["verified_pandit_booking"] is False
    assert payload["production_release_ready"] is False
    assert payload["release_blockers"]
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


def test_public_pandit_application_stays_private_until_admin_review(monkeypatch, tmp_path):
    import main as backend_main
    backend_main._pandit_application_rate_windows.clear()

    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "applications.sqlite3")
    payload = {
        "display_name": "Pandit Test",
        "contact_phone": "+91 9876543210",
        "city": "Kanpur",
        "state": "Uttar Pradesh",
        "country": "India",
        "service_categories": ["Vivah Puja"],
        "languages": ["Hindi", "Sanskrit"],
        "tradition": "Smarta",
        "biography": "Traditional ritual services.",
        "qualification_summary": "Acharya course",
        "privacy_consent": True,
        "website": "",
    }
    created = client.post("/api/pandit-applications", json=payload)
    assert created.status_code == 201
    assert created.json()["status"] == "pending_review"
    assert created.json()["public_listing"] is False
    assert client.get("/api/pandits").json()["count"] == 0

    token = "test-admin-token-" + "b" * 40
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", token)
    queue = client.get("/api/admin/pandits/pending", headers={"Authorization": f"Bearer {token}"})
    assert queue.status_code == 200
    assert queue.json()["count"] == 1
    private = queue.json()["items"][0]
    assert private["contact_phone"] == payload["contact_phone"]
    assert private["profile_id"] == created.json()["profile_id"]


def test_pandit_application_requires_privacy_consent_and_valid_contact(tmp_path, monkeypatch):
    import main as backend_main
    backend_main._pandit_application_rate_windows.clear()

    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "applications.sqlite3")
    payload = {
        "display_name": "Pandit Test", "contact_phone": "123", "city": "Kanpur",
        "state": "Uttar Pradesh", "service_categories": ["Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "qualification_summary": "Acharya", "privacy_consent": False,
    }
    assert client.post("/api/pandit-applications", json=payload).status_code == 422
    payload["contact_phone"] = "+91 9876543210"
    assert client.post("/api/pandit-applications", json=payload).status_code == 422


def test_pandit_application_rejects_honeypot_submission(monkeypatch, tmp_path):
    import main as backend_main
    backend_main._pandit_application_rate_windows.clear()

    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "applications.sqlite3")
    payload = {
        "display_name": "Pandit Test", "contact_phone": "+91 9876543210", "city": "Kanpur",
        "state": "Uttar Pradesh", "service_categories": ["Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "qualification_summary": "Acharya", "privacy_consent": True,
        "website": "spam",
    }
    assert client.post("/api/pandit-applications", json=payload).status_code == 422


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


@pytest.mark.parametrize("overrides", [
    {"birth_date": "2026-02-30"},
    {"birth_time": "25:61"},
    {"timezone": "Not/A_Real_Timezone"},
    {"latitude": 91},
    {"longitude": 181},
])
def test_kundli_api_rejects_invalid_birth_inputs(overrides):
    payload = {
        "birth_date": "1990-12-10",
        "birth_time": "00:40",
        "latitude": 26.4499,
        "longitude": 80.3319,
        "timezone": "Asia/Kolkata",
        "engine": "approximate",
    }
    payload.update(overrides)
    response = client.post("/api/kundli/calculate", json=payload)
    assert response.status_code == 422


def test_kundli_api_reports_approximate_engine_and_does_not_store_birth_data():
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10",
        "birth_time": "00:40",
        "latitude": 26.4499,
        "longitude": 80.3319,
        "timezone": "Asia/Kolkata",
        "engine": "approximate",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["status"] == "approximate"
    assert payload["data_retention"] == "not_stored_by_this_endpoint"
    assert payload["birth_datetime_local"].startswith("1990-12-10T00:40")
    assert payload["planets"]


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


def test_frontend_has_validated_local_backup_and_restore_controls():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="exportLocalData"' in frontend
    assert 'id="importLocalData"' in frontend
    assert "family-pandit-ji-local-backup" in frontend
    assert "function validateLocalBackup(payload)" in frontend
    assert "file.size>1024*1024" in frontend
    assert "URL.createObjectURL(blob)" in frontend
    assert "loadPujaGuides()" in frontend


def test_operational_readiness_probe_checks_required_assets_and_catalogues():
    response = client.get("/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["ready"] is True
    assert payload["checks_passed"] == payload["checks_total"]
    assert payload["scope"] == "local_application_files_and_catalogue_structure_only"
    assert payload["checks"]["valid_json:data/knowledge_hi.json"] is True
    assert payload["checks"]["valid_json:data/pandit_directory.json"] is True
    assert payload["checks"]["valid_json:data/temples.json"] is True
    assert "production launch" in payload["note_hi"]


def test_operational_readiness_probe_returns_503_when_required_catalogue_is_missing(monkeypatch, tmp_path):
    import main as backend_main
    monkeypatch.setattr(backend_main, "PROJECT_ROOT", tmp_path)
    response = client.get("/ready")
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "not_ready"
    assert payload["ready"] is False
    assert payload["checks"]["data/temples.json"] is False
    assert payload["checks"]["valid_json:data/temples.json"] is False


def test_operational_readiness_probe_rejects_invalid_temple_catalogue(monkeypatch, tmp_path):
    import main as backend_main
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "temples.json").write_text('{"temples": "not-a-list"}', encoding="utf-8")
    monkeypatch.setattr(backend_main, "PROJECT_ROOT", tmp_path)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["valid_json:data/temples.json"] is False


def test_operational_readiness_probe_is_not_cached():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


def test_service_worker_versions_its_cache_and_keeps_api_responses_network_only():
    worker = (Path(__file__).resolve().parent.parent / "sw.js").read_text(encoding="utf-8")
    assert 'const CACHE_NAME = "family-pandit-shell-v4"' in worker
    assert 'const CACHE_PREFIX = "family-pandit-shell-"' in worker
    assert '"/privacy", "/terms"' in worker
    assert 'url.pathname.startsWith("/api/")' in worker
    assert 'url.pathname === "/ready"' in worker
    assert 'key.startsWith(CACHE_PREFIX)' in worker
    assert 'await cache.put(request, copy)' in worker


def test_ask_endpoint_rate_limits_repeated_requests(monkeypatch):
    import main as backend_main

    monkeypatch.setattr(backend_main, "ASK_RATE_LIMIT_MAX", 2)
    monkeypatch.setattr(backend_main, "ASK_RATE_LIMIT_WINDOW_SECONDS", 60)
    backend_main._ask_rate_windows.clear()

    first = client.post("/api/ask", json={"question": "अलग प्रश्न एक", "language": "hi"})
    second = client.post("/api/ask", json={"question": "अलग प्रश्न दो", "language": "hi"})
    blocked = client.post("/api/ask", json={"question": "अलग प्रश्न तीन", "language": "hi"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.headers["Cache-Control"] == "no-store"


def test_ask_rate_limit_does_not_block_other_api_routes(monkeypatch):
    import main as backend_main

    monkeypatch.setattr(backend_main, "ASK_RATE_LIMIT_MAX", 1)
    monkeypatch.setattr(backend_main, "ASK_RATE_LIMIT_WINDOW_SECONDS", 60)
    backend_main._ask_rate_windows.clear()

    first = client.post("/api/ask", json={"question": "पहला प्रश्न", "language": "hi"})
    blocked = client.post("/api/ask", json={"question": "दूसरा प्रश्न", "language": "hi"})
    health = client.get("/health")

    assert first.status_code == 200
    assert blocked.status_code == 429
    assert health.status_code == 200


def test_admin_review_queue_requires_configured_token(monkeypatch):
    import main as backend_main

    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", "")
    response = client.get("/api/admin/review-queue")
    assert response.status_code == 503


def test_admin_review_queue_rejects_missing_or_invalid_token(monkeypatch):
    import main as backend_main

    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", "x" * 40)
    assert client.get("/api/admin/review-queue").status_code == 401
    assert client.get(
        "/api/admin/review-queue",
        headers={"Authorization": "Bearer " + "y" * 40},
    ).status_code == 401


def test_admin_review_queue_lists_drafts_without_approval_mutation(monkeypatch):
    import main as backend_main

    token = "test-admin-token-" + "a" * 40
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", token)
    response = client.get(
        "/api/admin/review-queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["access"] == "authenticated_admin_read_only"
    assert payload["count"] >= 1
    assert all(item["review_status"] == "pending_acharya_review" for item in payload["items"])
    assert payload["write_enabled"] is False
    assert response.headers["Cache-Control"] == "no-store"

def test_acharya_review_submission_records_audit_without_publishing(monkeypatch, tmp_path):
    import main as backend_main
    token = "acharya-test-token-" + "b" * 40
    monkeypatch.setattr(backend_main, "ACHARYA_API_TOKEN", token)
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", "a" * 40)
    monkeypatch.setattr(backend_main, "ACHARYA_REVIEWER_ID", "acharya-test-01")
    monkeypatch.setattr(backend_main, "ACHARYA_REVIEWER_QUALIFICATION", "Test reviewer qualification")
    monkeypatch.setattr(backend_main, "REVIEW_AUDIT_DB", tmp_path / "audit.sqlite3")
    payload = {"content_id":"gayatri-mantra","content_type":"knowledge","decision":"approved","language":"hi","tradition_or_sampradaya":"Test tradition","source_title":"Source title","source_author_or_tradition":"Source author","edition_or_publication":"Test edition","page_or_section":"Chapter 1","review_notes":"Review notes with enough detail."}
    response = client.post("/api/admin/reviews", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["published"] is False
    events = client.get("/api/admin/review-events", headers={"Authorization": "Bearer " + "a" * 40})
    assert events.status_code == 200 and events.json()["count"] == 1


def test_acharya_review_submission_requires_auth_and_pending_content(monkeypatch, tmp_path):
    import main as backend_main
    token = "acharya-test-token-" + "c" * 40
    monkeypatch.setattr(backend_main, "ACHARYA_API_TOKEN", token)
    monkeypatch.setattr(backend_main, "ACHARYA_REVIEWER_ID", "acharya-test-02")
    monkeypatch.setattr(backend_main, "ACHARYA_REVIEWER_QUALIFICATION", "Test reviewer qualification")
    monkeypatch.setattr(backend_main, "REVIEW_AUDIT_DB", tmp_path / "audit.sqlite3")
    payload = {"content_id":"not-found","content_type":"knowledge","decision":"approved","language":"hi","tradition_or_sampradaya":"Tradition","source_title":"Source","source_author_or_tradition":"Author","edition_or_publication":"Edition","page_or_section":"Page 1","review_notes":"Detailed review notes."}
    assert client.post("/api/admin/reviews", json=payload).status_code == 401
    assert client.post("/api/admin/reviews", json=payload, headers={"Authorization": f"Bearer {token}"}).status_code == 404
    assert not (tmp_path / "audit.sqlite3").exists()

def test_free_panchang_calculation_returns_location_specific_limbs():
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.4499,
        "longitude": 80.3319, "timezone_name": "Asia/Kolkata",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["weekday"] == "शनिवार"
    assert data["tithi"] and data["nakshatra"] and data["yoga"] and data["karana"]
    assert data["sunrise"] and data["sunset"]
    assert data["calculation"] == "free_low_precision_astronomical_approximation"
    assert set(data["limb_ends_at"]) == {"tithi", "nakshatra", "yoga", "karana"}
    assert all(data["limb_ends_at"][limb].endswith("+05:30") for limb in data["limb_ends_at"])
    assert "आचार्य" in data["accuracy_note_hi"]


def test_free_panchang_rejects_invalid_date_and_coordinates():
    bad_date = client.get("/api/panchang/calculate", params={
        "date": "not-a-date", "latitude": 26.4, "longitude": 80.3,
    })
    bad_lat = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "latitude": 120, "longitude": 80.3,
    })
    assert bad_date.status_code == 422
    assert bad_lat.status_code == 422


def test_free_kundli_calculation_returns_nine_planets_and_no_storage_claim():
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.4499, "longitude": 80.3319, "timezone": "Asia/Kolkata",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["lagna"]["rashi"]
    assert len(data["planets"]) == 9
    assert data["data_retention"] == "not_stored_by_this_endpoint"
    assert data["calculation"] == "free_low_precision_orbital_approximation"
    assert data["house_system"] == "whole_sign_from_approximate_ascendant"


def test_free_kundli_rejects_invalid_birth_input():
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "10/12/1990", "birth_time": "25:61",
        "latitude": 26.4, "longitude": 80.3, "timezone": "Asia/Kolkata",
    })
    assert response.status_code == 422


def test_frontend_exposes_free_panchang_and_kundli_forms_without_geolocation():
    html = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    for control in ("panchangForm", "pDate", "pLat", "pLon", "kundliForm", "kDate", "kTime", "kLat", "kLon"):
        assert control in html
    assert "/api/panchang/calculate?" in html
    assert "/api/kundli/calculate" in html
    assert "geolocation" not in html.lower()


def test_advanced_jyotish_returns_d9_and_birth_anchored_vimshottari_without_storage():
    response = client.post("/api/jyotish/advanced", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.4499, "longitude": 80.3319, "timezone": "Asia/Kolkata"
    })
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["navamsa_d9"]) == 10  # nine grahas plus Lagna
    assert len(payload["vimshottari"]["mahadasha_periods"]) == 9
    assert payload["vimshottari"]["birth_period"] == payload["vimshottari"]["mahadasha_periods"][0]["lord"]
    assert payload["data_retention"] == "not_stored_by_this_endpoint"
    assert "निम्न-सटीकता" in payload["accuracy_note_hi"]


def test_advanced_jyotish_rejects_invalid_timezone_and_coordinates():
    bad_timezone = client.post("/api/jyotish/advanced", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.4, "longitude": 80.3, "timezone": "Mars/Olympus"
    })
    assert bad_timezone.status_code == 422
    bad_coordinates = client.post("/api/jyotish/advanced", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 96, "longitude": 80.3, "timezone": "Asia/Kolkata"
    })
    assert bad_coordinates.status_code == 422


def test_frontend_exposes_advanced_jyotish_calculator():
    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    assert 'id="advancedJyotishButton"' in html
    assert "/api/jyotish/advanced" in html
    assert "D9 नवांश" in html



def test_advanced_jyotish_returns_supported_divisional_charts():
    response = client.post("/api/jyotish/advanced", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.4499, "longitude": 80.3319, "timezone": "Asia/Kolkata"
    })
    assert response.status_code == 200
    payload = response.json()
    charts = payload["divisional_charts"]
    assert set(charts) == {"d2_hora", "d3_drekkana", "d7_saptamsa", "d10_dashamsa", "d12_dwadasamsa"}
    for chart in charts.values():
        assert len(chart) == 10  # nine grahas plus Lagna
        assert all(item["rashi"] for item in chart.values())
        assert all(0 <= item["source_longitude_degrees"] < 360 for item in chart.values())


def test_divisional_sign_known_parashari_boundaries():
    from advanced_jyotish import divisional_sign
    # First/second Hora in an odd sign: Leo/Cancer; in an even sign: Cancer/Leo.
    assert divisional_sign(1.0, 2, "hora") == "सिंह"
    assert divisional_sign(16.0, 2, "hora") == "कर्क"
    assert divisional_sign(31.0, 2, "hora") == "कर्क"
    assert divisional_sign(46.0, 2, "hora") == "सिंह"
    # Drekkana starts from the sign itself, fifth and ninth signs.
    assert divisional_sign(1.0, 3, "drekkana") == "मेष"
    assert divisional_sign(11.0, 3, "drekkana") == "सिंह"
    assert divisional_sign(21.0, 3, "drekkana") == "धनु"


def test_divisional_sign_supports_seven_and_ten_part_vargas():
    from advanced_jyotish import divisional_sign
    # D7: odd signs start from the same sign; even signs from the seventh.
    assert divisional_sign(1.0, 7, "saptamsa") == "मेष"
    assert divisional_sign(31.0, 7, "saptamsa") == "वृश्चिक"
    # D10: odd signs start from the same sign; even signs from the ninth.
    assert divisional_sign(1.0, 10, "dashamsa") == "मेष"
    assert divisional_sign(31.0, 10, "dashamsa") == "मकर"
    # D12 starts from the natal sign for both odd and even signs.
    assert divisional_sign(1.0, 12, "dwadasamsa") == "मेष"
    assert divisional_sign(31.0, 12, "dwadasamsa") == "वृषभ"


def test_divisional_sign_normalizes_longitude_and_rejects_unknown_method():
    from advanced_jyotish import divisional_sign
    assert divisional_sign(361.0, 3, "drekkana") == divisional_sign(1.0, 3, "drekkana")
    import pytest
    with pytest.raises(ValueError):
        divisional_sign(10.0, 3, "unknown")


def test_advanced_jyotish_ui_lists_all_supported_vargas():
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    for label in ("D2 होरा", "D3 द्रेष्काण", "D7 सप्तांश", "D9 नवांश", "D10 दशांश", "D12 द्वादशांश"):
        assert label in html
    assert "data.divisional_charts" in html


def test_astronomy_status_discloses_optional_ephemeris_and_limits():
    payload = client.get("/api/astronomy/status").json()
    assert payload["request_downloads_ephemeris"] is False
    assert payload["certified_vedic_engine"] is False
    assert payload["supported_years"] == [1849, 2150]
    assert "approximate Lahiri ayanamsa" in payload["limitations"]


def test_panchang_explicit_approximate_engine_is_reported():
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "approximate",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["id"] == "free_approximate"
    assert payload["transition_times_status"] == "estimated_low_precision"


def test_kundli_auto_engine_falls_back_transparently_when_ephemeris_absent(monkeypatch, tmp_path):
    import main
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", tmp_path / "missing-de440s.bsp")
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.45, "longitude": 80.33, "timezone": "Asia/Kolkata",
    })
    assert response.status_code == 200
    assert response.json()["engine"]["id"] == "free_approximate"


def test_explicit_jpl_mode_fails_closed_when_ephemeris_file_is_missing(monkeypatch, tmp_path):
    import main
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", tmp_path / "missing-de440s.bsp")
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.45, "longitude": 80.33, "timezone": "Asia/Kolkata",
        "engine": "jpl",
    })
    assert response.status_code == 503
    assert "JPL engine unavailable" in response.json()["detail"]


def test_jpl_mode_uses_injected_ephemeris_positions_and_labels_remaining_approximations(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(main, "calculate_tropical_longitudes", lambda moment, path: {
        "Sun": 10.0, "Moon": 20.0, "Mercury": 30.0, "Venus": 40.0,
        "Mars": 50.0, "Jupiter": 60.0, "Saturn": 70.0,
    })
    monkeypatch.setattr(main, "calculate_tropical_ascendant", lambda moment, lat, lon, path: 123.4)
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.45, "longitude": 80.33, "timezone": "Asia/Kolkata",
        "engine": "jpl",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["id"] == "jpl_de440s_skyfield"
    assert payload["engine"]["ayanamsa"] == "approximate_Lahiri"
    assert payload["ascendant_calculation"] == "Skyfield_apparent_GMST_plus_approximate_obliquity"
    assert payload["house_system"] == "whole_sign_from_skyfield_apparent_sidereal_time_approximate_obliquity"
    assert payload["planets"]["Sun"]["longitude_degrees"] != 10.0
    assert "lagna_and_houses" in payload["engine"]


def test_jpl_panchang_does_not_present_approximate_transition_times_as_jpl(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(main, "calculate_sunrise_sunset", lambda moment, lat, lon, path: {"sunrise": "2026-11-21T06:18:00+05:30", "sunset": "2026-11-21T17:12:00+05:30"})
    monkeypatch.setattr(main, "calculate_panchang_limb_transitions", lambda moment, path: {"tithi": "2026-11-21T19:14:00+05:30", "nakshatra": "2026-11-22T02:11:00+05:30", "yoga": "2026-11-22T04:10:00+05:30", "karana": "2026-11-21T16:10:00+05:30"})
    monkeypatch.setattr(main, "calculate_tropical_longitudes", lambda moment, path: {
        "Sun": 10.0, "Moon": 20.0, "Mercury": 30.0, "Venus": 40.0,
        "Mars": 50.0, "Jupiter": 60.0, "Saturn": 70.0,
    })
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "jpl",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["id"] == "jpl_de440s_skyfield"
    assert payload["limb_ends_at"]["tithi"] == "2026-11-21T19:14:00+05:30"
    assert set(payload["limb_ends_at"]) == {"tithi", "nakshatra", "yoga", "karana"}
    assert payload["transition_times_status"] == "jpl_de440s_with_approximate_lahiri_conventions"


def test_birth_chart_rejects_unknown_engine():
    response = client.post("/api/kundli/calculate", json={
        "birth_date": "1990-12-10", "birth_time": "00:40",
        "latitude": 26.45, "longitude": 80.33, "timezone": "Asia/Kolkata",
        "engine": "magic-precision",
    })
    assert response.status_code == 422


def test_frontend_exposes_engine_selection_and_displays_provenance():
    frontend = (Path(__file__).resolve().parent.parent / "index.html").read_text(encoding="utf-8")
    assert 'id="pEngine"' in frontend
    assert 'id="kEngine"' in frontend
    assert "engine:document.getElementById('pEngine').value" in frontend
    assert "engine:document.getElementById('kEngine').value" in frontend
    assert "data.engine?.note_hi" in frontend
    assert "data.transition_times_status" in frontend


def test_jpl_panchang_uses_ephemeris_sunrise_sunset_and_reports_horizon_limit(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(main, "calculate_tropical_longitudes", lambda moment, path: {
        "Sun": 10.0, "Moon": 20.0, "Mercury": 30.0, "Venus": 40.0,
        "Mars": 50.0, "Jupiter": 60.0, "Saturn": 70.0,
    })
    monkeypatch.setattr(main, "calculate_sunrise_sunset", lambda moment, lat, lon, path: {
        "sunrise": "2026-11-21T06:18:00+05:30", "sunset": "2026-11-21T17:12:00+05:30",
    })
    monkeypatch.setattr(main, "calculate_panchang_limb_transitions", lambda moment, path: {
        "tithi": "2026-11-21T19:14:00+05:30", "nakshatra": "2026-11-22T02:11:00+05:30",
        "yoga": "2026-11-22T04:10:00+05:30", "karana": "2026-11-21T16:10:00+05:30",
    })
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "jpl",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["sunrise"] == "2026-11-21T06:18:00+05:30"
    assert payload["sunset"] == "2026-11-21T17:12:00+05:30"
    assert payload["sunrise_sunset_status"] == "jpl_de440s_standard_horizon"
    assert "standard unobstructed horizon; local terrain/buildings are not modeled" in payload["engine"]["limitations"]


def test_astronomy_status_reports_both_jpl_prerequisites(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: None)
    payload = client.get("/api/astronomy/status").json()
    assert payload["jpl_ephemeris_configured"] is True
    assert payload["skyfield_installed"] is False
    assert payload["jpl_ready"] is False
    assert "Skyfield dependency missing" in payload["jpl_unavailable_reasons"]


def test_auto_engine_falls_back_if_ephemeris_exists_but_skyfield_is_missing(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: None)
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "auto",
    })
    assert response.status_code == 200
    assert response.json()["engine"]["id"] == "free_approximate"
    assert "Skyfield dependency" in response.json()["engine"]["fallback_reason"]


def test_explicit_jpl_mode_fails_clearly_when_skyfield_is_missing(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: None)
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "jpl",
    })
    assert response.status_code == 503
    assert "install backend/requirements-astronomy.txt" in response.json()["detail"]


def test_trust_status_reports_implemented_calculation_apis_and_remaining_release_blockers():
    response = client.get("/api/trust/status")
    assert response.status_code == 200
    payload = response.json()
    capabilities = payload["capabilities"]
    assert capabilities["panchang_calculation_api"] is True
    assert capabilities["kundli_calculation_api"] is True
    assert capabilities["advanced_jyotish_api"] is True
    assert set(capabilities["divisional_charts"]) == {"D2", "D3", "D7", "D9", "D10", "D12"}
    assert set(capabilities["vimshottari_periods"]) == {"mahadasha", "antardasha", "pratyantardasha"}
    assert capabilities["pandit_directory_discovery_api"] is True
    assert capabilities["verified_pandit_booking"] is False
    assert payload["production_release_ready"] is False
    assert payload["release_blockers"]


def test_module_catalogue_does_not_claim_unimplemented_muhurta_or_certified_jyotish():
    payload = client.get("/api/modules").json()
    modules = {item["id"]: item for item in payload["modules"]}
    assert "optional JPL DE440s" in modules["panchang"]["description"]
    assert "D2/D3/D7/D9/D10/D12" in modules["jyotish"]["description"]
    assert modules["pandit-directory"]["status"] == "planned"


def test_public_pandit_directory_returns_no_unverified_profiles(monkeypatch, tmp_path):
    import main
    monkeypatch.setattr(main, "PANDIT_DIRECTORY_DB", tmp_path / "pandits.sqlite3")
    response = client.get("/api/pandits")
    assert response.status_code == 200
    assert response.json()["status"] == "directory_beta_no_booking"
    assert response.json()["items"] == []
    assert response.json()["pandits"] == []
    assert response.json()["booking_enabled"] is False


def test_admin_pandit_review_lifecycle_only_publishes_verified_profiles(monkeypatch, tmp_path):
    import main
    token = "pandit-directory-admin-" + "p" * 40
    monkeypatch.setattr(main, "ADMIN_API_TOKEN", token)
    monkeypatch.setattr(main, "PANDIT_DIRECTORY_DB", tmp_path / "pandits.sqlite3")
    headers = {"Authorization": f"Bearer {token}"}
    profile = {
        "display_name": "Acharya Example", "city": "Kanpur", "state": "Uttar Pradesh",
        "country": "India", "service_categories": ["Vivah Puja", "Griha Pravesh"],
        "languages": ["Hindi", "Sanskrit"], "tradition": "Smarta",
        "biography": "Profile biography for directory testing.",
        "qualification_summary": "Traditional Vedic studies",
    }
    created = client.post("/api/admin/pandits", json=profile, headers=headers)
    assert created.status_code == 201
    profile_id = created.json()["profile_id"]
    assert created.json()["status"] == "pending_review"
    assert client.get("/api/pandits?city=Kanpur").json()["items"] == []

    review = {
        "reviewer_name": "Platform reviewer",
        "reviewer_qualification": "Reviewer qualification record",
        "verification_method": "document_review",
        "evidence_reference": "secure-evidence-ref-001",
        "review_notes": "Identity and qualification documents checked against the submitted profile.",
    }
    verified = client.post(f"/api/admin/pandits/{profile_id}/verify", json=review, headers=headers)
    assert verified.status_code == 200
    assert verified.json()["verification_scope"] == "platform_reviewed_profile"
    public = client.get("/api/pandits?city=kanpur&service=Vivah%20Puja&language=Hindi")
    assert public.status_code == 200
    assert public.json()["count"] == 1
    item = public.json()["items"][0]
    assert item["display_name"] == "Acharya Example"
    assert item["directory_status"] == "platform_reviewed_profile"
    assert "government certification" in item["verification_scope"]
    assert "evidence_reference" not in item
    assert "verifier_name" not in item
    assert public.json()["booking_enabled"] is False

    suspended = client.post(
        f"/api/admin/pandits/{profile_id}/suspend",
        json={"reason": "Profile is suspended pending a complaint review."}, headers=headers,
    )
    assert suspended.status_code == 200
    assert client.get("/api/pandits?city=Kanpur").json()["items"] == []


def test_pandit_directory_admin_endpoints_require_admin_token(monkeypatch, tmp_path):
    import main
    monkeypatch.setattr(main, "PANDIT_DIRECTORY_DB", tmp_path / "pandits.sqlite3")
    monkeypatch.setattr(main, "ADMIN_API_TOKEN", "x" * 40)
    response = client.post("/api/admin/pandits", json={
        "display_name": "Acharya Example", "city": "Kanpur", "state": "Uttar Pradesh",
        "service_categories": ["Vivah Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "qualification_summary": "Vedic studies",
    })
    assert response.status_code == 401
    assert client.get("/api/admin/pandits/not-a-profile/status").status_code == 401


def test_pandit_directory_rejects_incomplete_verification_evidence(monkeypatch, tmp_path):
    import main
    token = "pandit-directory-admin-" + "q" * 40
    monkeypatch.setattr(main, "ADMIN_API_TOKEN", token)
    monkeypatch.setattr(main, "PANDIT_DIRECTORY_DB", tmp_path / "pandits.sqlite3")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/admin/pandits", json={
        "display_name": "Acharya Example", "city": "Lucknow", "state": "Uttar Pradesh",
        "service_categories": ["Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "qualification_summary": "Vedic studies",
    }, headers=headers)
    profile_id = created.json()["profile_id"]
    invalid = client.post(f"/api/admin/pandits/{profile_id}/verify", json={
        "reviewer_name": "Reviewer", "reviewer_qualification": "Qualified reviewer",
        "verification_method": "guess", "evidence_reference": "x", "review_notes": "too short",
    }, headers=headers)
    assert invalid.status_code == 422
    assert client.get("/api/pandits").json()["items"] == []


def test_public_pandit_directory_only_accepts_verified_status_filter():
    assert client.get("/api/pandits", params={"status": "unverified"}).status_code == 422
    assert client.get("/api/pandits", params={"status": "verified"}).status_code == 200
    assert client.get("/api/pandits", params={"status": "all"}).status_code == 200


def test_frontend_exposes_verified_only_pandit_directory_search_without_booking_controls():
    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    for control in ("panditDirectory", "panditCity", "panditService", "panditLanguage", "panditSearchButton", "panditDirectoryResults"):
        assert control in html
    assert "/api/pandits?" in html
    assert "booking_available!==false" in html
    assert "कोई live verified पंडित प्रोफ़ाइल उपलब्ध नहीं है" in html


def test_jpl_panchang_reports_transition_provenance_and_all_four_limbs(monkeypatch, tmp_path):
    import main
    ephemeris = tmp_path / "de440s.bsp"
    ephemeris.write_bytes(b"stub")
    monkeypatch.setattr(main, "JPL_EPHEMERIS_PATH", ephemeris)
    monkeypatch.setattr(main.importlib.util, "find_spec", lambda name: object())
    monkeypatch.setattr(main, "calculate_tropical_longitudes", lambda moment, path: {
        "Sun": 10.0, "Moon": 20.0, "Mercury": 30.0, "Venus": 40.0,
        "Mars": 50.0, "Jupiter": 60.0, "Saturn": 70.0,
    })
    monkeypatch.setattr(main, "calculate_sunrise_sunset", lambda *args: {"sunrise": None, "sunset": None})
    monkeypatch.setattr(main, "calculate_panchang_limb_transitions", lambda *args: {
        "tithi": "2026-11-21T19:14:00+05:30", "nakshatra": None, "yoga": None, "karana": None,
    })
    response = client.get("/api/panchang/calculate", params={
        "date": "2026-11-21", "time": "12:00", "latitude": 26.45,
        "longitude": 80.33, "timezone_name": "Asia/Kolkata", "engine": "jpl",
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["transition_times_status"] == "jpl_de440s_with_approximate_lahiri_conventions"
    assert payload["limb_ends_at"]["tithi"].endswith("+05:30")
    assert payload["limb_ends_at"]["nakshatra"] is None


def test_temple_directory_returns_curated_official_source_records():
    response = client.get("/api/temples")
    assert response.status_code == 200
    payload = response.json()
    assert payload["official_source_only"] is True
    assert payload["count"] >= 5
    for temple in payload["temples"]:
        assert temple["official_website"].startswith("https://")
        assert temple["official_information_url"].startswith("https://")
        assert temple["source_status"].startswith("official_")
        assert temple["last_checked_on"] == "2026-11-21"


def test_temple_detail_returns_source_provenance_and_pilgrimage_circuit():
    response = client.get("/api/temples/kedarnath-dham-uttarakhand")
    assert response.status_code == 200
    payload = response.json()
    assert payload["temple"]["id"] == "kedarnath-dham-uttarakhand"
    assert payload["temple"]["pilgrimage_circuit"] == "Uttarakhand Char Dham"
    assert "Dwadasha Jyotirlinga" in payload["temple"]["pilgrimage_circuits"]
    assert payload["temple"]["source_status"] == "official_uttarakhand_tourism_government_portal"
    assert payload["notice_hi"]
    assert payload["last_catalogue_reviewed"] == "2026-11-21"


def test_temple_detail_returns_404_for_unknown_id():
    assert client.get("/api/temples/not-a-real-temple").status_code == 404


def test_temple_directory_includes_all_twelve_dwadasha_jyotirlingas():
    response = client.get("/api/temples")
    assert response.status_code == 200
    jyotirlingas = [item for item in response.json()["temples"]
                    if "Dwadasha Jyotirlinga" in item.get("pilgrimage_circuits", [])]
    assert len(jyotirlingas) == 12
    assert len({item["id"] for item in jyotirlingas}) == 12
    assert all(item["deity"] == "भगवान शिव" for item in jyotirlingas)
    assert all(item["official_website"].startswith("https://") for item in jyotirlingas)
    assert all(item["official_information_url"].startswith("https://") for item in jyotirlingas)
    assert all(item["source_status"].startswith("official_") for item in jyotirlingas)
    assert {item["id"] for item in jyotirlingas} >= {
        "somnath-gujarat", "mallikarjuna-srisailam", "mahakaleshwar-ujjain",
        "omkareshwar-madhya-pradesh", "kedarnath-dham-uttarakhand",
        "bhimashankar-maharashtra", "kashi-vishwanath-varanasi",
        "trimbakeshwar-maharashtra", "vaidyanath-deoghar", "nageshwar-dwarka",
        "ramanathaswamy-rameswaram", "grishneshwar-verul",
    }


def test_temple_directory_includes_four_uttarakhand_char_dham_with_government_sources():
    response = client.get("/api/temples", params={"state": "Uttarakhand"})
    assert response.status_code == 200
    temples = response.json()["temples"]
    assert {item["id"] for item in temples} == {
        "yamunotri-dham-uttarakhand", "gangotri-dham-uttarakhand",
        "kedarnath-dham-uttarakhand", "badrinath-dham-uttarakhand",
    }
    assert all(item["source_status"] == "official_uttarakhand_tourism_government_portal" for item in temples)
    assert all(item["official_website"] == "https://registrationandtouristcare.uk.gov.in/" for item in temples)
    assert all(item["pilgrimage_circuit"] == "Uttarakhand Char Dham" for item in temples)


def test_temple_directory_filters_by_city_state_and_deity():
    city = client.get("/api/temples", params={"q": "Varanasi"})
    assert city.status_code == 200
    assert [item["id"] for item in city.json()["temples"]] == ["kashi-vishwanath-varanasi"]
    state = client.get("/api/temples", params={"state": "Gujarat"})
    assert {item["id"] for item in state.json()["temples"]} >= {"somnath-gujarat", "nageshwar-dwarka"}
    deity = client.get("/api/temples", params={"deity": "भगवान शिव"})
    assert deity.json()["count"] >= 3


def test_temple_directory_frontend_has_search_and_official_link_safety():
    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    for control in ("templeDirectory", "templeQuery", "templeState", "templeDeity", "templeSearchButton", "templeDirectoryResults"):
        assert control in html
    assert "/api/temples?" in html
    assert "parsed.protocol!=='https:'" in html
    assert "noopener noreferrer" in html



def test_puja_guide_detail_returns_one_draft_with_review_notice():
    response = client.get("/api/puja-guides/daily-puja")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert payload["guide"]["id"] == "daily-puja"
    assert payload["guide"]["review_required"] is True
    assert len(payload["guide"]["steps_hi"]) >= 1


def test_puja_guide_detail_returns_404_for_unknown_id():
    assert client.get("/api/puja-guides/not-a-real-guide").status_code == 404


def test_samskara_detail_returns_one_entry_with_review_notice():
    response = client.get("/api/samskaras/vivaha")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "draft_requires_acharya_review"
    assert payload["samskara"]["id"] == "vivaha"
    assert payload["samskara"]["review_required"] is True


def test_samskara_detail_returns_404_for_unknown_id():
    assert client.get("/api/samskaras/not-a-real-samskara").status_code == 404



def test_frontend_uses_individual_puja_and_samskara_detail_endpoints():
    html = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")
    assert "'/api/puja-guides/'+encodeURIComponent(item.id)" in html
    assert "'/api/samskaras/'+encodeURIComponent(item.id)" in html
    assert "विस्तृत जानकारी खोलें" in html
    assert "aria-live" in html


def test_admin_can_reject_pending_pandit_application_without_publication(monkeypatch, tmp_path):
    import main as backend_main
    backend_main._pandit_application_rate_windows.clear()
    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "applications.sqlite3")
    token = "test-admin-token-" + "r" * 40
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", token)
    payload = {
        "display_name": "Pandit Reject Test", "contact_phone": "+91 9876543210",
        "city": "Kanpur", "state": "Uttar Pradesh", "country": "India",
        "service_categories": ["Vivah Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "biography": "Traditional ritual services.",
        "qualification_summary": "Acharya course", "privacy_consent": True, "website": "",
    }
    created = client.post("/api/pandit-applications", json=payload)
    assert created.status_code == 201
    profile_id = created.json()["profile_id"]
    rejected = client.post(
        f"/api/admin/pandits/{profile_id}/reject",
        json={"reason": "Submitted qualification details need clarification."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert client.get("/api/admin/pandits/pending", headers={"Authorization": f"Bearer {token}"}).json()["count"] == 0
    assert client.get("/api/admin/pandits").status_code == 405
    status = client.get(f"/api/admin/pandits/{profile_id}/status", headers={"Authorization": f"Bearer {token}"})
    assert status.status_code == 200
    assert status.json()["status"] == "rejected"
    assert client.post(
        f"/api/admin/pandits/{profile_id}/reject",
        json={"reason": "Second attempt should not change decision."},
        headers={"Authorization": f"Bearer {token}"},
    ).status_code == 404



def test_admin_can_erase_pending_or_rejected_application_only_with_confirmation(monkeypatch, tmp_path):
    import main as backend_main
    backend_main._pandit_application_rate_windows.clear()
    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "erase.sqlite3")
    token = "test-admin-token-" + "e" * 40
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", token)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "display_name": "Pandit Erase Test", "contact_phone": "+91 9876543210",
        "city": "Kanpur", "state": "Uttar Pradesh", "country": "India",
        "service_categories": ["Vivah Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "biography": "Traditional ritual services.",
        "qualification_summary": "Acharya course", "privacy_consent": True, "website": "",
    }
    created = client.post("/api/pandit-applications", json=payload)
    assert created.status_code == 201
    profile_id = created.json()["profile_id"]
    no_confirm = client.post(f"/api/admin/pandits/{profile_id}/erase",
                             json={"reason": "Retention period ended.", "confirm_delete": False}, headers=headers)
    assert no_confirm.status_code == 422
    unauthorized = client.post(f"/api/admin/pandits/{profile_id}/erase",
                               json={"reason": "Retention period ended.", "confirm_delete": True})
    assert unauthorized.status_code == 401
    erased = client.post(f"/api/admin/pandits/{profile_id}/erase",
                         json={"reason": "Retention period ended.", "confirm_delete": True}, headers=headers)
    assert erased.status_code == 200
    assert erased.json()["status"] == "erased"
    assert client.get(f"/api/admin/pandits/{profile_id}/status", headers=headers).status_code == 404


def test_admin_cannot_erase_verified_pandit_profile(monkeypatch, tmp_path):
    import main as backend_main
    monkeypatch.setattr(backend_main, "PANDIT_DIRECTORY_DB", tmp_path / "verified-erase.sqlite3")
    token = "test-admin-token-" + "v" * 40
    monkeypatch.setattr(backend_main, "ADMIN_API_TOKEN", token)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/admin/pandits", json={
        "display_name": "Verified Pandit", "city": "Kanpur", "state": "Uttar Pradesh",
        "service_categories": ["Puja"], "languages": ["Hindi"],
        "tradition": "Smarta", "qualification_summary": "Vedic studies",
    }, headers=headers)
    profile_id = created.json()["profile_id"]
    verified = client.post(f"/api/admin/pandits/{profile_id}/verify", json={
        "reviewer_name": "Reviewer", "reviewer_qualification": "Qualified acharya",
        "verification_method": "in_person", "evidence_reference": "review-record-123",
        "review_notes": "Identity and qualifications checked in person.",
    }, headers=headers)
    assert verified.status_code == 200
    denied = client.post(f"/api/admin/pandits/{profile_id}/erase",
                         json={"reason": "Request to delete record.", "confirm_delete": True}, headers=headers)
    assert denied.status_code == 404
    assert client.get("/api/pandits").json()["count"] == 1



def test_pandit_application_privacy_copy_discloses_manual_erasure_and_no_retention_schedule():
    root = Path(__file__).resolve().parents[1]
    privacy = (root / "privacy.html").read_text(encoding="utf-8")
    home = (root / "index.html").read_text(encoding="utf-8")
    assert "automatic retention scheduler" in privacy
    assert "manually erase" in privacy
    assert "Backup, hosting logs" in privacy
    assert "निश्चित retention अवधि और applicant self-service deletion अभी उपलब्ध नहीं हैं" in home
    assert "सुरक्षित रूप से रखे जाएँ" not in home



def test_jpl_kundli_and_advanced_endpoints_wire_ephemeris_and_ascendant(monkeypatch):
    """Exercise both API routes with deterministic JPL adapter outputs."""
    import main as backend_main

    tropical = {
        "Sun": 280.0, "Moon": 100.0, "Mercury": 275.0,
        "Venus": 300.0, "Mars": 210.0, "Jupiter": 190.0, "Saturn": 200.0,
    }
    engine_info = {
        "id": "jpl_de440s_skyfield",
        "status": "jpl_de440s_skyfield",
        "precision": "JPL DE440s test fixture",
    }
    monkeypatch.setattr(
        backend_main, "resolve_astronomy_engine",
        lambda moment, requested: (dict(tropical), dict(engine_info)),
    )
    monkeypatch.setattr(
        backend_main, "resolve_ascendant",
        lambda moment, latitude, longitude, info: 45.0,
    )
    payload = {
        "birth_date": "2001-04-15",
        "birth_time": "06:20",
        "latitude": 26.4499,
        "longitude": 80.3319,
        "timezone": "Asia/Kolkata",
        "engine": "jpl",
    }

    chart_response = client.post("/api/kundli/calculate", json=payload)
    assert chart_response.status_code == 200
    chart = chart_response.json()
    assert chart["engine"]["id"] == "jpl_de440s_skyfield"
    assert chart["ascendant_calculation"] == "Skyfield_apparent_GMST_plus_approximate_obliquity"
    assert chart["lagna"]["longitude_degrees"] != 45.0
    assert {"Sun", "Moon", "Rahu", "Ketu"} <= set(chart["planets"])
    assert len(chart["houses"]) == 12
    assert [house["number"] for house in chart["houses"]] == list(range(1, 13))
    assert sum(len(house["planets"]) for house in chart["houses"]) == len(chart["planets"])
    for planet in chart["planets"].values():
        assert 1 <= planet["house"] <= 12

    advanced_response = client.post("/api/jyotish/advanced", json=payload)
    assert advanced_response.status_code == 200
    advanced = advanced_response.json()
    assert advanced["engine"]["id"] == "jpl_de440s_skyfield"
    assert advanced["lagna"] == chart["lagna"]
    assert {"Sun", "Moon", "Rahu", "Ketu"} <= set(advanced["navamsa_d9"])
    assert advanced["vimshottari"]["mahadasha_periods"]
    assert advanced["data_retention"] == "not_stored_by_this_endpoint"
