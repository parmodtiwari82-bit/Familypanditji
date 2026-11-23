"""Guardrails for the Render Blueprint: it must remain a non-production staging service."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_render_blueprint_is_explicitly_staging_only():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")

    assert "name: family-panditji-staging" in blueprint
    assert "plan: free" in blueprint
    assert "branch: main" in blueprint
    assert "healthCheckPath: /health" in blueprint
    assert "key: APP_ENV\n        value: staging" in blueprint


def test_render_blueprint_does_not_enable_production_or_embed_secrets():
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")

    # Wildcard CORS is tolerated only because this blueprint is explicitly
    # staging; production configuration must use exact HTTPS origins.
    assert 'key: ALLOWED_ORIGINS\n        value: "*"' in blueprint
    assert "value: production" not in blueprint
    assert "AI_API_KEY" not in blueprint
    assert "ADMIN_API_TOKEN" not in blueprint
    assert "ACHARYA_API_TOKEN" not in blueprint
