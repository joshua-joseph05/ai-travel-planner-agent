"""Local MCP server: Google Maps places tools backed by SerpApi.

Run standalone:
  python -m travel_planner.mcp_servers.places_server
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from travel_planner.tools.serpapi_travel import get_place_details, search_places

mcp = FastMCP("travel-places")


@mcp.tool()
def search_places_tool(query: str, location: str = "", limit: int = 5) -> str:
    """Search real places/attractions/restaurants with Google Maps via SerpApi.

    Args:
        query: What to look for, e.g. "museums", "ramen", "things to do".
        location: City or area to search in, e.g. "Tokyo" or "Rome".
        limit: Max number of places to return (1-8).
    """
    capped = max(1, min(int(limit or 5), 8))
    results = search_places(
        query,
        location=location or None,
        limit=capped,
    )
    return json.dumps(results, ensure_ascii=False, indent=2)


@mcp.tool()
def get_place_details_tool(place_id: str) -> str:
    """Get richer details for one place using its Google Maps place_id.

    Args:
        place_id: Google Maps place id from search_places_tool results.
    """
    details = get_place_details(place_id)
    return json.dumps(details, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
