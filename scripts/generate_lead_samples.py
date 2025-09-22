import json
import random
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent / 'leads'
ENQUIRY_DIR = BASE_DIR / 'enquiry'
QUOTE_DIR = BASE_DIR / 'quote'
BOOKING_DIR = BASE_DIR / 'booking'

RECORD_FILENAME = 'record.json'
TARGET_PER_TYPE = 50

random.seed(20240922)

FIRST_NAMES = [
    "Avery", "Jordan", "Morgan", "Sydney", "Harper", "Kai", "Rowan", "Sloane", "Drew", "Parker",
    "Logan", "Emerson", "Riley", "Campbell", "Jules", "Elliott", "Blair", "Reese", "Arden", "Sawyer",
    "Finley", "Hayden", "Marlow", "River", "Spencer", "Teagan", "Quinn", "Lennox", "Tatum", "Luca",
    "Monroe", "Sage", "Peyton", "Hendrix", "Frankie", "Dakota", "Hollis", "Indy", "Larkin", "Micah",
    "Nico", "Oakley", "Presley", "Shiloh", "Tristan", "Vale", "Winter", "Zephyr", "Callie", "Rumi",
    "Selene", "Atlas", "Imogen", "Arlo", "Remy", "Mila", "Ezra", "Isla", "Jasper", "Kaia"
]
LAST_NAMES = [
    "Cole", "Reid", "Hayes", "Bennett", "Lennon", "Ellis", "Remy", "Sutton", "Wilder", "Bright",
    "Calloway", "Decker", "Everett", "Fletcher", "Gray", "Harlow", "Iverson", "Jensen", "Keaton", "Lang",
    "Maddox", "Nash", "Orion", "Pryor", "Rhodes", "Sterling", "Thatcher", "Vale", "West", "York",
    "Abbott", "Barlow", "Carmichael", "Dalton", "Easton", "Falcon", "Galloway", "Hawkins", "Irving", "Jameson",
    "Kingsley", "Locke", "Montgomery", "North", "Oakwood", "Prescott", "Quill", "Rockwell", "Sinclair", "Tennyson"
]
DESTINATIONS = [
    "Lisbon & Azores", "Seoul & Busan", "Copenhagen & Faroe Islands", "Santorini", "Reykjavik & Golden Circle",
    "Cape Town & Winelands", "New York City", "Kyoto", "Queenstown", "Bali", "Barcelona", "Amalfi Coast",
    "Marrakesh", "Vancouver", "Banff", "Buenos Aires", "Patagonia", "Sydney", "Melbourne", "Fiji",
    "Edinburgh & Highlands", "Prague & Vienna", "Dubrovnik", "Iceland Ring Road", "Swiss Alps", "Tokyo",
    "Osaka", "Kyushu", "Sicily", "Provence", "Tuscany", "Geneva & Montreux", "Istanbul", "Cairo", "Amman & Petra",
    "Zanzibar", "Phuket", "Hoi An", "Koh Samui", "Queenstown & Milford Sound", "Paris", "London", "Dublin",
    "Berlin", "Morocco Desert Circuit", "Kenyan Safari", "Canadian Rockies", "Norwegian Fjords", "Hawaii Islands", "Yosemite & Napa"
]
REGIONS = [
    "Mediterranean", "Nordic", "Australasia", "Pacific", "North America", "South America", "Africa",
    "South-East Asia", "East Asia", "Middle East", "Europe", "United Kingdom", "Indian Ocean"
]
LOCATIONS = [
    "Sydney", "Melbourne", "Queenstown", "Tokyo", "Kyoto", "Seoul", "Osaka", "Lisbon", "Madrid",
    "Barcelona", "Rome", "Florence", "Venice", "Santorini", "Athens", "Copenhagen", "Reykjavik",
    "Edinburgh", "Dublin", "London", "Paris", "Provence", "Nice", "Zurich", "Interlaken", "Cape Town",
    "Marrakesh", "Nairobi", "Zanzibar", "Queenstown", "Auckland", "Honolulu", "Maui", "Banff",
    "Vancouver", "Montreal", "New York", "Los Angeles", "San Francisco", "Buenos Aires", "Cusco",
    "Patagonia", "Istanbul", "Amman", "Petra", "Dubai", "Abu Dhabi", "Doha", "Singapore"
]
HOTELS = [
    "Aurora Sky Lodge", "Harbourlight Residences", "Summit Ridge Retreat", "Azure View Villas",
    "Cedar & Stone Resort", "Lagoon Horizon Suites", "Atlas Grand Hotel", "Velvet Sands Resort",
    "Northern Lights Chalet", "Seascape Collection", "Verve Urban Retreat", "Palm Grove Villas"
]
ROOM_TYPES = [
    "Oceanview Suite", "Panoramic King", "Garden Residence", "Family Loft", "Skyline Penthouse",
    "Lagoon Villa", "Grand Deluxe Room", "Club Level Suite", "Boutique Apartment", "Mountain Chalet"
]
BOARD_OPTIONS = ["Room Only", "Bed and Breakfast", "Half Board", "Full Board", "All Inclusive"]
AIRLINES = ["QF", "SQ", "VA", "NZ", "CX", "BA", "AF", "EK", "QR", "UA", "DL", "AA", "JL", "NH"]
AIRPORTS = ["SYD", "MEL", "AKL", "CHC", "NAN", "BKK", "HKG", "SIN", "LAX", "SFO", "JFK", "LHR", "CDG", "AMS"]
SERVICE_TYPES = ["Transfer", "Tour", "Activity", "Dining", "Cruise", "Rail", "Spa"]
SERVICE_DESCRIPTIONS = [
    "Private transfer between airport and hotel",
    "Guided city highlights experience",
    "Sunset sailing with canapes",
    "Local cooking masterclass",
    "Exclusive wine tasting",
    "Wellness spa circuit",
    "Private museum after-hours tour"
]
CURRENCIES = ["AUD", "USD", "EUR", "GBP", "NZD", "JPY", "SGD"]
PAYMENT_METHODS = ["Credit Card", "Bank Transfer", "Cash", "Wire Transfer", "PayPal"]
STATUS_STAGES = ["Deposited", "Booked", "Completed", "Cancelled"]
NOTES_OPTIONS = [
    "Interested in boutique stays and local food tours.",
    "Needs fully accessible lodging and transfers.",
    "Celebrating milestone anniversary, wants luxury touches.",
    "Flexible on dates but keen on shoulder-season pricing.",
    "Prefers eco-certified experiences and guided hikes.",
    "Traveling with teens; wants adventure options.",
    "Requesting first-class flights and private transfers.",
    "Focus on culinary classes and wine tastings.",
    "Seeks combination of wellness and cultural immersion.",
    "Needs pet-friendly villas and chauffeur services.",
    None,
]
ASSISTANT_NOTES = [
    None,
    "Client prefers premium cabin flights when available.",
    "Keep an eye on shoulder-season promos for this route.",
    "Add welcome amenities to wow the guest on arrival.",
    "Coordinate with local concierge partners for bespoke tours.",
]
COMMUNICATION_METHODS = ["Email", "Call", "SMS"]
DIRECTIONS = ["incoming", "outgoing"]
FOLLOW_UP_NOTES = [
    "Followed up on preferred travel dates.",
    "Sent initial itinerary draft for review.",
    "Client requested pricing for business class.",
    "Discussed resort options and dining credits.",
    "Confirmed availability with local guide.",
    "Shared weather insights for target window.",
    ""
]

START_SUBMITTED = datetime(2025, 6, 1)
END_SUBMITTED = datetime(2025, 9, 21, 23, 59, 59)

TRIP_START = datetime(2025, 9, 1)
TRIP_END = datetime(2026, 12, 31)


def reset_directory(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for child in directory.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def random_datetime(start: datetime, end: datetime) -> datetime:
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))


def random_time() -> str:
    hour = random.randint(6, 22)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"


def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(name: str) -> str:
    first, last = name.split()
    domain = random.choice(["skydesk.test", "travellab.io", "example.com", "voyagersuite.au"])
    return f"{first.lower()}.{last.lower()}@{domain}"


def random_phone() -> str:
    return f"04{random.randint(10**8, 10**9 - 1)}"


def maybe_note(options):
    note = random.choice(options)
    return note if note else None


def ensure_double_newlines(text: str) -> str:
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text


def build_communications(submitted_at: datetime):
    if random.random() < 0.5:
        return None
    entries = []
    for _ in range(random.randint(1, 2)):
        when = submitted_at + timedelta(days=random.randint(1, 12), hours=random.randint(0, 22))
        entries.append(
            {
                "timestamp": when.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "method": random.choice(COMMUNICATION_METHODS),
                "direction": random.choice(DIRECTIONS),
                "note": random.choice(FOLLOW_UP_NOTES) or None,
            }
        )
    return entries


def generate_enquiries() -> None:
    reset_directory(ENQUIRY_DIR)
    created = 0
    while created < TARGET_PER_TYPE:
        submitted_at = random_datetime(START_SUBMITTED, END_SUBMITTED)
        record_id = f"{submitted_at.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex}"
        record_dir = ENQUIRY_DIR / record_id
        if record_dir.exists():
            continue
        record_dir.mkdir(parents=True, exist_ok=True)

        travellers = {
            "adults": random.randint(1, 3),
            "children": random.randint(0, 2),
            "infants": random.choice([0, 0, 1])
        }

        if random.random() < 0.55:
            departure = submitted_at + timedelta(days=random.randint(35, 160))
            length_days = random.randint(5, 18)
            return_date = departure + timedelta(days=length_days)
            schedule = {
                "departure_date": departure.strftime('%Y-%m-%d'),
                "return_date": return_date.strftime('%Y-%m-%d'),
                "flex_month": None,
                "flex_month_month": None,
                "flex_month_year": None,
                "trip_length_value": length_days,
                "trip_length_unit": "days",
            }
        else:
            month = f"{random.randint(1, 12):02d}"
            year = str(random.choice([2025, 2026]))
            schedule = {
                "departure_date": None,
                "return_date": None,
                "flex_month": f"{month}/{year}",
                "flex_month_month": month,
                "flex_month_year": year,
                "trip_length_value": random.choice([7, 10, 14, 21]),
                "trip_length_unit": random.choice(["days", "weeks"]),
            }

        name = random_name()
        payload = {
            "record_type": "enquiry",
            "submitted_at": submitted_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "name": name,
            "phone": random_phone(),
            "email": random_email(name),
            "destination": random.choice(DESTINATIONS),
            "travellers": travellers,
            "schedule": schedule,
            "notes": maybe_note(NOTES_OPTIONS),
        }

        comms = build_communications(submitted_at)
        if comms:
            payload["communications"] = comms

        with (record_dir / RECORD_FILENAME).open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=2)
        created += 1
    print(f"Created {created} enquiries")


def random_trip_dates():
    start = random_datetime(TRIP_START, TRIP_END - timedelta(days=3))
    nights = random.randint(5, 16)
    end = start + timedelta(days=nights)
    return start, end, nights


def build_trip():
    start, end, nights = random_trip_dates()
    regions = random.sample(REGIONS, k=random.randint(1, 2))
    locations = random.sample(LOCATIONS, k=random.randint(1, 3))
    return {
        "regions": regions,
        "locations": locations,
        "dates": {
            "start": start.strftime('%Y-%m-%d'),
            "end": end.strftime('%Y-%m-%d'),
            "nights": nights,
        },
    }, start, end, nights


def build_flights(start: datetime, end: datetime):
    flights = []
    legs = random.randint(2, 4)
    current_depart = start
    origin = random.choice(AIRPORTS)
    destination = random.choice([a for a in AIRPORTS if a != origin])
    for index in range(legs):
        carrier = random.choice(AIRLINES)
        route = f"{origin}-{destination}"
        depart_date = (current_depart + timedelta(days=random.randint(0, 2))).strftime('%Y-%m-%d')
        flight = {
            "description": f"{carrier} Flight {carrier}{random.randint(100, 999)} {origin} to {destination}",
            "carrier": carrier,
            "route": route,
            "depart_date": depart_date,
            "depart_time_local": random_time(),
            "arrive_time_local": random_time(),
            "pnr": random.choice([None, ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ', k=6))]),
            "ticket_numbers": [],
            "supplier_ref": None,
        }
        flights.append(flight)
        origin, destination = destination, random.choice([a for a in AIRPORTS if a != destination])
        current_depart += timedelta(days=random.randint(1, 5))
    # Ensure final leg returns near trip end
    flights[-1]["depart_date"] = end.strftime('%Y-%m-%d')
    return flights


def build_accommodation(start: datetime, nights: int):
    stays = []
    remaining_nights = nights
    current_start = start
    while remaining_nights > 0:
        stay_nights = min(remaining_nights, random.randint(3, 6))
        stay_end = current_start + timedelta(days=stay_nights)
        stays.append(
            {
                "name": random.choice(HOTELS),
                "check_in": current_start.strftime('%Y-%m-%d'),
                "check_out": stay_end.strftime('%Y-%m-%d'),
                "nights": stay_nights,
                "room_type": random.choice(ROOM_TYPES),
                "board": random.choice(BOARD_OPTIONS),
                "supplier_ref": None,
            }
        )
        current_start = stay_end
        remaining_nights -= stay_nights
    return stays


def build_services(start: datetime):
    services = []
    for _ in range(random.randint(0, 3)):
        service_day = start + timedelta(days=random.randint(1, 6))
        services.append(
            {
                "type": random.choice(SERVICE_TYPES),
                "description": random.choice(SERVICE_DESCRIPTIONS),
                "carrier": random.choice([None, random.choice(AIRLINES)]),
                "route": None,
                "depart_date": service_day.strftime('%Y-%m-%d'),
                "depart_time_local": random.choice([None, random_time()]),
                "arrive_time_local": None,
                "pnr": None,
                "ticket_numbers": [],
                "supplier_ref": None,
            }
        )
    return services


def build_other_pax(max_pax: int = 3):
    other_pax = []
    pax_types = ["ADT", "CNN", "INF"]
    for _ in range(random.randint(0, max_pax)):
        other_pax.append(
            {
                "name": random_name(),
                "pax_type": random.choice(pax_types),
            }
        )
    return other_pax


def generate_quotes() -> None:
    reset_directory(QUOTE_DIR)
    for index in range(TARGET_PER_TYPE):
        lead_id = f"7{random.randint(1000000, 9999999)}"
        while (QUOTE_DIR / lead_id).exists():
            lead_id = f"7{random.randint(1000000, 9999999)}"
        record_dir = QUOTE_DIR / lead_id
        record_dir.mkdir(parents=True, exist_ok=True)

        issued_at_dt = random_datetime(START_SUBMITTED, END_SUBMITTED)
        trip, start, end, nights = build_trip()
        flights = build_flights(start, end)
        accommodation = build_accommodation(start, nights)
        services = build_services(start)

        payload = {
            "record_type": "quote",
            "lead_id": lead_id,
            "issued_at": issued_at_dt.strftime('%d-%m-%Y'),
            "client": {"name": random_name()},
            "other_pax": build_other_pax(),
            "trip": trip,
            "accommodation": accommodation,
            "flights": flights,
            "services": services,
            "totals": {
                "grand_total": {
                    "amount": round(random.uniform(2500, 16000), 2),
                    "currency": random.choice(CURRENCIES),
                }
            },
            "notes": maybe_note(NOTES_OPTIONS),
            "assistant_notes": maybe_note(ASSISTANT_NOTES),
        }

        comms = build_communications(issued_at_dt)
        if comms:
            payload["communications"] = comms

        with (record_dir / RECORD_FILENAME).open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=2)
    print(f"Created {TARGET_PER_TYPE} quotes")


def generate_bookings() -> None:
    reset_directory(BOOKING_DIR)
    for index in range(TARGET_PER_TYPE):
        lead_id = f"8{random.randint(1000000, 9999999)}"
        while (BOOKING_DIR / lead_id).exists():
            lead_id = f"8{random.randint(1000000, 9999999)}"
        record_dir = BOOKING_DIR / lead_id
        record_dir.mkdir(parents=True, exist_ok=True)

        issued_at_dt = random_datetime(START_SUBMITTED, END_SUBMITTED)
        trip, start, end, nights = build_trip()
        flights = build_flights(start, end)
        accommodation = build_accommodation(start, nights)
        services = build_services(start)

        amount = round(random.uniform(3500, 24000), 2)
        balance = 0.0 if random.random() < 0.6 else round(amount * random.uniform(0.1, 0.4), 2)
        paid_amount = round(amount - balance, 2)
        currency = random.choice(CURRENCIES)

        payment_date = issued_at_dt + timedelta(days=random.randint(1, 20))
        transactions = [
            {
                "date": payment_date.strftime('%Y-%m-%d'),
                "amount": paid_amount,
                "currency": currency,
                "method": random.choice(PAYMENT_METHODS),
                "reference": random.choice([None, f"INV{random.randint(1000, 9999)}"]),
            }
        ]
        if balance > 0 and random.random() < 0.3:
            extra_date = payment_date + timedelta(days=random.randint(5, 20))
            extra_amount = min(balance, round(random.uniform(500, balance), 2))
            transactions.append(
                {
                    "date": extra_date.strftime('%Y-%m-%d'),
                    "amount": extra_amount,
                    "currency": currency,
                    "method": random.choice(PAYMENT_METHODS),
                    "reference": random.choice([None, f"RCPT{random.randint(1000, 9999)}"]),
                }
            )
            balance = round(balance - extra_amount, 2)

        payload = {
            "record_type": "booking",
            "lead_id": lead_id,
            "issued_at": issued_at_dt.strftime('%d-%m-%Y'),
            "client": {"name": random_name()},
            "other_pax": build_other_pax(max_pax=4),
            "trip": trip,
            "accommodation": accommodation,
            "flights": flights,
            "services": services,
            "totals": {
                "grand_total": {
                    "amount": amount,
                    "currency": currency,
                },
                "balance_remaining": {
                    "amount": round(balance, 2),
                    "currency": currency,
                },
            },
            "payments": {
                "last_payment_date": transactions[-1]['date'],
                "last_payment_method": transactions[-1]['method'],
                "transactions": transactions,
            },
            "status": {
                "stage": random.choice(STATUS_STAGES),
                "documents_issued": random.random() < 0.8,
                "travel_completed": random.random() < 0.2,
            },
            "notes": maybe_note(NOTES_OPTIONS),
            "assistant_notes": maybe_note(ASSISTANT_NOTES),
        }

        comms = build_communications(issued_at_dt)
        if comms:
            payload["communications"] = comms

        with (record_dir / RECORD_FILENAME).open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, indent=2)
    print(f"Created {TARGET_PER_TYPE} bookings")


def main() -> None:
    generate_enquiries()
    generate_quotes()
    generate_bookings()


if __name__ == '__main__':
    main()

