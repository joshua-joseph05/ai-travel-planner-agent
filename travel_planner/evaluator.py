"""Budget evaluator — checks whether selected flight+hotel fit the budget."""

from travel_planner.state import TravelState

# Leave headroom for food/activities when judging flight+hotel spend
ACTIVITY_BUFFER_RATIO = 0.15
MAX_REVISIONS = 2


def evaluator(state: TravelState) -> dict:
    budget_amount = state.get("budget_amount")
    flight_price = state.get("flight_price")
    hotel_total = state.get("hotel_total")

    # No numeric budget → nothing to enforce
    if budget_amount is None:
        return {
            "budget_ok": True,
            "budget_feedback": "No numeric budget provided; skipping budget check.",
            "estimated_cost": _sum_costs(flight_price, hotel_total),
        }

    if flight_price is None or hotel_total is None:
        return {
            "budget_ok": False,
            "budget_feedback": (
                "Missing priced flight or hotel selection; "
                "optimizer should pick the cheapest available options."
            ),
            "estimated_cost": _sum_costs(flight_price, hotel_total),
        }

    estimated = float(flight_price) + float(hotel_total)
    # Require leaving a small buffer inside the total budget
    allowed = budget_amount * (1 - ACTIVITY_BUFFER_RATIO)

    if estimated <= allowed:
        return {
            "estimated_cost": estimated,
            "budget_ok": True,
            "budget_feedback": (
                f"OK: flight+hotel ${estimated:.0f} is within "
                f"${allowed:.0f} of the ${budget_amount:.0f} budget "
                f"(keeping ~{int(ACTIVITY_BUFFER_RATIO * 100)}% for activities)."
            ),
        }

    over_by = estimated - allowed
    return {
        "estimated_cost": estimated,
        "budget_ok": False,
        "budget_feedback": (
            f"OVER BUDGET: flight+hotel ${estimated:.0f} exceeds the "
            f"${allowed:.0f} flight/hotel allowance from a ${budget_amount:.0f} budget "
            f"(over by ${over_by:.0f}). Switch to cheaper flight and/or hotel options."
        ),
    }


def route_budget(state: TravelState) -> str:
    if state.get("budget_ok"):
        return "pass"
    if (state.get("revision_count") or 0) >= MAX_REVISIONS:
        return "pass"
    return "revise"


def _sum_costs(flight_price, hotel_total) -> float | None:
    if flight_price is None and hotel_total is None:
        return None
    return float(flight_price or 0) + float(hotel_total or 0)
