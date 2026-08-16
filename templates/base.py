"""Base PDF template for flight reservation confirmations."""

import io
import os
import tempfile
from abc import ABC, abstractmethod
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak, Flowable
)
from reportlab.pdfgen import canvas

from models.booking import Booking, FlightSegment, Passenger
from generators.barcode_generator import generate_ticket_barcode


class ColoredBox(Flowable):
    """A colored rectangle flowable for section headers."""

    def __init__(self, width, height, color, text="", text_color=colors.white,
                 font_name="Helvetica-Bold", font_size=11):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color
        self.text = text
        self.text_color = text_color
        self.font_name = font_name
        self.font_size = font_size

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        if self.text:
            self.canv.setFillColor(self.text_color)
            self.canv.setFont(self.font_name, self.font_size)
            self.canv.drawString(6, (self.height - self.font_size) / 2 + 1, self.text)


class BaseTemplate(ABC):
    """Abstract base class for airline PDF templates."""

    # Override in subclasses
    AIRLINE_NAME: str = "Airline"
    AIRLINE_CODE: str = "XX"
    PRIMARY_COLOR: tuple = (0.03, 0.35, 0.67)  # RGB 0-1
    SECONDARY_COLOR: tuple = (0.92, 0.13, 0.15)
    HEADER_BG: tuple = (0.03, 0.35, 0.67)
    PAGE_MARGINS = (15 * mm, 15 * mm, 15 * mm, 15 * mm)  # L, R, T, B

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Set up common paragraph styles."""
        def _add_or_replace(style):
            """Add a style, replacing it if already defined."""
            if style.name in self.styles.byName:
                self.styles.byName[style.name] = style
            else:
                self.styles.add(style)

        _add_or_replace(ParagraphStyle(
            name="AirlineHeader",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=colors.white,
            alignment=TA_LEFT,
        ))
        _add_or_replace(ParagraphStyle(
            name="BookingRef",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=colors.Color(*self.PRIMARY_COLOR),
            alignment=TA_LEFT,
        ))
        _add_or_replace(ParagraphStyle(
            name="SectionTitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=colors.Color(*self.PRIMARY_COLOR),
            spaceAfter=4,
            leftIndent=6,
        ))
        _add_or_replace(ParagraphStyle(
            name="FieldLabel",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.Color(0.4, 0.4, 0.4),
        ))
        _add_or_replace(ParagraphStyle(
            name="FieldValue",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.Color(0.1, 0.1, 0.1),
        ))
        _add_or_replace(ParagraphStyle(
            name="SmallText",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.Color(0.3, 0.3, 0.3),
            leading=10,
        ))
        _add_or_replace(ParagraphStyle(
            name="ConfirmedStatus",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.Color(0.0, 0.5, 0.0),
        ))
        _add_or_replace(ParagraphStyle(
            name="RouteDisplay",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=colors.Color(*self.PRIMARY_COLOR),
            alignment=TA_CENTER,
        ))
        _add_or_replace(ParagraphStyle(
            name="CityName",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.Color(0.3, 0.3, 0.3),
            alignment=TA_CENTER,
        ))
        _add_or_replace(ParagraphStyle(
            name="TimeDisplay",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.Color(0.1, 0.1, 0.1),
            alignment=TA_CENTER,
        ))
        _add_or_replace(ParagraphStyle(
            name="DateDisplay",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.Color(0.3, 0.3, 0.3),
            alignment=TA_CENTER,
        ))
        _add_or_replace(ParagraphStyle(
            name="FooterText",
            fontName="Helvetica",
            fontSize=7,
            textColor=colors.Color(0.5, 0.5, 0.5),
            leading=9,
        ))
        _add_or_replace(ParagraphStyle(
            name="FieldValueRight",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.Color(0.1, 0.1, 0.1),
            alignment=TA_RIGHT,
        ))
        _add_or_replace(ParagraphStyle(
            name="FieldLabelRight",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.Color(0.4, 0.4, 0.4),
            alignment=TA_RIGHT,
        ))
        _add_or_replace(ParagraphStyle(
            name="MonoValue",
            fontName="Courier-Bold",
            fontSize=9,
            textColor=colors.Color(0.1, 0.1, 0.1),
        ))

    def generate_pdf(self, booking: Booking) -> bytes:
        """Generate complete PDF for a booking. Returns PDF bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.PAGE_MARGINS[0],
            rightMargin=self.PAGE_MARGINS[1],
            topMargin=self.PAGE_MARGINS[2],
            bottomMargin=self.PAGE_MARGINS[3],
        )

        story = []
        story.extend(self._build_header(booking))
        story.append(Spacer(1, 6 * mm))
        story.extend(self._build_booking_summary(booking))
        story.append(Spacer(1, 6 * mm))

        for i, segment in enumerate(booking.segments):
            label = "OUTBOUND FLIGHT" if i == 0 else "RETURN FLIGHT"
            story.extend(self._build_flight_segment(segment, label))
            story.append(Spacer(1, 6 * mm))

        story.extend(self._build_passenger_details(booking))
        story.append(Spacer(1, 6 * mm))
        story.extend(self._build_payment_summary(booking))
        story.append(Spacer(1, 8 * mm))
        story.extend(self._build_important_info(booking))
        story.append(Spacer(1, 6 * mm))
        story.extend(self._build_barcode_footer(booking))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _build_header(self, booking: Booking) -> list:
        """Build the airline header with logo area and booking reference."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        # Colored header bar
        header_box = ColoredBox(
            page_width, 18 * mm,
            colors.Color(*self.HEADER_BG),
            text=self.AIRLINE_NAME.upper(),
            text_color=colors.white,
            font_size=14,
        )
        elements.append(header_box)
        elements.append(Spacer(1, 4 * mm))

        # Title and booking reference row
        title_data = [
            [
                Paragraph("E-Ticket Confirmation / Itinerary Receipt",
                         ParagraphStyle("TitleLeft", parent=self.styles["SectionTitle"],
                                       fontSize=12, leftIndent=0)),
                Paragraph(f"Booking Reference: <b>{booking.booking_reference}</b>",
                         ParagraphStyle("RefRight", parent=self.styles["FieldValue"],
                                       alignment=TA_RIGHT,
                                       textColor=colors.Color(*self.PRIMARY_COLOR),
                                       fontSize=12)),
            ]
        ]
        title_table = Table(title_data, colWidths=[page_width * 0.6, page_width * 0.4])
        title_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
            ("LEFTPADDING", (0, 0), (0, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(title_table)

        return elements

    def _build_booking_summary(self, booking: Booking) -> list:
        """Build booking summary section."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        data = [
            [
                Paragraph("Status", self.styles["FieldLabel"]),
                Paragraph("Booking Date", self.styles["FieldLabel"]),
                Paragraph("Passengers", self.styles["FieldLabel"]),
                Paragraph("Trip Type", self.styles["FieldLabel"]),
            ],
            [
                Paragraph("✓ Confirmed", self.styles["ConfirmedStatus"]),
                Paragraph(booking.booking_date.strftime("%d %b %Y"), self.styles["FieldValue"]),
                Paragraph(str(len(booking.passengers)), self.styles["FieldValue"]),
                Paragraph("Return" if booking.is_return else "One Way", self.styles["FieldValue"]),
            ],
        ]

        col_w = page_width / 4
        t = Table(data, colWidths=[col_w] * 4)
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(t)
        return elements

    def _build_flight_segment(self, segment: FlightSegment, label: str) -> list:
        """Build a flight segment display block."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        # Section header
        section_box = ColoredBox(
            page_width, 8 * mm,
            colors.Color(*self.PRIMARY_COLOR),
            text=label,
            text_color=colors.white,
            font_size=9,
        )
        elements.append(section_box)
        elements.append(Spacer(1, 4 * mm))

        # Route display: DEP -----> ARR
        dep_time = segment.departure_datetime.strftime("%H:%M")
        arr_time = segment.arrival_datetime.strftime("%H:%M")
        dep_date = segment.departure_datetime.strftime("%a, %d %b %Y")
        arr_date = segment.arrival_datetime.strftime("%a, %d %b %Y")

        route_data = [
            [
                Paragraph(dep_time, self.styles["TimeDisplay"]),
                Paragraph("━━━━━━━━✈", ParagraphStyle(
                    "Arrow", parent=self.styles["RouteDisplay"], fontSize=14)),
                Paragraph(arr_time, self.styles["TimeDisplay"]),
            ],
            [
                Paragraph(segment.departure_airport, self.styles["RouteDisplay"]),
                Paragraph(segment.duration_str, self.styles["CityName"]),
                Paragraph(segment.arrival_airport, self.styles["RouteDisplay"]),
            ],
            [
                Paragraph(segment.departure_city, self.styles["CityName"]),
                Paragraph("Direct", self.styles["CityName"]),
                Paragraph(segment.arrival_city, self.styles["CityName"]),
            ],
            [
                Paragraph(dep_date, self.styles["DateDisplay"]),
                Paragraph("", self.styles["CityName"]),
                Paragraph(arr_date, self.styles["DateDisplay"]),
            ],
        ]

        col_w = page_width / 3
        route_table = Table(route_data, colWidths=[col_w] * 3)
        route_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            # Extra space below the large airport code row
            ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
            ("TOPPADDING", (0, 2), (-1, 2), 4),
        ]))
        elements.append(route_table)
        elements.append(Spacer(1, 4 * mm))

        # Flight details — 2 rows of 4 columns for better readability
        terminal_dep = f"Terminal {segment.departure_terminal}" if segment.departure_terminal else "—"
        terminal_arr = f"Terminal {segment.arrival_terminal}" if segment.arrival_terminal else "—"

        details_row1 = [
            [
                Paragraph("Flight", self.styles["FieldLabel"]),
                Paragraph("Aircraft", self.styles["FieldLabel"]),
                Paragraph("Class", self.styles["FieldLabel"]),
                Paragraph("Status", self.styles["FieldLabel"]),
            ],
            [
                Paragraph(segment.flight_number, self.styles["FieldValue"]),
                Paragraph(segment.aircraft_type or "—", self.styles["FieldValue"]),
                Paragraph(f"{segment.cabin_class} ({segment.booking_class})",
                         self.styles["FieldValue"]),
                Paragraph(segment.status, self.styles["ConfirmedStatus"]),
            ],
        ]

        det_widths_r1 = [page_width * 0.20, page_width * 0.35, page_width * 0.25, page_width * 0.20]
        det_table1 = Table(details_row1, colWidths=det_widths_r1)
        det_table1.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(det_table1)
        elements.append(Spacer(1, 2 * mm))

        details_row2 = [
            [
                Paragraph("Departure Terminal", self.styles["FieldLabel"]),
                Paragraph("Arrival Terminal", self.styles["FieldLabel"]),
            ],
            [
                Paragraph(terminal_dep, self.styles["FieldValue"]),
                Paragraph(terminal_arr, self.styles["FieldValue"]),
            ],
        ]

        det_widths_r2 = [page_width * 0.50, page_width * 0.50]
        det_table2 = Table(details_row2, colWidths=det_widths_r2)
        det_table2.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.Color(0.85, 0.85, 0.85)),
        ]))
        elements.append(det_table2)

        return elements

    def _build_passenger_details(self, booking: Booking) -> list:
        """Build passenger information table."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        elements.append(Paragraph("PASSENGER DETAILS", self.styles["SectionTitle"]))
        elements.append(Spacer(1, 2 * mm))

        header = [
            Paragraph("Passenger", self.styles["FieldLabel"]),
            Paragraph("Ticket Number", self.styles["FieldLabel"]),
            Paragraph("Seat", self.styles["FieldLabel"]),
            Paragraph("Status", self.styles["FieldLabel"]),
        ]

        rows = [header]
        for pax in booking.passengers:
            rows.append([
                Paragraph(pax.display_name, self.styles["FieldValue"]),
                Paragraph(pax.ticket_number or "—", self.styles["MonoValue"]),
                Paragraph(pax.seat or "—", self.styles["FieldValue"]),
                Paragraph("Confirmed", self.styles["ConfirmedStatus"]),
            ])

        col_widths = [page_width * 0.35, page_width * 0.30, page_width * 0.15, page_width * 0.20]
        pax_table = Table(rows, colWidths=col_widths)
        pax_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.Color(*self.PRIMARY_COLOR)),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.97)),
        ]))
        elements.append(pax_table)
        return elements

    def _build_payment_summary(self, booking: Booking) -> list:
        """Build payment/fare summary."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        elements.append(Paragraph("FARE SUMMARY", self.styles["SectionTitle"]))
        elements.append(Spacer(1, 2 * mm))

        num_pax = len(booking.passengers)
        per_pax = booking.total_price / num_pax if num_pax > 0 else booking.total_price
        currency_symbol = {"GBP": "£", "EUR": "€", "USD": "$"}.get(booking.currency, booking.currency + " ")

        fare_data = [
            [
                Paragraph("Description", self.styles["FieldLabel"]),
                Paragraph("Passengers", self.styles["FieldLabel"]),
                Paragraph("Amount", self.styles["FieldLabelRight"]),
            ],
            [
                Paragraph(f"Air fare ({booking.outbound.cabin_class})", self.styles["FieldValue"]),
                Paragraph(f"{num_pax} Adult(s)", self.styles["FieldValue"]),
                Paragraph(f"{currency_symbol}{per_pax * num_pax:.2f}", self.styles["FieldValueRight"]),
            ],
            [
                Paragraph("Taxes & Surcharges", self.styles["FieldValue"]),
                Paragraph("", self.styles["FieldValue"]),
                Paragraph("Included", self.styles["FieldValueRight"]),
            ],
        ]

        # Total row
        fare_data.append([
            Paragraph("<b>Total</b>", self.styles["FieldValue"]),
            Paragraph("", self.styles["FieldValue"]),
            Paragraph(f"<b>{currency_symbol}{booking.total_price:.2f}</b>",
                     ParagraphStyle("TotalPrice", parent=self.styles["FieldValue"],
                                   fontSize=12,
                                   alignment=TA_RIGHT,
                                   textColor=colors.Color(*self.PRIMARY_COLOR))),
        ])

        col_widths = [page_width * 0.50, page_width * 0.25, page_width * 0.25]
        fare_table = Table(fare_data, colWidths=col_widths)
        fare_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.Color(*self.PRIMARY_COLOR)),
            ("LINEBELOW", (0, -2), (-1, -2), 0.5, colors.Color(0.85, 0.85, 0.85)),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.Color(*self.PRIMARY_COLOR)),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.97)),
        ]))
        elements.append(fare_table)
        return elements

    def _build_important_info(self, booking: Booking) -> list:
        """Build important information/terms section."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        elements.append(Paragraph("IMPORTANT INFORMATION", self.styles["SectionTitle"]))
        elements.append(Spacer(1, 2 * mm))

        info_lines = self._get_important_info_text(booking)
        for line in info_lines:
            elements.append(Paragraph(f"• {line}", self.styles["SmallText"]))
            elements.append(Spacer(1, 1 * mm))

        return elements

    def _get_important_info_text(self, booking: Booking) -> list[str]:
        """Override in subclass for airline-specific info. Default generic text."""
        return [
            "Please check in online at least 24 hours before departure to avoid airport queues.",
            "Carry a valid passport with at least 6 months validity beyond your travel date.",
            f"Baggage allowance: 1 cabin bag (max 7kg) + 1 checked bag (23kg) for {booking.outbound.cabin_class} class.",
            "Arrive at the airport at least 2 hours before departure for international flights.",
            "This e-ticket receipt is your confirmation of booking. Please carry a printed or digital copy.",
            "For visa applications: this document confirms a valid flight reservation with the airline.",
            "Flight times are shown in local time. Please check for any time zone differences.",
            "The airline reserves the right to change flight times. Check the airline website for the latest schedule.",
        ]

    def _build_barcode_footer(self, booking: Booking) -> list:
        """Build barcode and footer section."""
        elements = []
        page_width = A4[0] - self.PAGE_MARGINS[0] - self.PAGE_MARGINS[1]

        # Barcode + human-readable e-ticket number for the passenger (centered)
        if booking.passengers and booking.passengers[0].ticket_number:
            pax0 = booking.passengers[0]
            try:
                barcode_bytes = generate_ticket_barcode(pax0.ticket_number)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                tmp.write(barcode_bytes)
                tmp.close()
                barcode_img = Image(tmp.name, width=70 * mm, height=14 * mm)
                barcode_img.hAlign = "CENTER"
                elements.append(barcode_img)
                elements.append(Paragraph(
                    f"e-Ticket {pax0.ticket_number}",
                    ParagraphStyle("TicketNo", parent=self.styles["SmallText"],
                                   fontName="Courier-Bold", fontSize=9,
                                   alignment=TA_CENTER,
                                   textColor=colors.Color(0.1, 0.1, 0.1)),
                ))
                elements.append(Spacer(1, 3 * mm))
            except Exception:
                pass

        # Footer
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                   color=colors.Color(0.8, 0.8, 0.8)))
        elements.append(Spacer(1, 2 * mm))

        footer_text = (
            f"This is an electronically generated document and does not require a signature. "
            f"Booking reference: {booking.booking_reference} | "
            f"Issued by: {self.AIRLINE_NAME} | "
            f"Date of issue: {booking.booking_date.strftime('%d %B %Y')}"
        )
        elements.append(Paragraph(footer_text, self.styles["FooterText"]))

        return elements
