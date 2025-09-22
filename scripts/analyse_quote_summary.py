import json
import re
import statistics
from collections import Counter
from pathlib import Path

text = Path('samples/quotes_summary.json').read_text(encoding='utf-8-sig')
data = json.loads(text)

price_values = []
for item in data:
    total = item.get('grand_total')
    if total:
        match = re.search(r'(\d[\d,]*\.\d{2})', total)
        if match:
            price_values.append(float(match.group(1).replace(',', '')))

trip_counts = Counter(item.get('trip_title') for item in data if item.get('trip_title'))

summary = {
    'quote_count': len(data),
    'destinations': trip_counts,
    'price_min': min(price_values) if price_values else None,
    'price_max': max(price_values) if price_values else None,
    'price_avg': round(statistics.mean(price_values), 2) if price_values else None,
}

print(json.dumps(summary, indent=2))
