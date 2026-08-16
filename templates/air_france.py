"""Air France PDF template."""

from templates.base import BaseTemplate
from models.booking import Booking


class AirFranceTemplate(BaseTemplate):
    """Air France branded booking confirmation."""

    AIRLINE_NAME = "Air France"
    AIRLINE_CODE = "AF"
    PRIMARY_COLOR = (0.0, 0.13, 0.34)  # #002157
    SECONDARY_COLOR = (0.89, 0.0, 0.17)  # #E4002B
    HEADER_BG = (0.0, 0.13, 0.34)

    def _get_important_info_text(self, booking: Booking) -> list[str]:
        return [
            "Online check-in opens 30 hours before departure at airfrance.com.",
            "Carry a valid passport or national ID card (Schengen flights) with sufficient validity.",
            "Baggage Economy: 1 cabin bag (12kg, 55x35x25cm) + 1 checked bag (23kg).",
            "Baggage Business/La Première: 2 cabin bags + 2 checked bags (32kg each).",
            "Please arrive at the airport at least 2 hours before international departure.",
            "This e-ticket receipt confirms your reservation with Air France.",
            "For visa applications: this document proves a confirmed booking in the Air France system.",
            "Flying Blue members can earn Miles on this journey. Manage at airfrance.com.",
            "Flight times shown are local times. Air France may adjust schedules — check online.",
            "Contact Air France: +33 9 69 39 02 15 or visit airfrance.com for assistance.",
        ]
