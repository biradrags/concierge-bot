import logging
from collections.abc import Iterator

import pytest
from bira_core.log.redaction import RedactionFilter

from concierge_bot.log import setup_logging


def _filtered(msg: str) -> str:
    rec = logging.LogRecord("t", logging.INFO, "x.py", 1, msg, None, None)
    RedactionFilter().filter(rec)
    return rec.getMessage()


@pytest.fixture
def restored_root_logger() -> Iterator[logging.Logger]:
    root = logging.getLogger()
    access = logging.getLogger("aiohttp.access")
    handlers, level, access_filters = root.handlers[:], root.level, access.filters[:]
    yield root
    root.handlers[:] = handlers
    root.setLevel(level)
    access.filters[:] = access_filters


def test_bare_aws_access_key_id_is_masked() -> None:
    out = _filtered("upload failed key=AKIAIOSFODNN7EXAMPLE")
    assert "AKIAIOSFODNN7EXAMPLE" not in out  # noqa: S101


def test_openai_project_key_is_masked() -> None:
    out = _filtered("openai error sk-proj-AbCdEfGhIjKlMnOpQrStUvWx")
    assert "sk-proj-AbCdEfGhIjKlMnOpQrStUvWx" not in out  # noqa: S101


def test_setup_logging_attaches_library_redaction_filter(
    restored_root_logger: logging.Logger,
) -> None:
    setup_logging()

    filters = [f for h in restored_root_logger.handlers for f in h.filters]
    assert any(isinstance(f, RedactionFilter) for f in filters)  # noqa: S101
