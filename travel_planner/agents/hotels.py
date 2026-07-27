"""Hotel specialist — fetches live prices via SerpApi Google Hotels."""

from travel_planner.budget import pick_under_budget
from travel_planner.llm import get_llm, message_text
from travel_planner.state import TravelState
from travel_planner.tools.serpapi_travel import format_hotel_results, search_hotels


def hotel_agent(state: TravelState) -> dict:
    options = search_hotels(
        location=state["destination"],
        check_in_date=state["outbound_date"],
        check_out_date=state["return_date"],
        adults=state.get("adults") or 2,
        currency=state.get("currency") or "USD",
    )
    priced = format_hotel_results(options)

    # Remaining budget after flights (leave ~20% buffer for activities/food)
    budget_amount = state.get("budget_amount")
    flight_price = state.get("flight_price") or 0.0
    hotel_cap = None
    if budget_amount is not None:
        hotel_cap = max(budget_amount * 0.8 - flight_price, 0)

    selected = pick_under_budget(options, hotel_cap, price_key="total_price_value")
    # Fallback: some results only have per-night extracted values
    if selected is None:
        selected = pick_under_budget(options, hotel_cap, price_key="price_per_night_value")

    hotel_total = None
    if selected:
        if selected.get("total_price_value") is not None:
            hotel_total = float(selected["total_price_value"])
        elif selected.get("price_per_night_value") is not None:
            hotel_total = float(selected["price_per_night_value"])

    llm = get_llm()
    budget = state.get("budget") or "flexible"
    selected_line = (
        f"Selected hotel total for budgeting: {state.get('currency') or 'USD'} {hotel_total}"
        if hotel_total is not None
        else "No priced hotel selected."
    )
    prompt = (
        "You are a hotel-planning specialist. Using ONLY the live priced options "
        "below, recommend the best 1–2 stays and briefly explain why. "
        f"Budget preference: {budget}.\n"
        f"{selected_line}\n\n{priced}"
    )
    response = llm.invoke(prompt)

    return {
        "hotel_options": options,
        "hotel_total": hotel_total,
        "hotels": f"{priced}\n\n{selected_line}\n\nRecommendation:\n{message_text(response.content)}",
    }
