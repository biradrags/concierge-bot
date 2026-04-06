from typing import Any

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from pydantic import BaseModel


def _is_reasoning_model(model: str) -> bool:
    return model.startswith(("gpt-5", "o3", "o4"))


def create_agent(
    client: OpenAIChatClient,
    *,
    name: str,
    prompt: str,
    tools: list[Any] | None = None,
    response_format: type[BaseModel] | None = None,
    model: str,
    max_tokens: int = 2048,
    middleware: list[Any] | None = None,
    context_providers: list[Any] | None = None,
    max_iterations: int = 8,
    temperature: float = 0.3,
    reasoning_effort: str = "low",
) -> Agent:
    options: dict[str, Any] = {
        "model": model,
        "response_format": response_format,
        "max_tokens": max_tokens,
        "allow_multiple_tool_calls": True,
    }
    if _is_reasoning_model(model):
        options["reasoning"] = {"effort": reasoning_effort, "summary": "concise"}
        options["text"] = {"verbosity": "low"}
    else:
        options["temperature"] = temperature

    agent = client.as_agent(
        name=name,
        instructions=prompt,
        tools=tools or [],
        default_options=options,
        middleware=middleware or [],
        context_providers=context_providers or [],
    )
    agent.function_invocation_configuration = {
        "max_iterations": max_iterations,
        "max_consecutive_errors_per_request": 2,
    }
    return agent
