"""British Airways PDF template."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle

from templates.base import BaseTemplate
from models.booking import Booking


class BritishAirwaysTemplate(BaseTemplate):
    """British Airways branded booking confirmation."""

    AIRLINE_NAME = "British Airways"
    AIRLINE_CODE = "BA"
    PRIMARY_COLOR = (0.03, 0.35, 0.67)  # #075AAA
    SECONDARY_COLOR = (0.92, 0.13, 0.15)  # #EB2226
    HEADER_BG = (0.03, 0.35, 0.67)

    def _get_important_info_text(self, booking: Booking) -> list[str]:
        return [
            "Online check-in opens 24 hours before departure at ba.com.",
            "Carry a valid passport with at least 6 months validity beyond your travel date.",
            "Hand baggage: 1 cabin bag (max 23kg, 56x45x25cm) + 1 personal item for all classes.",
            "Checked baggage: 1 bag (23kg) included for Economy; 2 bags (32kg each) for Business/First.",
            "Arrive at the airport at least 2.5 hours before departure for international flights.",
            "This e-ticket itinerary/receipt is your confirmation of booking with British Airways.",
            "For visa applications: this document serves as proof of a confirmed flight reservation.",
            "Executive Club members can earn Avios on this booking. Log in at ba.com to add your number.",
            "Flight times shown in local time. British Airways reserves the right to amend schedules.",
            "For assistance, contact British Airways: +44 344 493 0787 or visit ba.com.",
        ]
