"""Small helper to run an LLM with LangChain tools (including MCP tools)."""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from travel_planner.llm import get_llm, message_text


async def run_tool_agent(
    *,
    system: str,
    user: str,
    tools: list[BaseTool],
    max_rounds: int = 3,
) -> str:
    """Invoke Gemini with tools until it stops calling tools or hits max_rounds."""
    llm = get_llm().bind_tools(tools)
    tool_map = {t.name: t for t in tools}
    messages: list[Any] = [
        SystemMessage(content=system),
        HumanMessage(content=user),
    ]

    for _ in range(max_rounds):
        ai: AIMessage = await llm.ainvoke(messages)
        messages.append(ai)

        tool_calls = getattr(ai, "tool_calls", None) or []
        if not tool_calls:
            return message_text(ai.content)

        for call in tool_calls:
            name = call["name"]
            args = call.get("args") or {}
            tool = tool_map.get(name)
            if tool is None:
                result = f"Unknown tool: {name}"
            else:
                result = await tool.ainvoke(args)
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=call["id"],
                )
            )

    # Final pass without tools if we exhausted rounds mid-tool-use
    final = await get_llm().ainvoke(messages)
    return message_text(final.content)


def run_tool_agent_sync(
    *,
    system: str,
    user: str,
    tools: list[BaseTool],
    max_rounds: int = 3,
) -> str:
    return asyncio.run(
        run_tool_agent(
            system=system,
            user=user,
            tools=tools,
            max_rounds=max_rounds,
        )
    )
