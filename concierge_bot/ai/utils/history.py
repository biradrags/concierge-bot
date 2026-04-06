from __future__ import annotations

import contextvars
import json
import logging

import redis.asyncio as redis
from agent_framework import Message

logger = logging.getLogger(__name__)

KEY_PREFIX = "concierge_messages"

# Флаг для принудительной очистки function_calls на ретрае после ошибки грязной истории.
# RetryMiddleware выставляет True перед повторной попыткой → sanitize_messages стрипает
# function_calls из последнего assistant-сообщения, даже если там есть pending approval.
force_strip_dangling_calls: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "force_strip_dangling_calls", default=False,
)


def filter_for_commit(messages: list[Message]) -> list[Message]:
    """User + assistant text only for Redis commit after a sent reply."""
    result: list[Message] = []
    for msg in messages:
        if str(msg.role).lower() not in ("user", "assistant"):
            continue
        text_contents = [c for c in (msg.contents or []) if getattr(c, "type", None) == "text"]
        if text_contents:
            result.append(Message(role=msg.role, contents=text_contents))
    return result


def _strip_function_calls(msg: Message) -> Message | None:
    """Remove function_call items from a Message. Returns None if message becomes empty."""
    contents = msg.contents or []
    kept = [c for c in contents if getattr(c, "type", None) != "function_call"]
    if len(kept) == len(contents):
        return msg
    if not kept:
        return None
    return Message(role=msg.role, contents=kept)


def sanitize_messages(messages: list[Message]) -> list[Message]:
    """Sanitize history loaded from Redis before sending to OpenAI.

    Handles:
    1. Orphaned TOOL messages (tool result without preceding function_call)
    2. Mid-history orphaned function_calls (assistant → user without tool results)
    3. Tail orphaned function_calls on forced retry (contextvar flag from RetryMiddleware)

    Does NOT strip function_calls from the last assistant message by default —
    they may be needed for the approval flow (user confirms → framework matches
    function_approval_response to function_call in history).
    """
    if not messages:
        return messages

    force_strip = force_strip_dangling_calls.get(False)

    sanitized: list[Message] = []
    last_assistant_had_tool_calls = False
    skipped_tool = 0
    stripped_fc = 0

    for msg in messages:
        role = str(msg.role).lower()
        if role == "assistant":
            has_tool_calls = any(
                getattr(c, "type", None) == "function_call"
                for c in (msg.contents or [])
            )
            last_assistant_had_tool_calls = has_tool_calls
            sanitized.append(msg)
        elif role == "tool":
            if last_assistant_had_tool_calls:
                sanitized.append(msg)
            else:
                skipped_tool += 1
            last_assistant_had_tool_calls = False
        else:
            # USER/system after assistant с неразрешёнными function_calls → mid-history orphan
            if last_assistant_had_tool_calls and sanitized:
                for i in range(len(sanitized) - 1, -1, -1):
                    if str(sanitized[i].role).lower() == "assistant":
                        replacement = _strip_function_calls(sanitized[i])
                        if replacement:
                            sanitized[i] = replacement
                        else:
                            sanitized.pop(i)
                        stripped_fc += 1
                        break
            last_assistant_had_tool_calls = False
            sanitized.append(msg)

    if skipped_tool > 0:
        logger.info("Sanitized %d orphaned TOOL messages from history", skipped_tool)

    # Последнее сообщение: function_calls без tool-ответов.
    # По умолчанию НЕ стрипаем — они нужны для approval flow.
    # Стрипаем ТОЛЬКО при force_strip (ретрай после ошибки dirty history).
    if last_assistant_had_tool_calls and force_strip and sanitized:
        for i in range(len(sanitized) - 1, -1, -1):
            if str(sanitized[i].role).lower() == "assistant":
                replacement = _strip_function_calls(sanitized[i])
                if replacement:
                    sanitized[i] = replacement
                else:
                    sanitized.pop(i)
                stripped_fc += 1
                break

    if stripped_fc > 0:
        logger.info(
            "Sanitized dangling function_call(s) from %d assistant message(s) in history",
            stripped_fc,
        )

    return sanitized


def _normalize_messages_for_openai(messages: list[Message]) -> list[Message]:
    """Normalize history messages to strict OpenAI Responses input types."""
    result: list[Message] = []
    for msg in messages:
        d = msg.to_dict()
        role = str(d.get("role", "")).lower()
        contents = d.get("contents") or []
        fixed = []
        for c in contents:
            if not isinstance(c, dict):
                fixed.append(c)
                continue
            content_type = c.get("type")
            # Convert non-MCP approval wrappers to text. The framework serializes
            # function_approval_request as mcp_approval_request and always adds server_label —
            # but non-MCP tools (approval_mode="always_require") have no server_label, causing
            # OpenAI 400 on history replay. MCP approvals have server_label set, pass through.
            if content_type in ("function_approval_request", "mcp_approval_request"):
                fc = c.get("function_call") or {}
                ap = fc.get("additional_properties") or {}
                server_label = ap.get("server_label") or c.get("server_label")
                if not server_label:
                    name = fc.get("name") or c.get("name") or "tool"
                    fixed.append({"type": "text", "text": f"[approval: {name}]"})
                    continue
            if content_type in ("function_approval_response", "mcp_approval_response"):
                fc = c.get("function_call") or {}
                ap = fc.get("additional_properties") or {}
                if not (ap.get("server_label") or c.get("server_label")):
                    continue

            if content_type in ("image_generation_tool_call", "image_generation_tool_result"):
                fixed.append({"type": "text", "text": "[image generated]"})
                continue

            if content_type in ("uri", "data"):
                media_type = c.get("media_type", "")
                if isinstance(media_type, str) and media_type.startswith("image/"):
                    continue

            if (
                role == "assistant"
                and content_type == "output"
                and isinstance(c.get("output"), dict)
            ):
                obj = c["output"]
                text = obj.get("text") if isinstance(obj, dict) else None
                text = text or json.dumps(obj, ensure_ascii=False)
                fixed.append({"type": "text", "text": text})
            elif content_type == "function_result":
                # Когда MiddlewareTermination срабатывает на инструменте, вызванном через
                # function_approval_response, фреймворк создаёт function_result с call_id=None
                # (response имеет id, но не call_id). OpenAI отклоняет такие записи с 400.
                if not c.get("call_id"):
                    continue
                items = c.get("items") or []
                cleaned_items = []
                for item in items:
                    if isinstance(item, dict) and item.get("type") == "uri":
                        media_type = item.get("media_type", "file")
                        cleaned_items.append({"type": "text", "text": f"[{media_type}]"})
                    else:
                        cleaned_items.append(item)
                c = {**c, "items": cleaned_items} if cleaned_items != items else c

                value = c.get("result")
                if isinstance(value, str) or (
                    isinstance(value, list)
                    and all(isinstance(item, dict) for item in value)
                ):
                    fixed.append(c)
                else:
                    fixed.append(
                        {
                            **c,
                            "result": json.dumps(value, ensure_ascii=False)
                            if value is not None
                            else "",
                        }
                    )
            else:
                fixed.append(c)
        d["contents"] = fixed
        result.append(Message.from_dict(d))
    return result


def _trim_by_turns(
    messages: list[Message],
    history_turns: int,
    max_messages: int | None,
) -> list[Message]:
    user_indices = [i for i, m in enumerate(messages) if str(m.role).lower() == "user"]
    start_idx = (
        user_indices[-history_turns] if len(user_indices) >= history_turns else 0
    )
    trimmed = messages[start_idx:]
    if max_messages is not None and len(trimmed) > max_messages:
        trimmed = trimmed[-max_messages:]
    removed = len(messages) - len(trimmed)
    if removed > 0:
        logger.info(
            "Message store: trimmed history_turns=%s max_messages=%s, removed %s messages",
            history_turns,
            max_messages,
            removed,
        )
    return trimmed


def _redis_list_key(key_prefix: str, thread_id: str) -> str:
    return f"{key_prefix}:{thread_id}"


async def get_history(
    redis_url: str,
    thread_id: str,
    *,
    key_prefix: str = KEY_PREFIX,
    history_turns: int = 2,
    max_messages: int | None = None,
) -> list[Message]:
    if max_messages is not None and max_messages <= 0:
        raise ValueError(f"max_messages must be a positive integer or None, got {max_messages}")
    client = redis.from_url(redis_url, decode_responses=True)
    try:
        fetch_limit = max_messages if max_messages is not None else 100
        raw = await client.lrange(_redis_list_key(key_prefix, thread_id), -fetch_limit, -1)
        messages = [Message.from_dict(json.loads(s)) for s in (raw or [])]
    finally:
        await client.aclose()
    sanitized = sanitize_messages(messages)
    normalized = _normalize_messages_for_openai(sanitized)
    return _trim_by_turns(normalized, history_turns, max_messages)


def assert_max_messages_positive(max_messages: int | None) -> None:
    if max_messages is not None and max_messages <= 0:
        raise ValueError(f"max_messages must be a positive integer or None, got {max_messages}")
