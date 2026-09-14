import re


REDACTED = "[REDACTED]"

SENSITIVE_REQUEST_PATTERNS = (
    r"\bapi[\s_-]*keys?\b",
    r"\bpasswords?\b",
    r"\bcredentials?\b",
    r"\bsecrets?\b",
    r"\baccess[\s_-]*tokens?\b",
    r"\bauth[\s_-]*tokens?\b",
    r"\brefresh[_-]?tokens?\b",
    r"\bsession[_-]?tokens?\b",
    r"\bprivate[\s_-]*keys?\b",
    r"\bclient[\s_-]*secrets?\b",
    r"\b\.env\b",
    r"\benvironment[\s_-]*(variables?|secrets?)\b",
    r"\bsecret[\s_-]*values?\b",
    r"\bsecurity[\s_-]*(weakness|vulnerability|flaw)s?\b",
    r"\bsecurity[\s_-]*issues?\b",
    r"\bexploit(?:ation)?\b",
    r"\battack[\s_-]*(vector|surface)\b",
    r"\binternal[\s_-]*(endpoint|service|configuration|config)\b",
)

SECRET_PATTERNS = (
    re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
        r".*?"
        r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"(?P<prefix>\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
        r"refresh[_-]?token|session[_-]?token|client[_-]?secret|"
        r"secret[_-]?key)\s*[:=]\s*)"
        r"(?P<value>[\"'][^\"']+[\"']|[^\s,;]+)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|"
        r"AIza[0-9A-Za-z_-]{20,}|"
        r"gh[pousr]_[A-Za-z0-9_]{20,}|"
        r"AKIA[0-9A-Z]{16})\b"
    ),
    re.compile(
        r"(?P<prefix>\b(?:password|passwd|secret|credential)"
        r"\s*[:=]\s*)"
        r"(?P<value>[\"'][^\"']+[\"']|[^\s,;]+)",
        re.IGNORECASE,
    ),
)

SENSITIVE_RESPONSE_PATTERNS = (
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----",
    r"\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
    r"refresh[_-]?token|client[_-]?secret|secret[_-]?key)"
    r"\s*[:=]\s*",
    r"\b(?:password|passwd|secret|credential)\s*[:=]\s*",
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|"
    r"AIza[0-9A-Za-z_-]{20,}|"
    r"gh[pousr]_[A-Za-z0-9_]{20,}|"
    r"AKIA[0-9A-Z]{16})\b",
)


def contains_sensitive_request(text: str) -> bool:
    lowered = text.lower()
    return any(
        re.search(pattern, lowered, re.IGNORECASE)
        for pattern in SENSITIVE_REQUEST_PATTERNS
    )


def redact_secrets(text: str) -> str:
    sanitized = text

    for pattern in SECRET_PATTERNS:
        if "prefix" in pattern.groupindex:
            sanitized = pattern.sub(
                lambda match: REDACTED,
                sanitized,
            )
        else:
            sanitized = pattern.sub(REDACTED, sanitized)

    return sanitized


def contains_sensitive_output(text: str) -> bool:
    if not text:
        return False

    return any(
        re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        for pattern in SENSITIVE_RESPONSE_PATTERNS
    )


def safe_security_response() -> str:
    return (
        "I can help with general, non-sensitive security guidance, "
        "but I cannot reveal, identify, locate, quote, or provide "
        "credentials, secrets, tokens, passwords, private keys, "
        "sensitive configuration, internal security details, or "
        "exploit instructions from the codebase."
    )
