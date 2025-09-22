from pathlib import Path

BASE_DIR = Path(r'c:/Users/James/Documents/CRM/leads/enquiry')
RECORD_FILENAME = 'record.json'

if not BASE_DIR.exists():
    raise SystemExit('enquiry directory missing')

migrated = 0
skipped = 0

for json_path in BASE_DIR.glob('*.json'):
    record_id = json_path.stem
    record_dir = BASE_DIR / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    target = record_dir / RECORD_FILENAME
    if target.exists():
        json_path.unlink()
        skipped += 1
        continue

    json_path.rename(target)
    migrated += 1

print(f'Migrated {migrated} enquiries, skipped {skipped}.')
