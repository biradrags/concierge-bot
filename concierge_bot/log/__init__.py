"""Логи: logfmt на stdout."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from concierge_bot.log.redaction import RedactionFilter

_STD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}

_MAX_VAL = 120


def _fmt_val(value: object, limit: int | None = _MAX_VAL) -> str:
    text = str(value)
    if limit is not None and len(text) > limit:
        text = text[:limit] + "…"
    if text == "" or any(ch in text for ch in ' ="\n\t'):
        escaped = (
            text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'
    return text


class LogfmtFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime("%H:%M:%S")
        parts = [
            f"ts={ts}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={_fmt_val(record.getMessage(), limit=None)}",
        ]
        parts += [
            f"{key}={_fmt_val(value)}"
            for key, value in record.__dict__.items()
            if key not in _STD_ATTRS and not key.startswith("_")
        ]
        if record.exc_info:
            parts.append(
                f"exc={_fmt_val(self.formatException(record.exc_info), limit=None)}"
            )
        if record.stack_info:
            parts.append(
                f"stack={_fmt_val(self.formatStack(record.stack_info), limit=None)}"
            )
        return " ".join(parts)


class _ProbeAccessFilter(logging.Filter):
    _SKIP = ("/health", "/webhook")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(path in msg for path in self._SKIP)


def setup_logging(level: str | int | None = None) -> None:
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    if isinstance(level, str):
        level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(LogfmtFormatter())
    handler.addFilter(RedactionFilter())
    root = logging.getLogger()
    for existing in root.handlers[:]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("aiohttp.access").addFilter(_ProbeAccessFilter())
    for noisy in ("aiogram.event", "aiohttp.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
