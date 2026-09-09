# AI Travel Planner Agent

A LangGraph multi-agent travel planner that turns a natural-language request into a trip plan with live flight, hotel, and activity data.

Example:

```bash
python main.py I want to go from New York to Rome for a week with a budget of \$5000
```

## What it does

1. **Orchestrator** parses your request into origin, destination, dates, and budget
2. **Flights agent** searches live prices with SerpApi Google Flights
3. **Hotels agent** searches live prices with SerpApi Google Hotels
4. **Activities agent** finds real places via a local **MCP** places server (SerpApi Google Maps)
5. **Synthesizer** combines results into a readable itinerary
6. **Evaluator / Optimizer** checks the budget and revises with cheaper options if needed

## Architecture

```text
START
  → orchestrator
  → flights
  → hotels
  → activities (+ MCP places tools)
  → synthesizer
  → evaluator
       ├─ pass → END
       └─ revise → optimizer → synthesizer → evaluator ...
```

### Project layout

```text
main.py
travel_planner/
  graph.py              # LangGraph wiring
  state.py              # shared TravelState
  orchestrator.py       # parse natural language
  synthesizer.py        # options tried + final itinerary
  evaluator.py          # budget check
  optimizer.py          # cheaper re-picks
  llm.py                # Gemini client
  mcp_client.py         # load MCP tools
  tool_runtime.py       # LLM + tools loop
  agents/
    flights.py
    hotels.py
    activities.py
  tools/
    serpapi_travel.py   # Flights / Hotels / Maps helpers
  mcp_servers/
    places_server.py    # local MCP server for places
```

## Requirements

- Python 3.10+
- [Gemini API key](https://aistudio.google.com/apikey)
- [SerpApi API key](https://serpapi.com/manage-api-key)

## Setup

```bash
cd "AI Travel Planner Agent"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Fill in:

```bash
GEMINI_API_KEY=your_key_here
SERPAPI_API_KEY=your_key_here
ENABLE_PLACES_MCP=true
```

Optional:

```bash
# Override Gemini model (default: gemini-3.1-flash-lite)
GEMINI_MODEL=gemini-3.1-flash-lite
```

## Run

Always use the project virtualenv:

```bash
source .venv/bin/activate
python main.py
```

Or with your own prompt:

```bash
python main.py I am traveling from California to Italy and my budget is \$5000
```

Without activating the venv:

```bash
.venv/bin/python main.py "Trip from Seattle to Tokyo, October 10-17, budget $4000"
```

## Test MCP places tools

Confirm the MCP server exposes tools:

```bash
python -c "from travel_planner.mcp_client import load_places_tools_sync; print([t.name for t in load_places_tools_sync()])"
```

Expected:

```text
['search_places_tool', 'get_place_details_tool']
```

Run a live places search:

```bash
python -c "
import asyncio
from travel_planner.mcp_client import load_places_tools

async def main():
    tools = await load_places_tools()
    search = next(t for t in tools if t.name == 'search_places_tool')
    print(await search.ainvoke({'query': 'museums', 'location': 'Rome', 'limit': 3}))

asyncio.run(main())
"
```

## Output

The final print includes:

- Parsed trip fields (origin, destination, dates, budget)
- Budget status / revision count
- **Options Tried** (flight + hotel options considered)
- **Final Itinerary**

## Notes

- Keep secrets in `.env` only — never commit real keys
- Free Gemini tiers have rate limits; `gemini-3.1-flash-lite` is the default to reduce quota issues
- Set `ENABLE_PLACES_MCP=false` to fall back to Gemini-only activity suggestions
