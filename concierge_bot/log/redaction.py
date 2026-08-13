import logging
import re
from typing import Any

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
# Токен TG-бота: <bot_id>:<35 символов>. В мультибот-схеме он попадает в путь
# вебхука (`/webhook/t/<token>`), а оттуда в access-лог.
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


def _is_countable(value: str) -> bool:
    """Число - не секрет.

    Поля вроде `input_tokens=15234`, `total_tokens=…`, `hash=0` попадают под
    подстроку из SENSITIVE_KEY_PATTERNS, но несут статистику, а не тайну: у
    настоящего ключа/токена значение всегда содержит буквы или разделители.
    Без этой проверки счётчики LLM-usage уезжали в лог как `1***4` и переставали
    что-либо значить (найдено на живых логах 2026-08-13).
    """
    return value.isdigit() or (value.replace(".", "", 1).isdigit() and "." in value)


def redact_log_message(text: str) -> str:
    text = redact_string(text)
    for key_part in SENSITIVE_KEY_PATTERNS:
        pattern = re.compile(
            r"(\b\w*" + re.escape(key_part) + r"\w*\s*=\s*)" r"([^\s,)\]}\']+)",
            re.IGNORECASE,
        )
        text = pattern.sub(
            lambda m: m.group(0)
            if _is_countable(m.group(2))
            else m.group(1) + _mask_value(m.group(2)),
            text,
        )
        quoted = re.compile(
            r"(\b\w*" + re.escape(key_part) + r"\w*\s*=\s*)" r"[\'\"]([^\'\"]+)[\'\"]",
            re.IGNORECASE,
        )
        text = quoted.sub(
            lambda m: m.group(0)
            if _is_countable(m.group(2))
            else m.group(1) + "'" + _mask_value(m.group(2)) + "'",
            text,
        )
    return text


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        result: dict[str, Any] = {}
        for k, v in obj.items():
            if _is_sensitive_key(k):
                result[k] = _mask_value(str(v))
            else:
                result[k] = redact(v)
        return result
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


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
