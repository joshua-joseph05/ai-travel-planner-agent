"""Flight specialist — fetches live prices via SerpApi Google Flights."""

from travel_planner.budget import pick_under_budget
from travel_planner.llm import get_llm, message_text
from travel_planner.state import TravelState
from travel_planner.tools.serpapi_travel import format_flight_results, search_flights


def flight_agent(state: TravelState) -> dict:
    options = search_flights(
        origin=state["origin"],
        destination=state["destination"],
        outbound_date=state["outbound_date"],
        return_date=state["return_date"],
        adults=state.get("adults") or 1,
        currency=state.get("currency") or "USD",
    )
    priced = format_flight_results(options)

    # First pick: keep flights to ~45% of budget when a number exists
    budget_amount = state.get("budget_amount")
    flight_cap = budget_amount * 0.45 if budget_amount else None
    selected = pick_under_budget(options, flight_cap, price_key="price")
    flight_price = float(selected["price"]) if selected and selected.get("price") is not None else None

    llm = get_llm()
    budget = state.get("budget") or "flexible"
    selected_line = (
        f"Selected flight price for budgeting: {state.get('currency') or 'USD'} {flight_price}"
        if flight_price is not None
        else "No priced flight selected."
    )
    prompt = (
        "You are a flight-planning specialist. Using ONLY the live priced options "
        "below, recommend the best 1–2 choices and briefly explain why. "
        f"Budget preference: {budget}.\n"
        f"{selected_line}\n\n{priced}"
    )
    response = llm.invoke(prompt)

    return {
        "flight_options": options,
        "flight_price": flight_price,
        "flights": f"{priced}\n\n{selected_line}\n\nRecommendation:\n{message_text(response.content)}",
    }
