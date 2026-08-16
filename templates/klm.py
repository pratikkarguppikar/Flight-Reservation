"""KLM Royal Dutch Airlines PDF template."""

from templates.base import BaseTemplate
from models.booking import Booking


class KLMTemplate(BaseTemplate):
    """KLM branded booking confirmation."""

    AIRLINE_NAME = "KLM Royal Dutch Airlines"
    AIRLINE_CODE = "KL"
    PRIMARY_COLOR = (0.0, 0.63, 0.87)  # #00A1DE
    SECONDARY_COLOR = (0.0, 0.19, 0.27)  # #003145
    HEADER_BG = (0.0, 0.63, 0.87)

    def _get_important_info_text(self, booking: Booking) -> list[str]:
        return [
            "Online check-in opens 30 hours before departure at klm.com.",
            "Carry a valid passport with at least 6 months validity for non-Schengen travel.",
            "Baggage Economy: 1 hand baggage (12kg, 55x35x25cm) + 1 checked bag (23kg).",
            "Baggage Business: 2 hand baggage items + 2 checked bags (32kg each).",
            "Please be at the gate at least 40 minutes before departure.",
            "This is your electronic ticket confirmation issued by KLM Royal Dutch Airlines.",
            "For visa purposes: this document confirms an active reservation in the KLM system.",
            "Flying Blue members can earn Miles on this booking. Add your number at klm.com.",
            "All flight times are shown in local time at the departure/arrival airports.",
            "For support, contact KLM: +31 20 474 7747 or via klm.com.",
        ]
