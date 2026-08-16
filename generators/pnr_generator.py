"""PNR and ticket number generators."""

import random
import string
from datetime import date


# Characters used in real PNRs (excludes ambiguous: 0, O, 1, I)
PNR_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# IATA airline accounting codes — the 3-digit prefix of a 13-digit e-ticket number
AIRLINE_TICKET_PREFIXES = {
    "BA": "125", "LH": "220", "AF": "057", "KL": "074", "IB": "075",
    "AZ": "055", "LX": "724", "OS": "257", "SN": "082", "TP": "047",
    "SK": "117", "AY": "105", "EI": "053", "VS": "932", "U2": "888",
    "FR": "312", "AA": "001", "DL": "006", "UA": "016", "AC": "014",
    "EK": "176", "QR": "157", "EY": "607", "TK": "235", "SQ": "618",
    "CX": "160", "QF": "081", "NH": "205", "JL": "131", "WN": "526",
}


def airline_ticket_prefix(airline_code: str) -> str:
    """Return the 3-digit IATA accounting code that prefixes an e-ticket number."""
    code = (airline_code or "").upper()
    if code in AIRLINE_TICKET_PREFIXES:
        return AIRLINE_TICKET_PREFIXES[code]
    # Deterministic, plausible 3-digit fallback (never 000) for unlisted carriers
    return str((sum(ord(c) for c in code) * 7) % 899 + 100)


def generate_pnr() -> str:
    """Generate a realistic 6-character PNR/booking reference."""
    return "".join(random.choices(PNR_CHARS, k=6))


def generate_ticket_number(airline_prefix: str = "125") -> str:
    """Generate a realistic 13-digit e-ticket number.

    Format: {airline_prefix}-{10_digit_number}
    Example: 125-2345678901 (BA ticket)
    """
    seq = "".join(random.choices(string.digits, k=10))
    return f"{airline_prefix}-{seq}"


def generate_booking_reference_display(pnr: str, airline_code: str) -> str:
    """Format booking reference for display."""
    return f"{pnr}"


def generate_confirmation_number() -> str:
    """Generate a confirmation/order number (8 alphanumeric)."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_eticket_receipt(airline_prefix: str = "125") -> str:
    """Generate e-ticket receipt number (airline prefix + 10 digits)."""
    seq = "".join(random.choices(string.digits, k=10))
    return f"{airline_prefix}{seq}"
