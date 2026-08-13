import logging
import re
from typing import Any

# Имена полей, значение которых маскируется целиком. Матчинг ТОЧНЫЙ (полное имя
# или суффикс), а не по подстроке: подстрочный вариант съедал доменные поля -
# `token_id` (тикер монеты USDT в обменниках), `phash` (перцептивный хеш
# аватарки, по нему считается drift), `key` (путь объекта в приватном бакете).
# Все три - публичные величины, ради которых логи и читают; маскировка их
# обесценивала. Найдено параллельными сессиями на переводе логов 2026-08-13.
#
# `hash` убран совсем: хеш - уже необратимое представление, секретом не является.
SENSITIVE_KEY_NAMES = frozenset(
    {
        "token",
        "secret",
        "password",
        "passwd",
        "pwd",
        "dsn",
        "auth",
        "authorization",
        "credentials",
        "api_key",
        "apikey",
        "secret_key",
        "private_key",
        "access_key",
        "session_string",
    }
)
SENSITIVE_KEY_SUFFIXES = (
    "_token",
    "_secret",
    "_password",
    "_api_key",
    "_apikey",
    "_dsn",
    "_credentials",
)
# Для поиска `ключ=значение` внутри свободного текста: там имя не отделено, поэтому
# ищем по этим основам, а точность добирается тем же предикатом `_is_sensitive_key`.
SENSITIVE_KEY_PATTERNS = ("token", "secret", "password", "api_key", "dsn", "auth")
PREFIX_LEN = 4
SUFFIX_LEN = 4
MASK = "***"

OPENAI_KEY_RE = re.compile(r"sk-[a-zA-Z0-9]{20,}")
# Токен TG-бота: <bot_id>:<35 символов>. В мультибот-схеме он попадает в путь
# вебхука (`/webhook/t/<token>`), а оттуда в access-лог.
# Без \b слева: в URL вида `/bot8035582859:AAE…` перед цифрами стоит буква, и
# граница слова там не срабатывает - токен проходил мимо маскировки.
TG_TOKEN_RE = re.compile(r"\d{6,12}:[A-Za-z0-9_-]{30,}")
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
    return k in SENSITIVE_KEY_NAMES or k.endswith(SENSITIVE_KEY_SUFFIXES)


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
            lambda m: (
                m.group(0)
                if _is_countable(m.group(2))
                or not _is_sensitive_key(m.group(1).split("=")[0].strip())
                else m.group(1) + _mask_value(m.group(2))
            ),
            text,
        )
        quoted = re.compile(
            r"(\b\w*" + re.escape(key_part) + r"\w*\s*=\s*)" r"[\'\"]([^\'\"]+)[\'\"]",
            re.IGNORECASE,
        )
        text = quoted.sub(
            lambda m: (
                m.group(0)
                if _is_countable(m.group(2))
                or not _is_sensitive_key(m.group(1).split("=")[0].strip())
                else m.group(1) + "'" + _mask_value(m.group(2)) + "'"
            ),
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


# Служебные атрибуты LogRecord: их не трогаем, всё остальное в __dict__ - это extra.
# Снимаем с живого экземпляра, а не списком руками: набор зависит от версии Python.
_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


def redact_extra(fields: dict[str, Any]) -> dict[str, Any]:
    """Прогнать значения extra через маскировку.

    Пока данные жили внутри текста сообщения, их чистил `redact_log_message`.
    После переноса в `extra={...}` (канон logging.md) они идут мимо: фильтр правил
    только `record.msg`. Дыра реальная - `extra={"err": str(e)}` легко приносит в
    логи URL с токеном из текста исключения внешнего клиента.

    Чувствительное имя ключа маскирует значение целиком, остальные строки чистятся
    по содержимому (sk-ключи, DSN, токен бота). Числа не трогаем: счётчики вроде
    `input_tokens=15234` - не секрет.
    """
    result: dict[str, Any] = {}
    for key, value in fields.items():
        if isinstance(value, dict | list):
            # Вложенный payload (тело запроса, dump ответа) - рекурсивно: секрет
            # прячется на любой глубине, а не только в плоском поле.
            result[key] = redact(value)
        elif not isinstance(value, str) or _is_countable(value):
            result[key] = value
        elif _is_sensitive_key(key):
            result[key] = _mask_value(value)
        else:
            result[key] = redact_string(value)
    return result


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            record.msg = redact_log_message(msg)
            record.args = ()
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in _RECORD_ATTRS and not k.startswith("_")
            }
            if extra:
                record.__dict__.update(redact_extra(extra))
        except (TypeError, ValueError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.debug("redaction filter skipped record", extra={"err": str(e)})
        return True
