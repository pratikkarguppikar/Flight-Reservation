"""Flight Reservation PDF Generator — guided Streamlit flow.

Flow: trip type -> route & dates -> search -> select outbound (and return) ->
number of tickets -> passenger details -> one e-ticket PDF per passenger.
"""

import io
import sys
import zipfile
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from datetime import date, datetime, timedelta

from models.booking import Booking, FlightSegment, Passenger
from generators.pdf_generator import (
    generate_booking_pdf, get_all_airports, get_terminal_for_airport,
)
from generators.pnr_generator import generate_pnr, generate_ticket_number, airline_ticket_prefix
from generators.local_flights import (
    search_local_flights, get_origins, get_destinations_from,
)
from generators.flight_search import search_flights, is_configured
from generators.duffel_search import search_duffel_flights, has_duffel_credentials


# --- Page config ---
st.set_page_config(page_title="Flight Reservation Generator", page_icon="✈️", layout="wide")

st.markdown("""
<style>
    .stApp {max-width: 1150px; margin: 0 auto;}
</style>
""", unsafe_allow_html=True)

# --- Load reference data ---
airports = get_all_airports()
airport_options = {f"{a['code']} — {a['name']} ({a['city']})": a for a in airports}
airport_code_to_key = {a["code"]: f"{a['code']} — {a['name']} ({a['city']})" for a in airports}
airport_by_code = {a["code"]: a for a in airports}

# --- Session state ---
_DEFAULTS = {
    "selected_flight": None,
    "selected_return_flight": None,
    "search_results": None,
    "return_results": None,
    "flight_source": "local",
    "was_return": False,
    "generated": None,
}
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


# =============================================================================
# Helpers
# =============================================================================
def fetch_flights(origin, destination, departure_date):
    """Return (results, source) preferring live providers, falling back to the local timetable."""
    if has_duffel_credentials():
        try:
            return search_duffel_flights(origin, destination, departure_date), "duffel"
        except Exception as e:
            st.warning(f"Duffel search unavailable ({e}). Trying next source.")
    if is_configured():
        try:
            return search_flights(origin=origin, destination=destination, departure_date=departure_date), "amadeus"
        except Exception as e:
            st.warning(f"Amadeus search unavailable ({e}). Showing built-in timetable data.")
    return search_local_flights(origin, destination, departure_date), "local"


def _source_badge(src):
    return {"duffel": "🟢 Live (Duffel)", "amadeus": "🟢 Live (Amadeus)"}.get(src, "📋 Timetable data")


def _flight_key(f):
    return f"{f.airline_code}|{f.flight_number}|{f.departure_datetime.isoformat()}|{f.arrival_datetime.isoformat()}"


def _dedupe(results):
    """Collapse duplicate offers for the same flight, keeping the cheapest."""
    best = {}
    for f in results:
        k = _flight_key(f)
        if k not in best or f.price < best[k].price:
            best[k] = f
    return sorted(best.values(), key=lambda r: (r.stops, r.departure_datetime))


def _reset_selection():
    st.session_state.selected_flight = None
    st.session_state.selected_return_flight = None
    st.session_state.generated = None


def _to_segment(flight):
    """Convert a FlightResult into a FlightSegment for the PDF booking model."""
    dep = airport_by_code.get(flight.departure_airport, {})
    arr = airport_by_code.get(flight.arrival_airport, {})
    dep_term = flight.departure_terminal or get_terminal_for_airport(flight.airline_code, flight.departure_airport)
    arr_term = flight.arrival_terminal or get_terminal_for_airport(flight.airline_code, flight.arrival_airport)
    return FlightSegment(
        airline_code=flight.airline_code or "XX",
        airline_name=flight.airline_name or flight.airline_code or "Airline",
        flight_number=flight.flight_number or f"{flight.airline_code}000",
        departure_airport=flight.departure_airport,
        departure_city=dep.get("city", flight.departure_airport),
        departure_terminal=dep_term,
        arrival_airport=flight.arrival_airport,
        arrival_city=arr.get("city", flight.arrival_airport),
        arrival_terminal=arr_term,
        departure_datetime=flight.departure_datetime,
        arrival_datetime=flight.arrival_datetime,
        cabin_class=flight.cabin_class or "Economy",
        booking_class=(flight.booking_class or "Y").upper()[:1],
        aircraft_type=flight.aircraft_type or None,
    )


def _currency_symbol(cur):
    return {"GBP": "£", "EUR": "€", "USD": "$"}.get(cur, f"{cur} ")


def render_flight_list(results, kind):
    """Render selectable flight cards. kind is 'out' or 'ret'."""
    state_key = "selected_flight" if kind == "out" else "selected_return_flight"
    selected = st.session_state.get(state_key)
    sel_key = _flight_key(selected) if selected else None

    for idx, f in enumerate(results):
        is_sel = sel_key == _flight_key(f)
        sym = _currency_symbol(f.currency)
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([2.2, 2.2, 1.8, 1.3, 1.4])
            with c1:
                st.markdown(f"**{f.airline_name}**")
                st.caption(f"{f.flight_number} · {f.aircraft_type or '—'}")
            with c2:
                st.markdown(f"**{f.departure_datetime.strftime('%H:%M')}** → **{f.arrival_datetime.strftime('%H:%M')}**")
                st.caption(f"{f.departure_airport} → {f.arrival_airport} · {f.departure_datetime.strftime('%d %b')}")
            with c3:
                st.markdown(f.duration_display)
                st.caption(("🟢 " if f.stops == 0 else "🟡 ") + f.stops_display)
            with c4:
                st.markdown(f"**{sym}{f.price:.0f}**")
                st.caption(f.cabin_class)
            with c5:
                if is_sel:
                    st.button("✅ Selected", key=f"{kind}_{idx}", disabled=True, use_container_width=True)
                elif st.button("Select", key=f"{kind}_{idx}", use_container_width=True):
                    st.session_state[state_key] = f
                    st.session_state.generated = None
                    st.rerun()


# =============================================================================
# Header
# =============================================================================
st.title("✈️ Flight Reservation PDF Generator")
st.caption("Search flights, pick your itinerary, add travellers, and get one e-ticket PDF per passenger.")

# =============================================================================
# Step 1 — Trip, route & dates
# =============================================================================
st.subheader("1 · Trip & route")

if has_duffel_credentials():
    st.caption("Live search via Duffel — falls back to built-in timetable data if unavailable.")
elif is_configured():
    st.caption("Live search via Amadeus — falls back to built-in timetable data if unavailable.")
else:
    st.caption("Using built-in timetable data. Add a Duffel or Amadeus API key for live search.")

trip_type = st.segmented_control("Trip type", options=["One way", "Return"], default="One way", key="trip_type")
is_return = trip_type == "Return"

origin_display = [airport_code_to_key[c] for c in get_origins() if c in airport_code_to_key]

with st.container(border=True):
    r1, r2 = st.columns(2)
    with r1:
        search_from = st.selectbox("✈️ From", options=origin_display, index=0, key="search_from")
        from_code = airport_options[search_from]["code"]
    with r2:
        dest_codes = get_destinations_from(from_code)
        dest_display = [airport_code_to_key[c] for c in dest_codes if c in airport_code_to_key]
        options_to = dest_display or list(airport_options.keys())
        search_to = st.selectbox("🛬 To", options=options_to, index=0, key="search_to")
        to_code = airport_options[search_to]["code"]

    if is_return:
        d1, d2 = st.columns(2)
        with d1:
            dep_date = st.date_input("📅 Departure", value=date.today() + timedelta(days=30),
                                     min_value=date.today(), key="search_dep_date")
        with d2:
            ret_date = st.date_input("📅 Return", value=date.today() + timedelta(days=37),
                                     min_value=date.today(), key="search_ret_date")
    else:
        dep_date = st.date_input("📅 Departure", value=date.today() + timedelta(days=30),
                                 min_value=date.today(), key="search_dep_date")
        ret_date = None

if st.button("🔎 Search flights", type="primary", use_container_width=True):
    if is_return and ret_date and ret_date < dep_date:
        st.error("Return date can't be before the departure date.")
    else:
        _reset_selection()
        with st.spinner("Searching for flights…"):
            out_results, source = fetch_flights(from_code, to_code, dep_date)
            out_results = _dedupe(out_results)
            st.session_state.search_results = out_results
            st.session_state.flight_source = source
            st.session_state.was_return = is_return
            if is_return and ret_date:
                ret_results, _ = fetch_flights(to_code, from_code, ret_date)
                st.session_state.return_results = _dedupe(ret_results)
            else:
                st.session_state.return_results = None
        st.toast(f"Found {len(out_results)} outbound flight(s).", icon="✈️")

# =============================================================================
# Step 2 — Select flights
# =============================================================================
results = st.session_state.search_results
if results is not None:
    st.subheader("2 · Choose your flight" + ("s" if st.session_state.was_return else ""))
    badge = _source_badge(st.session_state.flight_source)

    st.markdown(f"**Outbound** · {badge}")
    if results:
        render_flight_list(results, "out")
    else:
        st.info("No flights found for this route. Try different cities or dates.")

    if st.session_state.was_return:
        st.markdown("---")
        st.markdown(f"**Return** · {badge}")
        ret_results = st.session_state.return_results
        if ret_results:
            render_flight_list(ret_results, "ret")
        else:
            st.info("No return flights found for this route.")

    # Selection summary
    out_sel = st.session_state.selected_flight
    ret_sel = st.session_state.selected_return_flight
    if out_sel:
        sym = _currency_symbol(out_sel.currency)
        msg = (f"**Outbound selected:** {out_sel.airline_name} {out_sel.flight_number} · "
               f"{out_sel.departure_airport}→{out_sel.arrival_airport} · "
               f"{out_sel.departure_datetime.strftime('%d %b %H:%M')} · {sym}{out_sel.price:.0f}")
        if st.session_state.was_return and ret_sel:
            msg += (f"\n\n**Return selected:** {ret_sel.airline_name} {ret_sel.flight_number} · "
                    f"{ret_sel.departure_airport}→{ret_sel.arrival_airport} · "
                    f"{ret_sel.departure_datetime.strftime('%d %b %H:%M')} · {sym}{ret_sel.price:.0f}")
        st.success(msg)

# Whether the itinerary is complete enough to continue
ready = st.session_state.selected_flight is not None and (
    not st.session_state.was_return or st.session_state.selected_return_flight is not None
)
if results is not None and not ready:
    if st.session_state.was_return:
        st.info("Select both an outbound and a return flight to continue.")
    else:
        st.info("Select a flight to continue.")

# =============================================================================
# Step 3 — Passengers
# =============================================================================
if ready:
    st.subheader("3 · Passengers")
    num_pax = st.number_input("Number of tickets", min_value=1, max_value=9, value=1, step=1)

    passengers_data = []
    with st.container(border=True):
        for i in range(int(num_pax)):
            st.markdown(f"**Passenger {i + 1}**")
            p1, p2, p3 = st.columns([1, 2, 2])
            with p1:
                title = st.selectbox("Title", ["Mr", "Mrs", "Ms", "Miss", "Dr"], key=f"title_{i}")
            with p2:
                first_name = st.text_input("First name", key=f"first_{i}", placeholder="John")
            with p3:
                last_name = st.text_input("Last name", key=f"last_{i}", placeholder="Smith")
            passengers_data.append({"title": title, "first_name": first_name.strip(), "last_name": last_name.strip()})
            if i < int(num_pax) - 1:
                st.divider()

    # =========================================================================
    # Step 4 — Generate one PDF per passenger
    # =========================================================================
    st.subheader("4 · Generate e-tickets")
    st.caption("Each passenger gets their own PDF with a unique ticket number and barcode, sharing the same booking reference (PNR).")

    if st.button("🎫 Generate e-tickets", type="primary", use_container_width=True):
        if not all(p["first_name"] and p["last_name"] for p in passengers_data):
            st.error("Every passenger needs a first and last name.")
        else:
            out = st.session_state.selected_flight
            ret = st.session_state.selected_return_flight if st.session_state.was_return else None
            segments = [_to_segment(out)] + ([_to_segment(ret)] if ret else [])

            pnr = generate_pnr()
            prefix = airline_ticket_prefix(out.airline_code)
            total_price = out.price + (ret.price if ret else 0)

            items = []
            with st.spinner("Generating e-tickets…"):
                for p in passengers_data:
                    pax = Passenger(
                        title=p["title"], first_name=p["first_name"], last_name=p["last_name"],
                        ticket_number=generate_ticket_number(prefix),
                    )
                    booking = Booking(
                        booking_reference=pnr,
                        airline_code=out.airline_code or "XX",
                        airline_name=out.airline_name or "Airline",
                        passengers=[pax],
                        segments=segments,
                        booking_date=date.today(),
                        total_price=total_price,
                        currency=out.currency,
                    )
                    pdf_bytes = generate_booking_pdf(booking)
                    fname = f"E-Ticket_{pnr}_{p['last_name']}_{p['first_name']}.pdf".replace(" ", "_")
                    items.append({"name": pax.full_name, "file": fname, "bytes": pdf_bytes})

                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for it in items:
                        zf.writestr(it["file"], it["bytes"])

            st.session_state.generated = {
                "pnr": pnr,
                "items": items,
                "zip": zip_buf.getvalue(),
                "route": f"{out.departure_airport} → {out.arrival_airport}",
            }

# =============================================================================
# Downloads (persist across reruns)
# =============================================================================
gen = st.session_state.generated
if gen:
    st.success(f"✅ Generated {len(gen['items'])} e-ticket(s) · Booking reference **{gen['pnr']}** · {gen['route']}")

    if len(gen["items"]) > 1:
        st.download_button(
            "📦 Download all (ZIP)", data=gen["zip"],
            file_name=f"E-Tickets_{gen['pnr']}.zip", mime="application/zip",
            type="primary", use_container_width=True,
        )

    for i, it in enumerate(gen["items"]):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{it['name']}**")
            st.caption(it["file"])
        with c2:
            st.download_button(
                "📥 Download", data=it["bytes"], file_name=it["file"],
                mime="application/pdf", key=f"dl_{i}", use_container_width=True,
            )
