"""Generic airline PDF template for airlines without a specific template."""

from templates.base import BaseTemplate
from models.booking import Booking


class GenericTemplate(BaseTemplate):
    """Generic airline booking confirmation template.

    Used for airlines that don't have a dedicated template.
    Colors are set dynamically from airline data.
    """

    AIRLINE_NAME = "Airline"
    AIRLINE_CODE = "XX"
    PRIMARY_COLOR = (0.2, 0.2, 0.4)
    SECONDARY_COLOR = (0.8, 0.1, 0.1)
    HEADER_BG = (0.2, 0.2, 0.4)

    def set_airline_branding(self, name: str, code: str, primary_hex: str,
                            secondary_hex: str):
        """Dynamically configure airline branding."""
        self.AIRLINE_NAME = name
        self.AIRLINE_CODE = code
        self.PRIMARY_COLOR = self._hex_to_rgb(primary_hex)
        self.SECONDARY_COLOR = self._hex_to_rgb(secondary_hex)
        self.HEADER_BG = self.PRIMARY_COLOR
        # Re-initialize styles with new colors
        self._setup_styles()

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color (#RRGGBB) to RGB tuple (0-1 scale)."""
        hex_color = hex_color.lstrip("#")
        return (
            int(hex_color[0:2], 16) / 255,
            int(hex_color[2:4], 16) / 255,
            int(hex_color[4:6], 16) / 255,
        )
