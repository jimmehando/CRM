# SkyDesk — Lightweight CRM Workbench

SkyDesk is a dark, sleek Flask app for capturing enquiries, ingesting quotes/bookings from PDFs, and tracking follow‑ups. It persists data as JSON on disk and keeps the UI fast and readable with Tailwind.

## Features
- Dashboard with counters, recent activity, and an Active To‑Dos list
- Lead intake (Enquiry) with server‑side validation and JSON persistence
- Quote/Booking ingestion via LLM from uploaded PDFs (optional)
- Detail pages with top tabs (Overview • Communication • Documents)
- To‑Do panel per lead; Add/Toggle/Delete with due badges
- Communication log and a friendly “Log new touchpoint” modal

## Quickstart
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Visit `http://localhost:8008`.

## Configuration
Create a `.env` file (or export env vars) for optional LLM features and Flask secret:
```
FLASK_SECRET_KEY=skydesk-dev-secret
OPENAI_API_KEY=...           # required for quote/booking ingestion and To‑Do assistant
OPENAI_MODEL=gpt-4.1-nano    # default if unset
OPENAI_TEMPERATURE=0         # optional
```

## Storage Layout
```
leads/
  enquiry/<id>/record.json
  quote/<lead_id>/record.json
  quote/<lead_id>/metadata.json
  quote/<lead_id>/documents/<original.pdf>
  quote/<lead_id>/todos.json           # assistant-generated To‑Dos index
  booking/<lead_id>/...                # mirrors quote structure
tmp/
  quote_drafts/<draft_id>/{draft.json, source.pdf}
  booking_drafts/<draft_id>/{draft.json, source.pdf}
```
`leads/` is gitignored by default; commit fixtures only when needed.

## Tests (suggested)
- Unit tests for enquiry payload builder and persistence
- Route tests for `/leads/new`, `/leads/*/confirm/*`, and `/leads/<type>/<id>`
- Snapshot tests for key JSON structures

## Notes
- Large uploads: consider setting `app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024` (10MB)
- Security: CSRF is not enabled; add if exposing publicly
