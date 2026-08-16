"""Lufthansa PDF template."""

from templates.base import BaseTemplate
from models.booking import Booking


class LufthansaTemplate(BaseTemplate):
    """Lufthansa branded booking confirmation."""

    AIRLINE_NAME = "Lufthansa"
    AIRLINE_CODE = "LH"
    PRIMARY_COLOR = (0.02, 0.09, 0.30)  # #05164D
    SECONDARY_COLOR = (1.0, 0.78, 0.17)  # #FFC72C
    HEADER_BG = (0.02, 0.09, 0.30)

    def _get_important_info_text(self, booking: Booking) -> list[str]:
        return [
            "Online check-in is available from 23 hours before departure at lufthansa.com.",
            "Carry a valid passport or ID card (for Schengen flights) with sufficient validity.",
            "Baggage allowance Economy: 1 cabin bag (8kg, 55x40x23cm) + 1 checked bag (23kg).",
            "Baggage allowance Business: 2 cabin bags (2x8kg) + 2 checked bags (32kg each).",
            "Please arrive at the airport at least 2 hours before scheduled departure.",
            "This booking confirmation is your electronic ticket receipt issued by Lufthansa.",
            "For visa applications: this confirms a valid reservation in the Lufthansa booking system.",
            "Miles & More members can credit miles for this flight at lufthansa.com.",
            "All times are local. Lufthansa reserves the right to make schedule changes.",
            "Contact Lufthansa Service Center: +49 69 86 799 799 or visit lufthansa.com.",
        ]
