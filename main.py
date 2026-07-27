"""Entry point — runs the travel planner from a natural-language request."""

import sys

from dotenv import load_dotenv

from travel_planner.graph import build_graph

load_dotenv()


def main():
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        user_request = (
            "I am traveling from California to Italy and my budget is $5000"
        )

    app = build_graph()

    result = app.invoke(
        {
            "messages": [],
            "user_request": user_request,
            "origin": None,
            "destination": None,
            "outbound_date": None,
            "return_date": None,
            "budget": None,
            "budget_amount": None,
            "adults": None,
            "currency": None,
            "flight_options": None,
            "hotel_options": None,
            "flight_price": None,
            "hotel_total": None,
            "estimated_cost": None,
            "flights": None,
            "hotels": None,
            "activities": None,
            "itinerary": None,
            "budget_ok": None,
            "budget_feedback": None,
            "revision_count": 0,
        }
    )

    print("Parsed trip:")
    print(f"  From: {result.get('origin')}")
    print(f"  To:   {result.get('destination')}")
    print(f"  Dates:{result.get('outbound_date')} → {result.get('return_date')}")
    print(f"  Budget:{result.get('budget')} ({result.get('budget_amount')})")
    print(f"  Flight+hotel: {result.get('estimated_cost')}")
    print(f"  Budget OK: {result.get('budget_ok')}")
    print(f"  Revisions: {result.get('revision_count')}")
    if result.get("budget_feedback"):
        print(f"  Feedback: {result.get('budget_feedback')}")
    print()
    # Includes ## Options Tried and ## Final Itinerary from the synthesizer
    print(result["itinerary"])


if __name__ == "__main__":
    main()
