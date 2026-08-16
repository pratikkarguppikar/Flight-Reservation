"""Flight search module — queries Amadeus API for real flight data."""

import os
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

from amadeus import Client, ResponseError
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


@dataclass
class FlightResult:
    """A single flight option from search results."""
    airline_code: str
    airline_name: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_datetime: datetime
    arrival_datetime: datetime
    duration: str  # ISO 8601 duration like "PT2H15M"
    stops: int
    cabin_class: str
    price: float
    currency: str
    aircraft_type: Optional[str] = None
    departure_terminal: Optional[str] = None
    arrival_terminal: Optional[str] = None
    booking_class: Optional[str] = None
    # For return flights
    return_flight_number: Optional[str] = None
    return_departure_airport: Optional[str] = None
    return_arrival_airport: Optional[str] = None
    return_departure_datetime: Optional[datetime] = None
    return_arrival_datetime: Optional[datetime] = None
    return_duration: Optional[str] = None
    return_stops: Optional[int] = None
    return_aircraft_type: Optional[str] = None
    return_departure_terminal: Optional[str] = None
    return_arrival_terminal: Optional[str] = None

    @property
    def duration_display(self) -> str:
        """Convert ISO duration PT2H15M to '2h 15m'."""
        return _parse_iso_duration(self.duration)

    @property
    def stops_display(self) -> str:
        if self.stops == 0:
            return "Direct"
        elif self.stops == 1:
            return "1 Stop"
        return f"{self.stops} Stops"


# Airline name mapping (common IATA codes)
AIRLINE_NAMES = {
    "BA": "British Airways",
    "LH": "Lufthansa",
    "KL": "KLM Royal Dutch Airlines",
    "AF": "Air France",
    "LX": "Swiss International Air Lines",
    "OS": "Austrian Airlines",
    "SK": "Scandinavian Airlines",
    "TP": "TAP Air Portugal",
    "IB": "Iberia",
    "FR": "Ryanair",
    "U2": "easyJet",
    "AY": "Finnair",
    "AZ": "ITA Airways",
    "SN": "Brussels Airlines",
    "EI": "Aer Lingus",
    "DY": "Norwegian",
    "W6": "Wizz Air",
    "VY": "Vueling",
    "EW": "Eurowings",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "TK": "Turkish Airlines",
    "VS": "Virgin Atlantic",
}


def _parse_iso_duration(iso_dur: str) -> str:
    """Convert PT2H15M to '2h 15m'."""
    iso_dur = iso_dur.replace("PT", "")
    hours = 0
    minutes = 0
    if "H" in iso_dur:
        parts = iso_dur.split("H")
        hours = int(parts[0])
        iso_dur = parts[1]
    if "M" in iso_dur:
        minutes = int(iso_dur.replace("M", ""))
    return f"{hours}h {minutes}m"


def get_amadeus_client() -> Optional[Client]:
    """Get configured Amadeus client from env vars."""
    client_id = os.getenv("AMADEUS_CLIENT_ID")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    return Client(
        client_id=client_id,
        client_secret=client_secret,
    )


def search_flights(
    origin: str,
    destination: str,
    departure_date: date,
    return_date: Optional[date] = None,
    adults: int = 1,
    cabin_class: str = "ECONOMY",
    max_results: int = 15,
) -> list[FlightResult]:
    """Search for flights using Amadeus API.

    Args:
        origin: IATA departure airport code (e.g. 'LHR')
        destination: IATA arrival airport code (e.g. 'CDG')
        departure_date: Outbound departure date
        return_date: Optional return date (omit for one-way)
        adults: Number of adult passengers
        cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
        max_results: Max number of results to return

    Returns:
        List of FlightResult objects, sorted by stops (direct first) then price.
    """
    client = get_amadeus_client()
    if not client:
        raise ValueError(
            "Amadeus API credentials not configured. "
            "Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env file."
        )

    search_params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date.isoformat(),
        "adults": adults,
        "travelClass": cabin_class,
        "nonStop": False,  # We want both, will sort later
        "max": max_results,
    }

    if return_date:
        search_params["returnDate"] = return_date.isoformat()

    try:
        response = client.shopping.flight_offers_search.get(**search_params)
    except ResponseError as e:
        raise ValueError(f"Amadeus API error: {e.response.body}") from e

    # Parse results
    results = []
    for offer in response.data:
        try:
            result = _parse_offer(offer)
            if result:
                results.append(result)
        except (KeyError, IndexError, ValueError):
            continue

    # Sort: direct first, then 1-stop, then by price
    results.sort(key=lambda r: (r.stops, r.price))

    return results


def _parse_offer(offer: dict) -> Optional[FlightResult]:
    """Parse a single Amadeus flight offer into a FlightResult."""
    price = float(offer["price"]["total"])
    currency = offer["price"]["currency"]

    itineraries = offer["itineraries"]
    if not itineraries:
        return None

    # Outbound itinerary
    outbound = itineraries[0]
    segments = outbound["segments"]
    if not segments:
        return None

    # For the main flight, use first segment info
    first_seg = segments[0]
    last_seg = segments[-1]
    stops = len(segments) - 1

    # Use the operating/marketing carrier
    airline_code = first_seg.get("operating", {}).get("carrierCode") or first_seg["carrierCode"]
    flight_num = f"{first_seg['carrierCode']}{first_seg['number']}"

    dep_dt = datetime.fromisoformat(first_seg["departure"]["at"])
    arr_dt = datetime.fromisoformat(last_seg["arrival"]["at"])

    aircraft_type = None
    if "aircraft" in first_seg:
        aircraft_type = first_seg["aircraft"].get("code")

    dep_terminal = first_seg["departure"].get("terminal")
    arr_terminal = last_seg["arrival"].get("terminal")

    # Get booking class from traveler pricing
    booking_class = None
    if "travelerPricings" in offer:
        try:
            fare_detail = offer["travelerPricings"][0]["fareDetailsBySegment"][0]
            booking_class = fare_detail.get("class")
            cabin = fare_detail.get("cabin", "ECONOMY")
        except (KeyError, IndexError):
            cabin = "ECONOMY"
    else:
        cabin = "ECONOMY"

    cabin_display = {
        "ECONOMY": "Economy",
        "PREMIUM_ECONOMY": "Premium Economy",
        "BUSINESS": "Business",
        "FIRST": "First",
    }.get(cabin, "Economy")

    result = FlightResult(
        airline_code=airline_code,
        airline_name=AIRLINE_NAMES.get(airline_code, airline_code),
        flight_number=flight_num,
        departure_airport=first_seg["departure"]["iataCode"],
        arrival_airport=last_seg["arrival"]["iataCode"],
        departure_datetime=dep_dt,
        arrival_datetime=arr_dt,
        duration=outbound.get("duration", "PT0H0M"),
        stops=stops,
        cabin_class=cabin_display,
        price=price,
        currency=currency,
        aircraft_type=aircraft_type,
        departure_terminal=dep_terminal,
        arrival_terminal=arr_terminal,
        booking_class=booking_class,
    )

    # Parse return itinerary if present
    if len(itineraries) > 1:
        ret = itineraries[1]
        ret_segments = ret["segments"]
        if ret_segments:
            ret_first = ret_segments[0]
            ret_last = ret_segments[-1]
            result.return_flight_number = f"{ret_first['carrierCode']}{ret_first['number']}"
            result.return_departure_airport = ret_first["departure"]["iataCode"]
            result.return_arrival_airport = ret_last["arrival"]["iataCode"]
            result.return_departure_datetime = datetime.fromisoformat(ret_first["departure"]["at"])
            result.return_arrival_datetime = datetime.fromisoformat(ret_last["arrival"]["at"])
            result.return_duration = ret.get("duration", "PT0H0M")
            result.return_stops = len(ret_segments) - 1
            result.return_aircraft_type = ret_first.get("aircraft", {}).get("code")
            result.return_departure_terminal = ret_first["departure"].get("terminal")
            result.return_arrival_terminal = ret_last["arrival"].get("terminal")

    return result


def is_configured() -> bool:
    """Check if Amadeus API credentials are configured."""
    return bool(os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET"))
