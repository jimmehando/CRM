import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(r'c:/Users/James/Documents/CRM/leads/enquiry')
BASE_DIR.mkdir(parents=True, exist_ok=True)

FIRST_NAMES = [
    "Avery", "Jordan", "Morgan", "Sydney", "Harper", "Kai", "Rowan", "Sloane", "Drew", "Parker",
    "Logan", "Emerson", "Riley", "Campbell", "Jules", "Elliott", "Blair", "Reese", "Arden", "Sawyer",
    "Finley", "Hayden", "Marlow", "River", "Spencer", "Teagan", "Quinn", "Lennox", "Tatum", "Luca",
    "Monroe", "Sage", "Peyton", "Hendrix", "Frankie", "Dakota", "Hollis", "Indy", "Larkin", "Micah",
    "Nico", "Oakley", "Presley", "Shiloh", "Tristan", "Vale", "Winter", "Zephyr", "Cali", "Indira",
]
LAST_NAMES = [
    "Cole", "Reid", "Hayes", "Bennett", "Lennon", "Ellis", "Remy", "Sutton", "Wilder", "Bright",
    "Calloway", "Decker", "Everett", "Fletcher", "Gray", "Harlow", "Iverson", "Jensen", "Keaton", "Lang",
    "Maddox", "Nash", "Orion", "Pryor", "Rhodes", "Sterling", "Thatcher", "Vale", "West", "York",
    "Abbott", "Barlow", "Carmichael", "Dalton", "Easton", "Falcon", "Galloway", "Hawkins", "Irving", "Jameson",
    "Kingsley", "Locke", "Montgomery", "North", "Oakwood", "Prescott", "Quill", "Rockwell", "Sinclair", "Tennyson",
]
DESTINATIONS = [
    "Lisbon & Azores", "Seoul & Busan", "Copenhagen & Faroe Islands", "Santorini", "Reykjavík & Golden Circle",
    "Cape Town & Winelands", "New York City", "Kyoto", "Queenstown", "Bali", "Barcelona", "Amalfi Coast",
    "Marrakesh", "Vancouver", "Banff", "Buenos Aires", "Patagonia", "Sydney", "Melbourne", "Fiji",
    "Edinburgh & Highlands", "Prague & Vienna", "Dubrovnik", "Iceland Ring Road", "Swiss Alps", "Tokyo",
    "Osaka", "Kyushu", "Sicily", "Provence", "Tuscany", "Geneva & Montreux", "Istanbul", "Cairo", "Amman & Petra",
    "Zanzibar", "Phuket", "Hoi An", "Koh Samui", "Queenstown & Milford Sound", "Paris", "London", "Dublin",
    "Berlin", "Morocco Desert Circuit", "Kenyan Safari", "Canadian Rockies", "Norwegian Fjords", "Hawaii Islands", "Yosemite & Napa"
]
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
    "",
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

START_DATE = datetime(2025, 6, 1)
END_DATE = datetime(2025, 9, 21, 23, 59, 59)
MONTH_YEAR_PAIRS = [
    ("06", "2025"), ("07", "2025"), ("08", "2025"), ("09", "2025"),
    ("10", "2025"), ("11", "2025"), ("12", "2025"), ("01", "2026"),
    ("02", "2026"), ("03", "2026"), ("04", "2026"), ("05", "2026"),
]
TRIP_UNITS = ["days", "weeks"]

random.seed(20240921)

existing_files = {p.name for p in BASE_DIR.glob('*.json')}

def random_datetime(start: datetime, end: datetime) -> datetime:
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=random.randint(0, delta_seconds))

created = 0
attempts = 0
TARGET = 50

while created < TARGET and attempts < TARGET * 20:
    attempts += 1
    submitted_at = random_datetime(START_DATE, END_DATE)
    record_id = f"{submitted_at.strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex}"
    filename = f"{record_id}.json"

    if filename in existing_files:
        continue

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}@example.com"
    phone = f"04{random.randint(10**8, 10**9 - 1)}"

    travellers = {
        "adults": random.randint(1, 3),
        "children": random.randint(0, 2),
        "infants": random.choice([0, 0, 1])
    }

    if random.random() < 0.55:
        departure = submitted_at + timedelta(days=random.randint(35, 140))
        length_days = random.randint(5, 18)
        return_date = departure + timedelta(days=length_days)
        schedule = {
            "departure_date": departure.strftime('%Y-%m-%d'),
            "return_date": return_date.strftime('%Y-%m-%d'),
            "flex_month": None,
            "flex_month_month": None,
            "flex_month_year": None,
            "trip_length_value": length_days,
            "trip_length_unit": "days"
        }
    else:
        month, year = random.choice(MONTH_YEAR_PAIRS)
        schedule = {
            "departure_date": None,
            "return_date": None,
            "flex_month": f"{month}/{year}",
            "flex_month_month": month,
            "flex_month_year": year,
            "trip_length_value": random.choice([7, 10, 14, 21]),
            "trip_length_unit": random.choice(TRIP_UNITS)
        }

    payload = {
        "record_type": "enquiry",
        "submitted_at": submitted_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "name": name,
        "phone": phone,
        "email": email,
        "destination": random.choice(DESTINATIONS),
        "travellers": travellers,
        "schedule": schedule,
        "notes": random.choice(NOTES_OPTIONS) or None,
    }

    if random.random() < 0.6:
        comm_time = submitted_at + timedelta(days=random.randint(1, 12), hours=random.randint(0, 22))
        payload["communications"] = [
            {
                "timestamp": comm_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "method": random.choice(COMMUNICATION_METHODS),
                "direction": random.choice(DIRECTIONS),
                "note": random.choice(FOLLOW_UP_NOTES)
            }
        ]

    with (BASE_DIR / filename).open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)

    existing_files.add(filename)
    created += 1

print(f"Created {created} enquiry leads.")
