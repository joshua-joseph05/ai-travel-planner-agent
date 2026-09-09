"""Load LangChain tools from local MCP servers."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _python_executable() -> str:
    return sys.executable


def places_server_command() -> dict:
    """Stdio connection config for the local places MCP server."""
    return {
        "command": _python_executable(),
        "args": ["-m", "travel_planner.mcp_servers.places_server"],
        "cwd": str(PROJECT_ROOT),
        "transport": "stdio",
        "env": {
            **os.environ,
            # Ensure package imports resolve when launched as a subprocess
            "PYTHONPATH": str(PROJECT_ROOT),
        },
    }


async def load_places_tools() -> list[BaseTool]:
    """Connect to the places MCP server and return its tools."""
    client = MultiServerMCPClient({"places": places_server_command()})
    return await client.get_tools()


def load_places_tools_sync() -> list[BaseTool]:
    return asyncio.run(load_places_tools())
