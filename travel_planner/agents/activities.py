"""Activities specialist — only cares about things to do."""

from travel_planner.llm import get_llm, message_text
from travel_planner.state import TravelState


def activity_agent(state: TravelState) -> dict:
    llm = get_llm()
    destination = state["destination"]
    outbound = state["outbound_date"]
    ret = state["return_date"]
    budget = state.get("budget") or "flexible"

    prompt = (
        "You are an activities specialist. Suggest things to do "
        f"in {destination} from {outbound} to {ret}. Budget: {budget}. "
        "Mix landmarks, food, and local experiences. "
        "Keep the answer concise (under 150 words)."
    )
    response = llm.invoke(prompt)

    return {"activities": message_text(response.content)}
