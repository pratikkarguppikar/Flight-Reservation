"""PDF generator orchestrator — ties booking data to airline templates."""

import json
import os
from pathlib import Path

from models.booking import Booking
from templates.british_airways import BritishAirwaysTemplate
from templates.lufthansa import LufthansaTemplate
from templates.klm import KLMTemplate
from templates.air_france import AirFranceTemplate
from templates.generic import GenericTemplate


# Template registry
TEMPLATE_MAP = {
    "BA": BritishAirwaysTemplate,
    "LH": LufthansaTemplate,
    "KL": KLMTemplate,
    "AF": AirFranceTemplate,
}

DATA_DIR = Path(__file__).parent.parent / "data"


def get_airlines_data() -> dict:
    """Load airlines metadata from JSON."""
    with open(DATA_DIR / "airlines.json", "r") as f:
        return json.load(f)


def get_airports_data() -> dict:
    """Load airports metadata from JSON."""
    with open(DATA_DIR / "airports.json", "r") as f:
        return json.load(f)


def get_airline_info(airline_code: str) -> dict | None:
    """Get airline metadata by IATA code."""
    data = get_airlines_data()
    for airline in data["airlines"]:
        if airline["code"] == airline_code:
            return airline
    return None


def get_template_for_airline(airline_code: str):
    """Get the appropriate template instance for an airline."""
    if airline_code in TEMPLATE_MAP:
        return TEMPLATE_MAP[airline_code]()

    # Use generic template with dynamic branding
    airline_info = get_airline_info(airline_code)
    template = GenericTemplate()
    if airline_info:
        template.set_airline_branding(
            name=airline_info["name"],
            code=airline_info["code"],
            primary_hex=airline_info["primary_color"],
            secondary_hex=airline_info["secondary_color"],
        )
    return template


def generate_booking_pdf(booking: Booking) -> bytes:
    """Generate a complete booking confirmation PDF.

    Args:
        booking: Complete booking data model.

    Returns:
        PDF file content as bytes.
    """
    template = get_template_for_airline(booking.airline_code)
    return template.generate_pdf(booking)


def get_all_airports() -> list[dict]:
    """Get flat list of all airports with region info."""
    data = get_airports_data()
    airports = []
    for region, airport_list in data.items():
        for airport in airport_list:
            airports.append({**airport, "region": region})
    return airports


def get_all_airlines() -> list[dict]:
    """Get list of all supported airlines."""
    data = get_airlines_data()
    return data["airlines"]


def get_terminal_for_airport(airline_code: str, airport_code: str) -> str | None:
    """Look up the terminal for a given airline at a given airport."""
    airline_info = get_airline_info(airline_code)
    if airline_info and "terminals" in airline_info:
        return airline_info["terminals"].get(airport_code)
    return None
