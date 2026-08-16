"""Data models for flight reservation PDF generator."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Passenger(BaseModel):
    """Passenger information."""
    title: str = "Mr"  # Mr, Mrs, Ms, Miss, Dr
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    passport_number: Optional[str] = None
    seat: Optional[str] = None
    ticket_number: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.title} {self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        return f"{self.last_name}/{self.first_name} {self.title}".upper()


# Summer UTC offsets (BST/CEST) for duration calculation
_AIRPORT_UTC_OFFSET = {
    # UK (BST = UTC+1)
    "LHR": 1, "LGW": 1, "STN": 1, "LTN": 1, "MAN": 1,
    "EDI": 1, "BHX": 1, "BRS": 1, "NCL": 1, "GLA": 1,
    # Ireland (IST = UTC+1)
    "DUB": 1,
    # Portugal (WEST = UTC+1)
    "LIS": 1,
    # Central Europe (CEST = UTC+2)
    "CDG": 2, "AMS": 2, "FRA": 2, "MUC": 2, "ZRH": 2,
    "VIE": 2, "BRU": 2, "BCN": 2, "MAD": 2, "FCO": 2,
    "FLR": 2, "MXP": 2, "VCE": 2, "NAP": 2,
    "CPH": 2, "OSL": 2, "ARN": 2, "HEL": 2,
    "MLA": 2,
}


class FlightSegment(BaseModel):
    """Single flight leg."""
    airline_code: str  # IATA 2-letter code (BA, LH, KL, AF)
    airline_name: str
    flight_number: str  # e.g. "BA304"
    departure_airport: str  # IATA code
    departure_city: str
    departure_terminal: Optional[str] = None
    arrival_airport: str
    arrival_city: str
    arrival_terminal: Optional[str] = None
    departure_datetime: datetime
    arrival_datetime: datetime
    cabin_class: str = "Economy"  # Economy, Premium Economy, Business, First
    booking_class: str = "Y"  # Fare class letter
    aircraft_type: Optional[str] = None  # e.g. "Airbus A320"
    status: str = "Confirmed"

    @property
    def duration_str(self) -> str:
        # Adjust for timezone difference between airports
        dep_offset = _AIRPORT_UTC_OFFSET.get(self.departure_airport, 1)
        arr_offset = _AIRPORT_UTC_OFFSET.get(self.arrival_airport, 1)
        delta = self.arrival_datetime - self.departure_datetime
        total_minutes = int(delta.total_seconds() / 60) + (dep_offset - arr_offset) * 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes:02d}m"


class Booking(BaseModel):
    """Complete booking/reservation."""
    booking_reference: str = Field(min_length=6, max_length=6)  # PNR
    airline_code: str  # Primary airline
    airline_name: str
    passengers: list[Passenger]
    segments: list[FlightSegment]
    booking_date: date
    total_price: float
    currency: str = "GBP"
    status: str = "Confirmed"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    @property
    def is_return(self) -> bool:
        return len(self.segments) > 1

    @property
    def outbound(self) -> FlightSegment:
        return self.segments[0]

    @property
    def inbound(self) -> Optional[FlightSegment]:
        return self.segments[1] if len(self.segments) > 1 else None
