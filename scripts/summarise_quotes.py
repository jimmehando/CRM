import json
import re
from pathlib import Path

SOURCE_DIR = Path(r'c:/Users/James/Documents/CRM/samples/quotes_txt')

summaries = []

for txt_path in sorted(SOURCE_DIR.glob('*.txt')):
    text = txt_path.read_text(encoding='utf-8')
    lines = [line.strip() for line in text.splitlines()]

    def find_after(label):
        for idx, line in enumerate(lines):
            if line.lower() == label.lower():
                for nxt in lines[idx + 1:]:
                    if nxt:
                        return nxt
        return None

    quote_number = find_after('Quote number')
    issued_on = find_after('Issued on')
    trip_title = find_after('Review your holiday')
    travel_dates = find_after('Travel dates')
    travellers = find_after('Travellers')

    accommodation = None
    for line in lines:
        if line.startswith('Stay '):
            accommodation = line
            break

    grand_total = None
    match = re.search(r'Grand Total(?:.|\n){0,200}?([\d,]+\.\d{2}\s*[A-Z]{3})', text)
    if match:
        grand_total = match.group(1)

    inclusions = []
    if 'Trip Summary' in lines:
        start = lines.index('Trip Summary') + 1
        for line in lines[start:start + 20]:
            if not line or line.startswith(('Travellers', 'Your Peace of Mind', 'Quote ID', '/', 'Trip Summary')):
                continue
            inclusions.append(line)
    cleaned_inclusions = []
    for inc in inclusions:
        if inc not in cleaned_inclusions:
            cleaned_inclusions.append(inc)
    cleaned_inclusions = cleaned_inclusions[:5]

    summaries.append({
        'file': txt_path.name,
        'quote_number': quote_number,
        'issued_on': issued_on,
        'trip_title': trip_title,
        'travel_dates': travel_dates,
        'travellers': travellers,
        'accommodation': accommodation,
        'grand_total': grand_total,
        'inclusions': cleaned_inclusions,
    })

print(json.dumps(summaries, indent=2))
