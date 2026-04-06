from typing import Annotated
from uuid import UUID

from agent_framework import FunctionInvocationContext, tool
from pydantic import Field

from concierge_bot.ai.agents.concierge._tools_bundle import bundle_tool_ctx


@tool(
    name="search_services",
    description="Search hotel services by text and optional category.",
)
async def search_services(
    query: Annotated[str, Field(description="Search text for name or description")],
    ctx: FunctionInvocationContext,
    category: Annotated[
        str | None,
        Field(description="Optional category filter", default=None),
    ] = None,
) -> str:
    got = bundle_tool_ctx(ctx)
    if got is None:
        return "Error: internal context missing."
    deps, _state = got
    rows = await deps.dao.service.search(deps.hotel.id, query)
    if category:
        rows = [r for r in rows if r.category.lower() == category.lower()]
    if not rows:
        return "No matching services."
    lines = [f"- {r.name} ({r.category}) id={r.id} price={r.price} {r.currency}" for r in rows[:15]]
    return "Services:\n" + "\n".join(lines)


@tool(
    name="create_booking",
    description="Create a pending booking for a service UUID.",
)
async def create_booking(
    service_id: Annotated[str, Field(description="Service UUID from search_services")],
    ctx: FunctionInvocationContext,
    notes: Annotated[str | None, Field(description="Optional guest notes")] = None,
) -> str:
    got = bundle_tool_ctx(ctx)
    if got is None:
        return "Error: internal context missing."
    deps, state = got
    try:
        sid = UUID(service_id.strip())
    except ValueError:
        return "Invalid service_id — must be a UUID."
    try:
        booking = await deps.booking_service.create_booking(
            guest=deps.guest,
            service_id=sid,
            hotel=deps.hotel,
            notes=notes,
        )
        state.last_booking = booking
        return f"Booking created (pending): {booking.id}. The hotel will confirm soon."
    except ValueError as e:
        return f"Could not book: {e}"
