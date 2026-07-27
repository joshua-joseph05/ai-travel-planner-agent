"""SerpApi helpers for Google Flights and Google Hotels."""

from __future__ import annotations

import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


def _api_key() -> str:
    key = os.getenv("SERPAPI_API_KEY")
    if not key:
        raise ValueError(
            "Missing SERPAPI_API_KEY. Add it to your .env file (see .env.example)."
        )
    return key


def _search(params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(
        SERPAPI_ENDPOINT,
        params={**params, "api_key": _api_key()},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError(f"SerpApi error: {data['error']}")
    return data


def resolve_airport_code(place: str) -> str:
    """Return a 3-letter IATA code. Pass-through if already a code."""
    cleaned = place.strip().upper()
    if re.fullmatch(r"[A-Z]{3}", cleaned):
        return cleaned

    # Lightweight city → primary airport map for common demos
    known = {
        "TOKYO": "NRT",
        "OSAKA": "KIX",
        "SEOUL": "ICN",
        "BEIJING": "PEK",
        "SHANGHAI": "PVG",
        "HONG KONG": "HKG",
        "SINGAPORE": "SIN",
        "BANGKOK": "BKK",
        "LONDON": "LHR",
        "PARIS": "CDG",
        "NEW YORK": "JFK",
        "LOS ANGELES": "LAX",
        "CALIFORNIA": "LAX",
        "SAN FRANCISCO": "SFO",
        "CHICAGO": "ORD",
        "SEATTLE": "SEA",
        "MIAMI": "MIA",
        "DALLAS": "DFW",
        "AUSTIN": "AUS",
        "SYDNEY": "SYD",
        "MELBOURNE": "MEL",
        "DUBAI": "DXB",
        "ROME": "FCO",
        "ITALY": "FCO",
        "MILAN": "MXP",
        "BARCELONA": "BCN",
        "AMSTERDAM": "AMS",
        "BERLIN": "BER",
        "MADRID": "MAD",
        "TORONTO": "YYZ",
        "VANCOUVER": "YVR",
    }
    for city, code in known.items():
        if city in cleaned:
            return code

    # Fall back to Gemini for anything else
    from travel_planner.llm import get_llm

    llm = get_llm()
    reply = llm.invoke(
        "Return ONLY the primary 3-letter IATA airport code for this place. "
        f"No punctuation or explanation. Place: {place}"
    )
    match = re.search(r"[A-Za-z]{3}", str(reply.content))
    if not match:
        raise ValueError(f"Could not resolve airport code for '{place}'")
    return match.group(0).upper()


def search_flights(
    origin: str,
    destination: str,
    outbound_date: str,
    return_date: str,
    *,
    adults: int = 1,
    currency: str = "USD",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Flights via SerpApi and return priced options."""
    departure_id = resolve_airport_code(origin)
    arrival_id = resolve_airport_code(destination)

    data = _search(
        {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": outbound_date,
            "return_date": return_date,
            "type": "1",  # round trip
            "adults": adults,
            "currency": currency,
            "hl": "en",
        }
    )

    options = data.get("best_flights") or data.get("other_flights") or []
    formatted: list[dict[str, Any]] = []

    for option in options[:limit]:
        legs = option.get("flights") or []
        first = legs[0] if legs else {}
        last = legs[-1] if legs else {}
        airlines = " → ".join(
            dict.fromkeys(leg.get("airline", "Unknown") for leg in legs)
        ) or "Unknown"
        stops = max(len(legs) - 1, 0)
        formatted.append(
            {
                "price": option.get("price"),
                "currency": currency,
                "airlines": airlines,
                "stops": stops,
                "total_duration_minutes": option.get("total_duration"),
                "depart": (first.get("departure_airport") or {}).get("time"),
                "arrive": (last.get("arrival_airport") or {}).get("time"),
                "from": departure_id,
                "to": arrival_id,
                "type": option.get("type", "Round trip"),
            }
        )

    return formatted


def search_hotels(
    location: str,
    check_in_date: str,
    check_out_date: str,
    *,
    adults: int = 2,
    currency: str = "USD",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search Google Hotels via SerpApi and return priced properties."""
    data = _search(
        {
            "engine": "google_hotels",
            "q": location,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": adults,
            "currency": currency,
            "gl": "us",
            "hl": "en",
            "sort_by": "3",  # lowest price
        }
    )

    properties = data.get("properties") or []
    formatted: list[dict[str, Any]] = []

    for prop in properties[:limit]:
        rate = prop.get("rate_per_night") or {}
        total = prop.get("total_rate") or {}
        formatted.append(
            {
                "name": prop.get("name"),
                "type": prop.get("type"),
                "rating": prop.get("overall_rating"),
                "reviews": prop.get("reviews"),
                "price_per_night": rate.get("lowest") or rate.get("before_taxes_fees"),
                "price_per_night_value": rate.get("extracted_lowest"),
                "total_price": total.get("lowest") or total.get("before_taxes_fees"),
                "total_price_value": total.get("extracted_lowest"),
                "currency": currency,
            }
        )

    return formatted


def format_flight_results(options: list[dict[str, Any]]) -> str:
    if not options:
        return "No flight results found for these dates/airports."

    lines = ["Top flight options (live SerpApi prices):"]
    for i, opt in enumerate(options, start=1):
        price = opt.get("price")
        price_text = f"{opt.get('currency', 'USD')} {price}" if price is not None else "Price n/a"
        duration = opt.get("total_duration_minutes")
        duration_text = f"{duration} min" if duration else "duration n/a"
        lines.append(
            f"{i}. {opt.get('airlines')} | {price_text} | "
            f"{opt.get('stops')} stop(s) | {duration_text} | "
            f"{opt.get('from')} → {opt.get('to')} | "
            f"depart {opt.get('depart')} / arrive {opt.get('arrive')}"
        )
    return "\n".join(lines)


def format_hotel_results(options: list[dict[str, Any]]) -> str:
    if not options:
        return "No hotel results found for this location/dates."

    lines = ["Top hotel options (live SerpApi prices):"]
    for i, opt in enumerate(options, start=1):
        rating = opt.get("rating")
        rating_text = f"{rating}/5" if rating is not None else "no rating"
        lines.append(
            f"{i}. {opt.get('name')} | "
            f"{opt.get('price_per_night') or 'n/a'}/night | "
            f"total {opt.get('total_price') or 'n/a'} | "
            f"{rating_text}"
        )
    return "\n".join(lines)
