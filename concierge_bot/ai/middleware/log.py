import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from agent_framework import (
    AgentContext,
    AgentMiddleware,
    FunctionInvocationContext,
    FunctionMiddleware,
    Message,
)

logger = logging.getLogger(__name__)

CONTENT_PREVIEW_LEN = 1000
INSTRUCTIONS_LIMIT = 200
TOOL_RESPONSE_LOG_MAX_CHARS = 800
PAYLOAD_WARN_BYTES = 500_000


class LoggingMiddleware(AgentMiddleware):
    async def process(
        self, context: AgentContext, call_next: Callable[[], Awaitable[None]]
    ) -> None:
        await self._log_start(context)
        await call_next()
        await self._log_complete(context)

    async def _log_start(self, ctx: AgentContext) -> None:
        logger.debug(
            "agent=%s session=%s",
            ctx.agent.name,
            ctx.session.session_id if ctx.session else None,
        )
        instructions = (ctx.agent.default_options or {}).get("instructions")
        if instructions and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "instructions_preview=%s",
                self._truncate(str(instructions), INSTRUCTIONS_LIMIT),
            )
        if ctx.messages:
            logger.debug("new_messages=%d", len(ctx.messages))
            if logger.isEnabledFor(logging.DEBUG):
                for msg in ctx.messages:
                    role = str(getattr(msg, "role", "unknown"))
                    approval_summary = self._get_approval_summary(msg)
                    if approval_summary:
                        logger.debug("%s: [approval_callback] %s", role.upper(), approval_summary)
                    else:
                        content = self._get_content(msg)
                        logger.debug("%s: %s", role.upper(), self._truncate(content, CONTENT_PREVIEW_LEN))
        total_for_llm = len(ctx.messages)
        if not logger.isEnabledFor(logging.DEBUG) and total_for_llm < 30:
            return
        payload_bytes = sum(len(json.dumps(m.to_dict())) for m in ctx.messages)
        payload_kb = payload_bytes / 1024
        if payload_bytes > PAYLOAD_WARN_BYTES:
            logger.warning(
                "large_llm_payload_kb=%.1f messages=%d agent=%s session=%s",
                payload_kb,
                total_for_llm,
                ctx.agent.name,
                ctx.session.session_id if ctx.session else None,
            )
        else:
            logger.debug("payload_kb=%.1f messages=%d", payload_kb, total_for_llm)

    async def _log_complete(self, ctx: AgentContext) -> None:
        logger.debug("agent_done=%s", ctx.agent.name)
        if ctx.result and logger.isEnabledFor(logging.DEBUG):
            text = getattr(ctx.result, "text", None) or str(ctx.result)
            self._log_response_text(text)

    def _get_approval_summary(self, msg: Message) -> str | None:
        contents = getattr(msg, "contents", None) or []
        approval_items: list[str] = []
        for item in contents:
            content_type = getattr(item, "type", None)
            if content_type in ("function_approval_response", "mcp_approval_response"):
                fc = getattr(item, "function_call", None) or {}
                name = (fc.get("name") if isinstance(fc, dict) else getattr(fc, "name", None)) or "unknown"
                approved = getattr(item, "approved", None)
                approval_items.append(f"{name}={'approved' if approved else 'rejected'}")
        return ", ".join(approval_items) if approval_items else None

    def _get_content(self, msg: Message) -> str:
        content = getattr(msg, "text", None) or getattr(msg, "content", "")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if hasattr(item, "text"):
                    parts.append(item.text)
                else:
                    parts.append(str(item))
            return " ".join(parts)
        return str(content)

    def _truncate(self, text: str, limit: int) -> str:
        text = " ".join(str(text).split())
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _log_response_text(self, text: str) -> None:
        try:
            data = json.loads(text)
            message = data.get("message", data.get("text", ""))
            logger.debug("result_message=%s", self._truncate(message, CONTENT_PREVIEW_LEN))
        except (json.JSONDecodeError, TypeError):
            logger.debug("result_text=%s", self._truncate(text, CONTENT_PREVIEW_LEN))


def _safe_tool_context_repr(ctx: Any) -> str:
    name = type(ctx).__name__
    config = getattr(ctx, "config", None)
    if config is None:
        return f"<{name}>"
    env = getattr(config, "app_env", "?")
    return f"<{name} config=<{type(config).__name__} app_env={env!r}>>"


def _safe_args_repr(arguments: Any) -> str:
    if not isinstance(arguments, dict):
        return repr(arguments)
    safe: dict[str, Any] = {}
    for k, v in arguments.items():
        if k in ("tool_context", "deps", "state") and v is not None:
            safe[k] = _safe_tool_context_repr(v)
        else:
            safe[k] = v
    return repr(safe)


def _args_preview(arguments: Any, function_name: str) -> str:  # noqa: ARG001
    full = _safe_args_repr(arguments)
    limit = CONTENT_PREVIEW_LEN
    return full[:limit] + ("..." if len(full) > limit else "")


def _tool_response_repr(result: object) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    try:
        return json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(result)


class FunctionLoggingMiddleware(FunctionMiddleware):
    async def process(
        self,
        context: FunctionInvocationContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        function_name = context.function.name
        preview = _args_preview(context.arguments, function_name)
        logger.debug("[tool] %s args=%s", function_name, preview)
        await call_next()
        response_repr = _tool_response_repr(context.result)
        response_size = len(response_repr)
        if response_size <= TOOL_RESPONSE_LOG_MAX_CHARS:
            logger.debug("[tool] %s done size=%s body=%s", function_name, response_size, response_repr)
        else:
            logger.debug("[tool] %s done size=%s", function_name, response_size)
