"""Shared TravelState — the notebook every agent reads and writes."""

from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    messages: Annotated[list, add_messages]
    # Raw natural-language request from the user
    user_request: str
    # Filled by the orchestrator after parsing user_request
    origin: Optional[str]
    destination: Optional[str]
    outbound_date: Optional[str]  # YYYY-MM-DD
    return_date: Optional[str]  # YYYY-MM-DD
    budget: Optional[str]
    budget_amount: Optional[float]
    adults: Optional[int]
    currency: Optional[str]
    # Live SerpApi option lists (for budget optimizer re-picks)
    flight_options: Optional[list[dict[str, Any]]]
    hotel_options: Optional[list[dict[str, Any]]]
    # Selected numeric costs
    flight_price: Optional[float]
    hotel_total: Optional[float]
    estimated_cost: Optional[float]
    # Specialist outputs — collected for the synthesizer
    flights: Optional[str]
    hotels: Optional[str]
    activities: Optional[str]
    # Final plan from the synthesizer
    itinerary: Optional[str]
    # Budget evaluator–optimizer loop
    budget_ok: Optional[bool]
    budget_feedback: Optional[str]
    revision_count: int
