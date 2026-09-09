"""Activities specialist — uses MCP places tools for live recommendations."""

from __future__ import annotations

import os

from travel_planner.llm import get_llm, message_text
from travel_planner.mcp_client import load_places_tools_sync
from travel_planner.state import TravelState
from travel_planner.tool_runtime import run_tool_agent_sync


def activity_agent(state: TravelState) -> dict:
    destination = state["destination"]
    outbound = state["outbound_date"]
    ret = state["return_date"]
    budget = state.get("budget") or "flexible"
    use_mcp = os.getenv("ENABLE_PLACES_MCP", "true").lower() not in {
        "0",
        "false",
        "no",
    }

    if use_mcp:
        try:
            tools = load_places_tools_sync()
            text = run_tool_agent_sync(
                system=(
                    "You are an activities specialist for trip planning. "
                    "Use the available MCP places tools to find real attractions, "
                    "food spots, and experiences. Prefer highly rated options. "
                    "Call search_places_tool at least once before answering. "
                    "Keep the final answer concise (under 180 words) and include "
                    "place names with ratings when available."
                ),
                user=(
                    f"Plan things to do in {destination} from {outbound} to {ret}. "
                    f"Budget: {budget}. Mix landmarks, food, and local experiences."
                ),
                tools=tools,
                max_rounds=3,
            )
            return {"activities": text}
        except Exception as exc:  # noqa: BLE001 - fall back so the graph still finishes
            fallback_note = f"(MCP places unavailable: {exc})"
    else:
        fallback_note = "(MCP places disabled)"

    # Fallback: Gemini-only suggestions if MCP is off or fails
    llm = get_llm()
    prompt = (
        "You are an activities specialist. Suggest things to do "
        f"in {destination} from {outbound} to {ret}. Budget: {budget}. "
        "Mix landmarks, food, and local experiences. "
        "Keep the answer concise (under 150 words).\n"
        f"{fallback_note}"
    )
    response = llm.invoke(prompt)
    return {"activities": message_text(response.content)}
