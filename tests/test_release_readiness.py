from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_release_readiness_never_self_certifies_beta_as_production():
    response = client.get("/api/release/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["release_status"] == "development_beta_not_production_ready"
    assert payload["production_release_ready"] is False
    assert payload["checks_total"] == len(payload["checks"])
    assert payload["checks_passed"] == sum(payload["checks"].values())
    assert payload["pending"]
    assert payload["checks"]["production_environment"] is False
    assert payload["checks"]["live_panchang_engine"] is False
    assert payload["checks"]["validated_jyotish_engine"] is False
    assert payload["checks"]["acharya_content_signoff"] is False
    assert payload["checks"]["live_hosting_verified"] is False


def test_local_readiness_probe_is_separate_from_production_release_gate():
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["status"] == "ready"
    assert payload["scope"] == "local_application_files_and_catalogue_structure_only"
    assert "production launch" in payload["note_hi"]
