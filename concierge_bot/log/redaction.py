import logging
import re

SENSITIVE_KEY_PATTERNS = (
    "key",
    "token",
    "secret",
    "password",
    "api_key",
    "dsn",
    "hash",
)
PREFIX_LEN = 4
SUFFIX_LEN = 4
MASK = "***"

OPENAI_KEY_RE = re.compile(r"sk-[a-zA-Z0-9]{20,}")
TG_TOKEN_RE = re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}")
DSN_RE = re.compile(
    r"(?:(?:postgres|mysql|redis|mongodb)(?::\/\/|[^\s,)]+))" r"[^\s,)\]]*",
    re.IGNORECASE,
)


def _mask_value(value: str) -> str:
    if len(value) <= PREFIX_LEN + SUFFIX_LEN:
        return MASK
    return value[:PREFIX_LEN] + MASK + value[-SUFFIX_LEN:]


def redact_string(s: str) -> str:
    s = TG_TOKEN_RE.sub(lambda m: _mask_value(m.group(0)), s)
    s = OPENAI_KEY_RE.sub(lambda m: _mask_value(m.group(0)), s)
    return DSN_RE.sub(lambda m: _mask_value(m.group(0)), s)


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    return any(p in k for p in SENSITIVE_KEY_PATTERNS)


def redact_log_message(text: str) -> str:
    text = redact_string(text)
    for key_part in SENSITIVE_KEY_PATTERNS:
        pattern = re.compile(
            r"(\b\w*" + re.escape(key_part) + r"\w*\s*=\s*)" r"([^\s,)\]}\']+)",
            re.IGNORECASE,
        )
        text = pattern.sub(lambda m: m.group(1) + _mask_value(m.group(2)), text)
        quoted = re.compile(
            r"(\b\w*" + re.escape(key_part) + r"\w*\s*=\s*)" r"[\'\"]([^\'\"]+)[\'\"]",
            re.IGNORECASE,
        )
        text = quoted.sub(
            lambda m: m.group(1) + "'" + _mask_value(m.group(2)) + "'", text
        )
    return text


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            record.msg = redact_log_message(msg)
            record.args = ()
        except (TypeError, ValueError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.debug("Redaction filter skipped record: %s", e)
        return True
