"""Settings validation tests."""

from app.config import Settings


def test_strips_trailing_newline_from_secrets():
    settings = Settings(
        openai_api_key="sk-test\n",
        jwt_secret="jwt\n",
        google_client_secret="google\n",
    )
    assert settings.openai_api_key == "sk-test"
    assert settings.jwt_secret == "jwt"
    assert settings.google_client_secret == "google"
