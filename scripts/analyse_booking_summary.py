import json
import re
import statistics
from pathlib import Path

def parse_amount(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"([\d,]+\.\d{2})", value)
    if not match:
        return None
    return float(match.group(1).replace(',', ''))

text = Path('samples/bookings_summary.json').read_text(encoding='utf-8-sig')
records = json.loads(text)

amounts = [amt for item in records if (amt := parse_amount(item.get('grand_total'))) is not None]
balances = [bal for item in records if (bal := parse_amount(item.get('balance_remaining'))) is not None]

fully_paid = sum(1 for bal in balances if abs(bal) < 0.01)
outstanding = len([bal for bal in balances if bal and bal > 0.01])

summary = {
    'booking_count': len(records),
    'grand_total_min': min(amounts) if amounts else None,
    'grand_total_max': max(amounts) if amounts else None,
    'grand_total_avg': round(statistics.mean(amounts), 2) if amounts else None,
    'total_balance_due': round(sum(balances), 2) if balances else None,
    'fully_paid': fully_paid,
    'with_balance_due': outstanding,
}

print(json.dumps(summary, indent=2))
