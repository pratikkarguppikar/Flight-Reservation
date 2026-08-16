"""Duffel flight search provider — returns FlightResult objects like the Amadeus path.

Uses the Duffel Air API (offer requests) to fetch priced, bookable flight offers.
Credentials come from the ``DUFFEL_ACCESS_TOKEN`` environment variable (a test-mode
token works). No AWS or third-party secret store involved.
"""

import os
from datetime import date, datetime
from typing import Optional

import requests

from generators.flight_search import FlightResult, AIRLINE_NAMES

API_URL = "https://api.duffel.com/air/offer_requests"
API_VERSION = "v2"

# App cabin codes -> Duffel cabin_class values
_CABIN_MAP = {
    "ECONOMY": "economy",
    "PREMIUM_ECONOMY": "premium_economy",
    "BUSINESS": "business",
    "FIRST": "first",
}


def has_duffel_credentials() -> bool:
    """True when a Duffel access token is configured."""
    return bool(os.getenv("DUFFEL_ACCESS_TOKEN"))


def _parse_dt(value: str) -> datetime:
    """Parse a Duffel local datetime string (e.g. '2026-09-01T06:25:00')."""
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _offer_to_result(offer: dict) -> Optional[FlightResult]:
    """Convert a single Duffel offer (first slice) into a FlightResult."""
    slices = offer.get("slices") or []
    if not slices:
        return None
    segments = slices[0].get("segments") or []
    if not segments:
        return None

    first, last = segments[0], segments[-1]
    carrier = first.get("marketing_carrier") or first.get("operating_carrier") or {}
    airline_code = carrier.get("iata_code", "")
    airline_name = carrier.get("name") or AIRLINE_NAMES.get(airline_code, airline_code)
    flight_number = first.get("marketing_carrier_flight_number") or ""
    if airline_code and flight_number:
        flight_number = f"{airline_code}{flight_number}"

    aircraft = (first.get("aircraft") or {}).get("name")

    return FlightResult(
        airline_code=airline_code,
        airline_name=airline_name,
        flight_number=flight_number,
        departure_airport=(first.get("origin") or {}).get("iata_code", ""),
        arrival_airport=(last.get("destination") or {}).get("iata_code", ""),
        departure_datetime=_parse_dt(first["departing_at"]),
        arrival_datetime=_parse_dt(last["arriving_at"]),
        duration=slices[0].get("duration") or "PT0H0M",
        stops=max(0, len(segments) - 1),
        cabin_class="Economy",
        price=float(offer.get("total_amount", 0.0)),
        currency=offer.get("total_currency", "GBP"),
        aircraft_type=aircraft,
        departure_terminal=first.get("origin_terminal"),
        arrival_terminal=last.get("destination_terminal"),
        booking_class="Y",
    )


def search_duffel_flights(
    origin: str,
    destination: str,
    departure_date: date,
    adults: int = 1,
    cabin_class: str = "ECONOMY",
    max_results: int = 15,
) -> list[FlightResult]:
    """Search Duffel for one-way offers on a route/date.

    Returns FlightResult objects sorted by stops (direct first) then price.
    """
    token = os.getenv("DUFFEL_ACCESS_TOKEN")
    if not token:
        raise ValueError("DUFFEL_ACCESS_TOKEN not configured.")

    payload = {
        "data": {
            "slices": [
                {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date.isoformat(),
                }
            ],
            "passengers": [{"type": "adult"} for _ in range(max(1, adults))],
            "cabin_class": _CABIN_MAP.get(cabin_class.upper(), "economy"),
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Duffel-Version": API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        API_URL,
        params={"return_offers": "true"},
        json=payload,
        headers=headers,
        timeout=30,
    )
    if resp.status_code >= 400:
        raise ValueError(f"Duffel API error {resp.status_code}: {resp.text[:300]}")

    offers = (resp.json().get("data") or {}).get("offers") or []
    results = [r for r in (_offer_to_result(o) for o in offers) if r is not None]
    results.sort(key=lambda r: (r.stops, r.price))
    return results[:max_results]
