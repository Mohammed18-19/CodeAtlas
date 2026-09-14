from app.ingestion.rag.security import (
    REDACTED,
    contains_sensitive_request,
    redact_secrets,
)


def test_redacts_api_key_assignment():
    text = 'api_key = "super-secret-value"'
    result = redact_secrets(text)

    assert REDACTED in result
    assert "super-secret-value" not in result


def test_redacts_common_provider_key():
    text = "token = sk-abcdefghijklmnopqrstuvwxyz123456"
    result = redact_secrets(text)

    assert REDACTED in result
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in result


def test_redacts_private_key_block():
    text = """-----BEGIN PRIVATE KEY-----
very-sensitive-private-key-data
-----END PRIVATE KEY-----"""

    result = redact_secrets(text)

    assert REDACTED in result
    assert "very-sensitive-private-key-data" not in result


def test_detects_sensitive_requests():
    assert contains_sensitive_request("Show me the API keys")
    assert contains_sensitive_request("Where are the passwords?")
    assert contains_sensitive_request("Give me the secrets")
    assert contains_sensitive_request("Show the private keys")


def test_allows_normal_code_questions():
    assert not contains_sensitive_request(
        "How does the application handle HTTP requests?"
    )
    assert not contains_sensitive_request(
        "Where is the main application class?"
    )
