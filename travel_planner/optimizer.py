"""Budget optimizer — re-picks cheaper flight/hotel options after a failed evaluation."""

from travel_planner.budget import cheapest
from travel_planner.llm import get_llm, message_text
from travel_planner.state import TravelState
from travel_planner.tools.serpapi_travel import format_flight_results, format_hotel_results


def optimizer(state: TravelState) -> dict:
    """Force cheapest available options and bump revision_count."""
    flight_options = state.get("flight_options") or []
    hotel_options = state.get("hotel_options") or []

    cheap_flight = cheapest(flight_options, price_key="price")
    cheap_hotel = cheapest(hotel_options, price_key="total_price_value")
    if cheap_hotel is None:
        cheap_hotel = cheapest(hotel_options, price_key="price_per_night_value")

    flight_price = (
        float(cheap_flight["price"])
        if cheap_flight and cheap_flight.get("price") is not None
        else state.get("flight_price")
    )
    hotel_total = None
    if cheap_hotel:
        if cheap_hotel.get("total_price_value") is not None:
            hotel_total = float(cheap_hotel["total_price_value"])
        elif cheap_hotel.get("price_per_night_value") is not None:
            hotel_total = float(cheap_hotel["price_per_night_value"])
    if hotel_total is None:
        hotel_total = state.get("hotel_total")

    currency = state.get("currency") or "USD"
    flights_text = format_flight_results(flight_options)
    hotels_text = format_hotel_results(hotel_options)

    llm = get_llm()
    prompt = (
        "You are revising a trip to fit budget constraints.\n"
        f"Feedback: {state.get('budget_feedback')}\n"
        f"Cheapest flight now selected: {currency} {flight_price}\n"
        f"Cheapest hotel now selected: {currency} {hotel_total}\n"
        "Write a short note explaining the cheaper picks for the synthesizer.\n\n"
        f"Flights:\n{flights_text}\n\nHotels:\n{hotels_text}"
    )
    note = message_text(llm.invoke(prompt).content)

    return {
        "flight_price": flight_price,
        "hotel_total": hotel_total,
        "flights": (
            f"{flights_text}\n\nSelected (optimizer): {currency} {flight_price}\n\n{note}"
        ),
        "hotels": (
            f"{hotels_text}\n\nSelected (optimizer): {currency} {hotel_total}\n\n{note}"
        ),
        "revision_count": (state.get("revision_count") or 0) + 1,
        "budget_ok": None,
    }
