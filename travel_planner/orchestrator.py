"""Orchestrator — parses the user request into structured trip fields."""

from datetime import date, timedelta

from pydantic import BaseModel, Field

from travel_planner.budget import parse_money
from travel_planner.llm import get_llm
from travel_planner.state import TravelState


class TripDetails(BaseModel):
    """Structured trip fields extracted from natural language."""

    origin: str = Field(
        description="Where the traveler is leaving from (city, region, or airport code)."
    )
    destination: str = Field(
        description="Where the traveler is going (city, country, or airport code)."
    )
    outbound_date: str = Field(
        description="Departure date in YYYY-MM-DD. Infer a reasonable future date if missing."
    )
    return_date: str = Field(
        description="Return date in YYYY-MM-DD. Default to ~7 days after outbound if missing."
    )
    budget: str | None = Field(
        default=None,
        description="Budget as stated by the user, e.g. '$5000' or 'moderate'.",
    )
    budget_amount: float | None = Field(
        default=None,
        description="Numeric budget amount if stated, e.g. 5000 for $5000. Null if unknown.",
    )
    adults: int = Field(default=1, description="Number of adult travelers.")
    currency: str = Field(default="USD", description="3-letter currency code.")


def _default_dates() -> tuple[str, str]:
    outbound = date.today() + timedelta(days=30)
    ret = outbound + timedelta(days=7)
    return outbound.isoformat(), ret.isoformat()


def _parse_request(user_request: str) -> TripDetails:
    llm = get_llm()
    structured = llm.with_structured_output(TripDetails)
    today = date.today().isoformat()
    default_out, default_ret = _default_dates()

    prompt = (
        "Extract travel planning details from the user's message.\n"
        f"Today's date is {today}.\n"
        "Rules:\n"
        "- origin = departure place (city/region/country/airport)\n"
        "- destination = arrival place\n"
        f"- If dates are missing, use outbound={default_out} and return={default_ret}\n"
        "- Dates must be YYYY-MM-DD and in the future\n"
        "- Keep budget text as the user said it (include $ if present)\n"
        "- budget_amount = numeric value only when a number is given\n"
        "- Prefer major airports when a state/country is given "
        "(e.g. California→Los Angeles/LAX, Italy→Rome/FCO)\n\n"
        f"User message:\n{user_request}"
    )
    return structured.invoke(prompt)


def orchestrator(state: TravelState) -> dict:
    """Parse the request once, then the graph moves on to the specialists."""
    details = _parse_request(state["user_request"])
    amount = details.budget_amount
    if amount is None:
        amount = parse_money(details.budget)

    return {
        "origin": details.origin,
        "destination": details.destination,
        "outbound_date": details.outbound_date,
        "return_date": details.return_date,
        "budget": details.budget,
        "budget_amount": amount,
        "adults": details.adults or 1,
        "currency": details.currency or "USD",
        "revision_count": 0,
        "budget_ok": None,
        "budget_feedback": None,
    }
