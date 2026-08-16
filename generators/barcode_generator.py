"""Barcode generation for flight tickets."""

import io
from typing import Optional

import barcode
from barcode.writer import ImageWriter


def generate_barcode_image(data: str, barcode_type: str = "code128") -> bytes:
    """Generate a barcode image as PNG bytes.

    Args:
        data: The data to encode in the barcode.
        barcode_type: Type of barcode (code128, ean13, etc.)

    Returns:
        PNG image bytes of the barcode.
    """
    code_class = barcode.get_barcode_class(barcode_type)
    writer = ImageWriter()
    writer.set_options({
        "module_width": 0.2,
        "module_height": 8.0,
        "quiet_zone": 2.0,
        "font_size": 8,
        "text_distance": 3.0,
        "write_text": False,
    })
    code = code_class(data, writer=writer)

    buffer = io.BytesIO()
    code.write(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_ticket_barcode(ticket_number: str) -> bytes:
    """Generate barcode for an e-ticket number."""
    # Remove dashes for barcode encoding
    clean_number = ticket_number.replace("-", "")
    return generate_barcode_image(clean_number)
