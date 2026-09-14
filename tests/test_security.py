from app.ingestion.rag.security import (
    REDACTED,
    contains_sensitive_request,
    redact_secrets,
    contains_sensitive_output,
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


def test_redaction_does_not_preserve_secret_assignment_name():
    text = 'API_KEY = "super-secret-value"'
    result = redact_secrets(text)

    assert "super-secret-value" not in result
    assert "API_KEY" not in result
    assert result == "[REDACTED]"


def test_sensitive_output_is_detected():
    assert contains_sensitive_output(
        'api_key = "super-secret-value"'
    )


def test_private_key_output_is_detected():
    assert contains_sensitive_output(
        "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"
    )


def test_safe_output_is_allowed():
    assert not contains_sensitive_output(
        "The application uses a standard authentication flow."
    )


def test_redacted_context_does_not_expose_location():
    from app.ingestion.rag.context_builder import ContextBuilder

    class FakeFile:
        path = "src/config.py"

    class FakeChunk:
        file = FakeFile()
        start_line = 10
        end_line = 20
        content = "[REDACTED]"

    result = ContextBuilder().build(
        [{"chunk": FakeChunk()}]
    )

    assert "src/config.py" not in result
    assert "10-20" not in result
    assert "Sensitive repository content was removed for security." in result
