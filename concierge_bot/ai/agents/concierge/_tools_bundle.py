from agent_framework import FunctionInvocationContext

from concierge_bot.ai.agents.concierge.context import ConciergeState, ToolDeps


def bundle_tool_ctx(
    ctx: FunctionInvocationContext,
) -> tuple[ToolDeps, ConciergeState] | None:
    k = ctx.kwargs
    if not k:
        return None
    d, s = k.get("deps"), k.get("state")
    if isinstance(d, ToolDeps) and isinstance(s, ConciergeState):
        return d, s
    return None
