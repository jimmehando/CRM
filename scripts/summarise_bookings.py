import json
import re
from pathlib import Path

SOURCE_DIR = Path(r'c:/Users/James/Documents/CRM/samples/bookings_txt')

summaries = []

KEY_PREFIXES = (
    'Flight', 'Stay', 'Transfer', 'Tour', 'Rail', 'Experience', 'Cruise', 'Insurance', 'Activity', 'Car'
)

for txt_path in sorted(SOURCE_DIR.glob('*.txt')):
    text = txt_path.read_text(encoding='utf-8')
    lines = [line.strip() for line in text.splitlines()]

    def find_after(label: str):
        lower_label = label.lower()
        for idx, line in enumerate(lines):
            if line.strip().lower() == lower_label:
                for nxt in lines[idx + 1:]:
                    if nxt:
                        return nxt
        return None

    booking_id = find_after('Booking ID')
    issued_on = find_after('Issued on')
    travel_dates = find_after('Travel dates')
    invoice_contact = find_after('Invoice issued to')
    travellers = find_after('Travellers')

    services: list[str] = []
    if 'Trip Summary' in lines:
        start = lines.index('Trip Summary') + 1
        for line in lines[start:start + 40]:
            if not line:
                continue
            if line.startswith(KEY_PREFIXES):
                if line not in services:
                    services.append(line)
            if line.startswith('Travellers') or line.startswith('Your Peace of Mind'):
                break
    services = services[:6]

    grand_total = None
    for idx, line in enumerate(lines):
        if line.lower() == 'grand total':
            for nxt in lines[idx + 1: idx + 10]:
                if nxt:
                    match = re.search(r"([\d,]+\.\d{2}\s*[A-Z]{3})", nxt)
                    if match:
                        grand_total = match.group(1)
                        break
            if grand_total:
                break
    if not grand_total:
        match_total = re.search(r"Grand Total(?:.|\n){0,200}?([\d,]+\.\d{2}\s*[A-Z]{3})", text)
        if match_total:
            grand_total = match_total.group(1)

    balance = None
    match_balance = re.search(r"Total Remaining Balance Owing\s*([\d,]+\.\d{2}\s*[A-Z]{3})", text)
    if match_balance:
        balance = match_balance.group(1)

    last_payment = None
    payment_method = None
    payment_match = re.search(r"(\d{2}\s\w{3}\s\d{4})\s+Payment\s+([^\n]+)", text)
    if payment_match:
        last_payment = payment_match.group(1)
        payment_method = payment_match.group(2).strip()

    summaries.append(
        {
            'file': txt_path.name,
            'booking_id': booking_id,
            'issued_on': issued_on,
            'travel_dates': travel_dates,
            'invoice_contact': invoice_contact,
            'travellers': travellers,
            'key_services': services,
            'grand_total': grand_total,
            'balance_remaining': balance,
            'last_payment_date': last_payment,
            'last_payment_method': payment_method,
        }
    )

print(json.dumps(summaries, indent=2))
