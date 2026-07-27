"""Synthesizer — lists considered options, then writes the final itinerary."""

from travel_planner.llm import get_llm, message_text
from travel_planner.state import TravelState
from travel_planner.tools.serpapi_travel import format_flight_results, format_hotel_results


def _options_tried_section(state: TravelState) -> str:
    """Build a factual list of flight/hotel options the planner considered."""
    flights = format_flight_results(state.get("flight_options") or [])
    hotels = format_hotel_results(state.get("hotel_options") or [])
    currency = state.get("currency") or "USD"
    revision = state.get("revision_count") or 0

    selected = [
        f"- Selected flight price: {currency} {state.get('flight_price')}",
        f"- Selected hotel total: {currency} {state.get('hotel_total')}",
        f"- Estimated flight+hotel: {currency} {state.get('estimated_cost')}",
        f"- Budget: {state.get('budget')} ({state.get('budget_amount')})",
        f"- Budget revisions tried: {revision}",
    ]
    if state.get("budget_feedback"):
        selected.append(f"- Budget feedback: {state.get('budget_feedback')}")

    return "\n".join(
        [
            "## Options Tried",
            "",
            "### Flights considered",
            flights,
            "",
            "### Hotels considered",
            hotels,
            "",
            "### Selection used for this plan",
            *selected,
            "",
            "### Activities considered",
            state.get("activities") or "(none)",
        ]
    )


def synthesizer(state: TravelState) -> dict:
    options_section = _options_tried_section(state)

    llm = get_llm()
    feedback = state.get("budget_feedback")
    feedback_block = f"\nBudget evaluator feedback:\n{feedback}\n" if feedback else ""

    prompt = (
        "You are a travel planner. Write ONLY the final trip plan section.\n"
        "Do not list all options again — that is already shown separately.\n\n"
        f"Original request: {state['user_request']}\n"
        f"From: {state['origin']}\n"
        f"To: {state['destination']}\n"
        f"Dates: {state['outbound_date']} → {state['return_date']}\n"
        f"Budget: {state.get('budget') or 'flexible'}\n"
        f"Selected flight price: {state.get('flight_price')}\n"
        f"Selected hotel total: {state.get('hotel_total')}\n"
        f"{feedback_block}\n"
        f"Flight notes:\n{state['flights']}\n\n"
        f"Hotel notes:\n{state['hotels']}\n\n"
        f"Activities:\n{state['activities']}\n\n"
        "Write a polished ## Final Itinerary the traveler should follow. "
        "Keep the real selected prices. "
        "If over budget, prioritize the cheaper selected options and note any shortfall."
    )
    response = llm.invoke(prompt)
    final = message_text(response.content).strip()
    if not final.startswith("## Final Itinerary"):
        final = f"## Final Itinerary\n\n{final}"

    return {"itinerary": f"{options_section}\n\n{final}"}
