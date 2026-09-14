import re


REDACTED = "[REDACTED]"

SENSITIVE_REQUEST_PATTERNS = (
    r"\bapi[\s_-]*keys?\b",
    r"\bpasswords?\b",
    r"\bcredentials?\b",
    r"\bsecrets?\b",
    r"\baccess[\s_-]*tokens?\b",
    r"\bprivate[\s_-]*keys?\b",
    r"\bauth[\s_-]*tokens?\b",
    r"\brefresh[\s_-]*tokens?\b",
    r"\bsession[\s_-]*tokens?\b",
    r"\b\.env\b",
    r"\bsecret[\s_-]*values?\b",
    r"\bsecurity[\s_-]*(weakness|vulnerability|flaw)s?\b",
    r"\bexploit(?:ation)?\b",
)

SECRET_PATTERNS = (
    # Private keys
    re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"
        r".*?"
        r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
        re.IGNORECASE | re.DOTALL,
    ),

    # Common API-token assignments
    re.compile(
        r"(?P<prefix>\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
        r"refresh[_-]?token|client[_-]?secret|secret[_-]?key)"
        r"\s*[:=]\s*)(?P<value>[\"'][^\"']+[\"']|[^\s,;]+)",
        re.IGNORECASE,
    ),

    # Common cloud/provider keys
    re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|"
        r"AIza[0-9A-Za-z_-]{20,}|"
        r"gh[pousr]_[A-Za-z0-9_]{20,}|"
        r"AKIA[0-9A-Z]{16})\b"
    ),

    # Generic secret/password assignments
    re.compile(
        r"(?P<prefix>\b(?:password|passwd|secret|credential)"
        r"\s*[:=]\s*)(?P<value>[\"'][^\"']+[\"']|[^\s,;]+)",
        re.IGNORECASE,
    ),
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
                lambda match: match.group("prefix") + REDACTED,
                sanitized,
            )
        else:
            sanitized = pattern.sub(REDACTED, sanitized)

    return sanitized


def safe_security_response() -> str:
    return (
        "I can help with general, non-sensitive security guidance, "
        "but I cannot reveal, identify, locate, quote, or provide "
        "credentials, secrets, tokens, passwords, private keys, or "
        "other sensitive security information from the codebase."
    )
