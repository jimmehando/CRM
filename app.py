import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple, Dict
from uuid import uuid4

from flask import Flask, render_template, request, redirect, url_for, abort, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from services.quote_ingest import QuoteDraft, process_quote_submission
from services.booking_ingest import BookingDraft, process_booking_submission
from services.llm_client import LLMNotConfigured
from services.todo_ingest import process_todo_submission

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'skydesk-dev-secret')
# Cap upload size to 10MB as per UI copy and README guidance
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

BASE_DIR = Path(__file__).resolve().parent
ENQUIRY_DIR = BASE_DIR / 'leads' / 'enquiry'
QUOTE_DIR = BASE_DIR / 'leads' / 'quote'
BOOKING_DIR = BASE_DIR / 'leads' / 'booking'
LEAD_DIRECTORIES = {
    'enquiry': ENQUIRY_DIR,
    'quote': QUOTE_DIR,
    'booking': BOOKING_DIR,
}

RECORD_FILENAME = 'record.json'
COMMUNICATIONS_FILENAME = 'communications.json'
TODOS_FILENAME = 'todos.json'

TMP_DIR = BASE_DIR / 'tmp'
QUOTE_DRAFT_DIR = TMP_DIR / 'quote_drafts'
BOOKING_DRAFT_DIR = TMP_DIR / 'booking_drafts'


def get_record_payload_path(directory: Path, record_id: str) -> Path:
    return directory / record_id / RECORD_FILENAME


def get_record_directory(directory: Path, record_id: str) -> Path:
    return directory / record_id


def _load_json_object(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open('r', encoding='utf-8') as h:
            data = json.load(h)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json_object(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as h:
        json.dump(data, h, indent=2)


def quote_draft_paths(draft_id: str) -> Tuple[Path, Path, Path]:
    draft_dir = QUOTE_DRAFT_DIR / draft_id
    data_path = draft_dir / 'draft.json'
    pdf_path = draft_dir / 'source.pdf'
    return draft_dir, data_path, pdf_path


def save_quote_draft(draft_id: str, draft: QuoteDraft, *, notes: str, original_filename: str) -> None:
    QUOTE_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    draft_dir, data_path, _ = quote_draft_paths(draft_id)
    draft_dir.mkdir(parents=True, exist_ok=True)
    data = {
        'parsed': draft.parsed,
        'raw_response': draft.raw_response,
        'transcript': draft.transcript,
        'notes': notes,
        'original_filename': original_filename,
        'pdf_filename': 'source.pdf',
    }
    with data_path.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)


def load_quote_draft(draft_id: str) -> Optional[dict]:
    _, data_path, pdf_path = quote_draft_paths(draft_id)
    if not data_path.exists() or not pdf_path.exists():
        return None
    try:
        with data_path.open('r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    payload['pdf_path'] = pdf_path
    return payload


def delete_quote_draft(draft_id: str) -> None:
    draft_dir, _, _ = quote_draft_paths(draft_id)
    if draft_dir.exists():
        shutil.rmtree(draft_dir, ignore_errors=True)


def persist_quote(record_id: str, payload: dict, *, pdf_source: Path, metadata: dict) -> None:
    record_dir = get_record_directory(QUOTE_DIR, record_id)
    if record_dir.exists():
        raise ValueError('A quote with this ID already exists.')

    record_dir.mkdir(parents=True, exist_ok=True)

    target_payload = record_dir / RECORD_FILENAME
    with target_payload.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)

    documents_dir = record_dir / 'documents'
    documents_dir.mkdir(parents=True, exist_ok=True)
    original_name = secure_filename(metadata.get('original_filename') or 'quote.pdf') or 'quote.pdf'
    target_pdf = documents_dir / original_name
    shutil.move(str(pdf_source), target_pdf)

    meta_path = record_dir / 'metadata.json'
    with meta_path.open('w', encoding='utf-8') as handle:
        json.dump(metadata, handle, indent=2)


def booking_draft_paths(draft_id: str) -> Tuple[Path, Path, Path]:
    draft_dir = BOOKING_DRAFT_DIR / draft_id
    data_path = draft_dir / 'draft.json'
    pdf_path = draft_dir / 'source.pdf'
    return draft_dir, data_path, pdf_path


def save_booking_draft(draft_id: str, draft: BookingDraft, *, notes: str, original_filename: str) -> None:
    BOOKING_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    draft_dir, data_path, _ = booking_draft_paths(draft_id)
    draft_dir.mkdir(parents=True, exist_ok=True)
    data = {
        'parsed': draft.parsed,
        'raw_response': draft.raw_response,
        'transcript': draft.transcript,
        'notes': notes,
        'original_filename': original_filename,
        'pdf_filename': 'source.pdf',
    }
    with data_path.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)


def load_booking_draft(draft_id: str) -> Optional[dict]:
    _, data_path, pdf_path = booking_draft_paths(draft_id)
    if not data_path.exists() or not pdf_path.exists():
        return None
    try:
        with data_path.open('r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    payload['pdf_path'] = pdf_path
    return payload


def delete_booking_draft(draft_id: str) -> None:
    draft_dir, _, _ = booking_draft_paths(draft_id)
    if draft_dir.exists():
        shutil.rmtree(draft_dir, ignore_errors=True)


def persist_booking(record_id: str, payload: dict, *, pdf_source: Path, metadata: dict) -> None:
    record_dir = get_record_directory(BOOKING_DIR, record_id)
    if record_dir.exists():
        raise ValueError('A booking with this ID already exists.')

    record_dir.mkdir(parents=True, exist_ok=True)

    target_payload = record_dir / RECORD_FILENAME
    with target_payload.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)

    documents_dir = record_dir / 'documents'
    documents_dir.mkdir(parents=True, exist_ok=True)
    original_name = secure_filename(metadata.get('original_filename') or 'booking.pdf') or 'booking.pdf'
    target_pdf = documents_dir / original_name
    shutil.move(str(pdf_source), target_pdf)

    meta_path = record_dir / 'metadata.json'
    with meta_path.open('w', encoding='utf-8') as handle:
        json.dump(metadata, handle, indent=2)


def build_quote_timeline(payload: dict) -> List[dict]:
    events: List[dict] = []

    def parse_date(value: Optional[str]):
        if not value:
            return None
        for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def add_event(date_str: Optional[str], label: str, title: str, details: Optional[str] = None):
        sort_key = parse_date(date_str) or datetime.max
        events.append(
            {
                'date': date_str,
                'date_display': format_travel_date(date_str) if date_str else 'TBC',
                'label': label,
                'title': title,
                'details': details,
                '_sort_key': sort_key,
            }
        )

    for flight in payload.get('flights') or []:
        title = f"{flight.get('origin') or '?'} → {flight.get('destination') or '?'}"
        details_parts = []
        if flight.get('route'):
            details_parts.append(f"Route {flight['route']}")
        if flight.get('carrier'):
            details_parts.append(f"Carrier {flight['carrier']}")
        # choose date from first segment if available
        date_str = None
        segs = flight.get('segments') or []
        if segs and isinstance(segs, list):
            date_str = (segs[0] or {}).get('depart_date') or None
        add_event(date_str, 'Flight', title, ', '.join(details_parts) or None)

    for stay in payload.get('accommodation') or []:
        name = stay.get('name') or 'Accommodation'
        add_event(stay.get('check_in'), 'Check-in', name, stay.get('room_type'))
        add_event(stay.get('check_out'), 'Check-out', name, stay.get('room_type'))

    for service in payload.get('services') or []:
        description = service.get('description') or 'Service'
        label = service.get('type') or 'Service'
        details_parts = []
        if service.get('carrier'):
            details_parts.append(f"Carrier {service['carrier']}")
        if service.get('route'):
            details_parts.append(f"Route {service['route']}")
        add_event(service.get('depart_date'), label, description, ', '.join(details_parts) or None)

    events.sort(key=lambda item: (item['_sort_key'], item['label']))
    for item in events:
        item.pop('_sort_key', None)
    return events


def build_booking_timeline(payload: dict) -> List[dict]:
    events: List[dict] = []

    def parse_date(value: Optional[str]):
        if not value:
            return None
        for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def add_event(date_str: Optional[str], label: str, title: str, details: Optional[str] = None):
        sort_key = parse_date(date_str) or datetime.max
        events.append(
            {
                'date': date_str,
                'date_display': format_travel_date(date_str) if date_str else 'TBC',
                'label': label,
                'title': title,
                'details': details,
                '_sort_key': sort_key,
            }
        )

    for flight in payload.get('flights') or []:
        title = f"{flight.get('origin') or '?'} → {flight.get('destination') or '?'}"
        details_parts = []
        if flight.get('route'):
            details_parts.append(f"Route {flight['route']}")
        if flight.get('carrier'):
            details_parts.append(f"Carrier {flight['carrier']}")
        if flight.get('pnr'):
            details_parts.append(f"PNR {flight['pnr']}")
        segs = flight.get('segments') or []
        date_str = None
        if segs and isinstance(segs, list):
            date_str = (segs[0] or {}).get('depart_date') or None
        add_event(date_str, 'Flight', title, ', '.join(details_parts) or None)

    for stay in payload.get('accommodation') or []:
        name = stay.get('name') or 'Accommodation'
        add_event(stay.get('check_in'), 'Check-in', name, stay.get('room_type'))
        add_event(stay.get('check_out'), 'Check-out', name, stay.get('room_type'))

    for service in payload.get('services') or []:
        desc = service.get('description') or 'Service'
        label = service.get('type') or 'Service'
        details_parts = []
        if service.get('carrier'):
            details_parts.append(f"Carrier {service['carrier']}")
        if service.get('route'):
            details_parts.append(f"Route {service['route']}")
        if service.get('pnr'):
            details_parts.append(f"Reference {service['pnr']}")
        add_event(service.get('depart_date'), label, desc, ', '.join(details_parts) or None)

    payments = (payload.get('payments') or {}).get('transactions') or []
    for txn in payments:
        amount = txn.get('amount')
        currency = txn.get('currency')
        method = txn.get('method') or 'Payment'
        title = f"{method}"
        if amount is not None:
            title += f" {amount}"
        if currency:
            title += f" {currency}"
        add_event(txn.get('date'), 'Payment', title.strip(), txn.get('reference'))

    events.sort(key=lambda item: (item['_sort_key'], item['label']))
    for item in events:
        item.pop('_sort_key', None)
    return events


@app.route('/')
@app.route('/dashboard')
def dashboard():
    leads_by_type = {key: load_leads(key) for key in LEAD_DIRECTORIES}
    lead_totals = {key: len(items) for key, items in leads_by_type.items()}

    type_labels = {
        'enquiry': 'Enquiry',
        'quote': 'Quote',
        'booking': 'Booking',
    }

    def parse_sort_key(raw: Optional[str]) -> datetime:
        if not raw:
            return datetime.min
        cleaned = raw.replace('Z', '+00:00') if raw.endswith('Z') else raw
        try:
            dt_value = datetime.fromisoformat(cleaned)
            if dt_value.tzinfo is not None:
                return dt_value.astimezone(timezone.utc).replace(tzinfo=None)
            return dt_value
        except ValueError:
            pass
        for fmt in ('%Y-%m-%d', '%d %b %Y'):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return datetime.min

    recent_leads = []
    for record_type, items in leads_by_type.items():
        for item in items:
            enriched = item.copy()
            enriched['type_label'] = type_labels.get(record_type, record_type.title())
            enriched['detail_url'] = url_for('lead_detail', record_type=record_type, record_id=item['record_id'])
            recent_leads.append(enriched)

    recent_leads.sort(key=lambda lead: parse_sort_key(lead.get('submitted_at_value')), reverse=True)
    recent_leads = recent_leads[:6]

    all_todos = collect_active_todos(type_labels=type_labels)
    active_todos = all_todos[:5]
    more_count = max(len(all_todos) - len(active_todos), 0)

    return render_template('dashboard.html', lead_totals=lead_totals, recent_leads=recent_leads, active_todos=active_todos, active_todos_more=more_count)


@app.route('/leads/new', methods=['GET', 'POST'])
def leads_new():
    form_defaults = default_enquiry_form()
    field_errors: dict[str, str] = {}
    error_messages: List[str] = []
    month_options = get_month_options()
    year_options = get_year_options()

    active_record_type = 'enquiry'

    if request.method == 'GET':
        requested_type = (request.args.get('record_type') or '').strip().lower()
        if requested_type in {'enquiry', 'quote', 'booking'}:
            active_record_type = requested_type

    if request.method == 'POST':
        record_type = request.form.get('record_type', '').strip().lower() or 'enquiry'
        active_record_type = record_type

        if record_type == 'enquiry':
            form_data = {**form_defaults, **request.form.to_dict(flat=True)}
            payload, field_errors = build_enquiry_payload(request.form)
            error_messages = list(dict.fromkeys(field_errors.values()))

            if field_errors:
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='enquiry',
                        form_data=form_data,
                        field_errors=field_errors,
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    400,
                )

            record_id = generate_record_id()
            persist_enquiry(record_id, payload)
            flash('Enquiry saved to the SkyDesk archive.', 'success')
            return redirect(url_for('dashboard'))

        if record_type == 'quote':
            quote_file = request.files.get('quote_pdf')
            if not quote_file or not quote_file.filename:
                error_messages = ['Please upload a quote PDF before submitting.']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='quote',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    400,
                )

            if not quote_file.filename.lower().endswith('.pdf'):
                error_messages = ['Only PDF files are supported for quote ingestion.']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='quote',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    400,
                )

            draft_id = uuid4().hex
            draft_dir, _, pdf_path = quote_draft_paths(draft_id)
            draft_dir.mkdir(parents=True, exist_ok=True)
            quote_file.save(pdf_path)

            notes_value = (request.form.get('notes') or '').strip()

            try:
                draft = process_quote_submission(pdf_path, notes=notes_value)
            except LLMNotConfigured as exc:
                shutil.rmtree(draft_dir, ignore_errors=True)
                error_messages = [str(exc)]
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='quote',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    500,
                )
            except Exception as exc:  # pragma: no cover - depends on external service
                shutil.rmtree(draft_dir, ignore_errors=True)
                error_messages = [f'Unable to parse the quote PDF: {exc}']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='quote',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    500,
                )

            save_quote_draft(
                draft_id,
                draft,
                notes=notes_value,
                original_filename=quote_file.filename,
            )

            return redirect(url_for('quote_confirm', draft_id=draft_id))

        if record_type == 'booking':
            booking_file = request.files.get('booking_pdf')
            if not booking_file or not booking_file.filename:
                error_messages = ['Please upload a booking PDF before submitting.']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='booking',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    400,
                )

            if not booking_file.filename.lower().endswith('.pdf'):
                error_messages = ['Only PDF files are supported for booking ingestion.']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='booking',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    400,
                )

            draft_id = uuid4().hex
            draft_dir, _, pdf_path = booking_draft_paths(draft_id)
            draft_dir.mkdir(parents=True, exist_ok=True)
            booking_file.save(pdf_path)

            notes_value = (request.form.get('notes') or '').strip()

            try:
                draft = process_booking_submission(pdf_path, notes=notes_value)
            except LLMNotConfigured as exc:
                shutil.rmtree(draft_dir, ignore_errors=True)
                error_messages = [str(exc)]
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='booking',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    500,
                )
            except Exception as exc:  # pragma: no cover - depends on external service
                shutil.rmtree(draft_dir, ignore_errors=True)
                error_messages = [f'Unable to parse the booking PDF: {exc}']
                return (
                    render_template(
                        'leads_new.html',
                        active_record_type='booking',
                        form_data=form_defaults,
                        field_errors={},
                        error_messages=error_messages,
                        month_options=month_options,
                        year_options=year_options,
                    ),
                    500,
                )

            save_booking_draft(
                draft_id,
                draft,
                notes=notes_value,
                original_filename=booking_file.filename,
            )

            return redirect(url_for('booking_confirm', draft_id=draft_id))

        abort(400, description='Unsupported record type')

    return render_template(
        'leads_new.html',
        active_record_type=active_record_type,
        form_data=form_defaults,
        field_errors=field_errors,
        error_messages=error_messages,
        month_options=month_options,
        year_options=year_options,
    )


@app.route('/leads')
def leads():
    leads_by_type = {key: load_leads(key) for key in LEAD_DIRECTORIES}
    requested_type = (request.args.get('record_type') or 'enquiry').strip().lower()
    active_record_type = requested_type if requested_type in LEAD_DIRECTORIES else 'enquiry'
    return render_template('leads.html', leads_by_type=leads_by_type, active_record_type=active_record_type)


@app.route('/todos')
def todos():
    type_labels = {
        'enquiry': 'Enquiry',
        'quote': 'Quote',
        'booking': 'Booking',
    }
    items = collect_active_todos(type_labels=type_labels)
    return render_template('todos.html', items=items)


@app.route('/leads/quote/confirm/<draft_id>', methods=['GET', 'POST'])
def quote_confirm(draft_id: str):
    draft = load_quote_draft(draft_id)
    if not draft:
        abort(404)

    payload = draft['parsed']
    error_message: Optional[str] = None

    def _split_list(value: str) -> List[str]:
        return [part.strip() for part in re.split(r'[\n,]+', value or '') if part.strip()]

    def _collect_items(prefix: str, fields: List[str], *, include_empty: bool = False) -> List[dict]:
        count = int(request.form.get(f'{prefix}_count', '0'))
        items: List[dict] = []
        for index in range(count):
            base = {}
            has_content = False
            for field in fields:
                key = f'{prefix}-{index}-{field}'
                value = request.form.get(key, '').strip()
                if value:
                    has_content = True
                base[field] = value or None
            if has_content or include_empty:
                items.append(base)
        return items

    if request.method == 'POST':
        lead_id = request.form.get('lead_id', '').strip()
        issued_at = request.form.get('issued_at', '').strip()

        if not re.fullmatch(r'\d{7}', lead_id):
            error_message = 'Lead ID must be a 7-digit number.'

        trip_destinations = _split_list(request.form.get('trip_destinations', ''))
        trip_locations = list(trip_destinations)

        other_pax = _collect_items('other_pax', ['name', 'pax_type'])
        accommodation = _collect_items('accommodation', ['name', 'check_in', 'check_out', 'nights', 'room_type', 'board', 'supplier_ref'])
        flights = _collect_items('flights', ['carrier', 'route', 'origin', 'destination', 'pnr', 'supplier_ref'])
        for index, flight in enumerate(flights):
            seg_key = f'flights-{index}-segments_json'
            lay_key = f'flights-{index}-layovers_json'
            try:
                segments_raw = request.form.get(seg_key, '')
                flight['segments'] = json.loads(segments_raw) if segments_raw.strip() else []
            except json.JSONDecodeError:
                flight['segments'] = []
            try:
                layovers_raw = request.form.get(lay_key, '')
                flight['layovers'] = json.loads(layovers_raw) if layovers_raw.strip() else []
            except json.JSONDecodeError:
                flight['layovers'] = []
            if isinstance(flight.get('segments'), list):
                flight['layover_count'] = max(len(flight['segments']) - 1, 0)
        services = _collect_items('services', ['type', 'description', 'depart_date', 'return_date', 'supplier_ref'])

        def _safe_int(value: Optional[str]) -> Optional[int]:
            if not value:
                return None
            try:
                return int(value)
            except ValueError:
                return None

        for stay in accommodation:
            stay['nights'] = _safe_int(stay.get('nights'))

        for flight in flights:
            flight['ticket_numbers'] = []

        for service in services:
            service['ticket_numbers'] = []
            service['supplier_ref'] = None
            service['route'] = None
            service['depart_time_local'] = None
            service['arrive_time_local'] = None

        totals_amount_raw = request.form.get('grand_total_amount', '').strip()
        totals_currency = request.form.get('grand_total_currency', '').strip()
        totals_amount = None
        if totals_amount_raw:
            try:
                totals_amount = float(totals_amount_raw)
            except ValueError:
                error_message = 'Grand total amount must be numeric.'

        payload = {
            'record_type': 'quote',
            'lead_id': lead_id,
            'issued_at': issued_at or None,
            'client': {'name': request.form.get('client_name', '').strip()},
            'other_pax': other_pax,
            'trip': {
                'destinations': trip_destinations,
                'locations': trip_locations,
                'dates': {
                    'start': request.form.get('trip_start', '').strip() or None,
                    'end': request.form.get('trip_end', '').strip() or None,
                    'nights': _safe_int(request.form.get('trip_nights', '').strip()),
                },
            },
            'accommodation': accommodation,
            'flights': flights,
            'services': services,
            'totals': {
                'grand_total': {
                    'amount': totals_amount,
                    'currency': totals_currency or None,
                }
            },
            'notes': request.form.get('notes_field', '').strip() or None,
            'assistant_notes': None,
        }

        if error_message is None:
            metadata = {
                'raw_response': draft.get('raw_response'),
                'transcript': draft.get('transcript'),
                'notes': draft.get('notes'),
                'original_filename': draft.get('original_filename'),
                'saved_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            }
            pdf_path: Path = draft['pdf_path']

            try:
                persist_quote(lead_id, payload, pdf_source=pdf_path, metadata=metadata)
            except ValueError as exc:
                error_message = str(exc)
            else:
                delete_quote_draft(draft_id)
                return redirect(url_for('lead_detail', record_type='quote', record_id=lead_id))

    return render_template(
        'quote_confirm.html',
        draft_id=draft_id,
        payload=payload,
        notes=draft.get('notes'),
        original_filename=draft.get('original_filename'),
        error_message=error_message,
        raw_response=draft.get('raw_response'),
        transcript=draft.get('transcript'),
    )


@app.route('/leads/booking/confirm/<draft_id>', methods=['GET', 'POST'])
def booking_confirm(draft_id: str):
    draft = load_booking_draft(draft_id)
    if not draft:
        abort(404)

    payload = draft['parsed']
    error_message: Optional[str] = None

    def _split_list(value: str) -> List[str]:
        return [part.strip() for part in re.split(r'[\n,]+', value or '') if part.strip()]

    def _collect_items(prefix: str, fields: List[str]) -> List[dict]:
        count = int(request.form.get(f'{prefix}_count', '0'))
        items: List[dict] = []
        for index in range(count):
            base = {}
            has_content = False
            for field in fields:
                key = f'{prefix}-{index}-{field}'
                value = request.form.get(key, '').strip()
                if value:
                    has_content = True
                base[field] = value or None
            if has_content:
                items.append(base)
        return items

    def _safe_int(value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _safe_float(value: Optional[str]) -> Optional[float]:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    if request.method == 'POST':
        lead_id = request.form.get('lead_id', '').strip()
        issued_at = request.form.get('issued_at', '').strip()

        if not re.fullmatch(r'\d{7}', lead_id):
            error_message = 'Lead ID must be a 7-digit number.'

        trip_destinations = _split_list(request.form.get('trip_destinations', ''))
        trip_locations = _split_list(request.form.get('trip_locations', ''))

        other_pax = _collect_items('other_pax', ['name', 'pax_type'])
        accommodation = _collect_items('accommodation', ['name', 'check_in', 'check_out', 'nights', 'room_type', 'board', 'supplier_ref'])
        flights = _collect_items('flights', ['carrier', 'route', 'origin', 'destination', 'pnr', 'supplier_ref'])
        for index, flight in enumerate(flights):
            seg_key = f'flights-{index}-segments_json'
            lay_key = f'flights-{index}-layovers_json'
            try:
                segments_raw = request.form.get(seg_key, '')
                flight['segments'] = json.loads(segments_raw) if segments_raw.strip() else []
            except json.JSONDecodeError:
                flight['segments'] = []
            try:
                layovers_raw = request.form.get(lay_key, '')
                flight['layovers'] = json.loads(layovers_raw) if layovers_raw.strip() else []
            except json.JSONDecodeError:
                flight['layovers'] = []
            if isinstance(flight.get('segments'), list):
                flight['layover_count'] = max(len(flight['segments']) - 1, 0)
        services = _collect_items('services', ['type', 'description', 'carrier', 'route', 'depart_date', 'depart_time_local', 'arrive_time_local', 'pnr'])

        for stay in accommodation:
            stay['nights'] = _safe_int(stay.get('nights'))

        for flight in flights:
            flight['ticket_numbers'] = []
            flight['supplier_ref'] = None

        for service in services:
            service['ticket_numbers'] = []
            service['supplier_ref'] = None

        grand_total_amount = _safe_float(request.form.get('grand_total_amount', '').strip())
        grand_total_currency = (request.form.get('grand_total_currency', '').strip() or None)
        balance_amount = _safe_float(request.form.get('balance_amount', '').strip())
        balance_currency = (request.form.get('balance_currency', '').strip() or None)

        if request.form.get('grand_total_amount', '').strip() and grand_total_amount is None and error_message is None:
            error_message = 'Grand total amount must be numeric.'
        if request.form.get('balance_amount', '').strip() and balance_amount is None and error_message is None:
            error_message = 'Balance amount must be numeric.'

        payments_transactions = []
        txn_count = int(request.form.get('payments_txn_count', '0'))
        for index in range(txn_count):
            date_value = request.form.get(f'transactions-{index}-date', '').strip() or None
            amount_value = _safe_float(request.form.get(f'transactions-{index}-amount', '').strip())
            currency_value = request.form.get(f'transactions-{index}-currency', '').strip() or None
            method_value = request.form.get(f'transactions-{index}-method', '').strip() or None
            reference_value = request.form.get(f'transactions-{index}-reference', '').strip() or None
            if any([date_value, amount_value is not None, currency_value, method_value, reference_value]):
                payments_transactions.append(
                    {
                        'date': date_value,
                        'amount': amount_value,
                        'currency': currency_value,
                        'method': method_value,
                        'reference': reference_value,
                    }
                )

        payload_candidate = {
            'record_type': 'booking',
            'lead_id': lead_id,
            'issued_at': issued_at or None,
            'client': {'name': request.form.get('client_name', '').strip()},
            'other_pax': other_pax,
            'trip': {
                'destinations': trip_destinations,
                'locations': trip_locations,
                'dates': {
                    'start': request.form.get('trip_start', '').strip() or None,
                    'end': request.form.get('trip_end', '').strip() or None,
                    'nights': _safe_int(request.form.get('trip_nights', '').strip()),
                },
            },
            'accommodation': accommodation,
            'flights': flights,
            'services': services,
            'totals': {
                'grand_total': {
                    'amount': grand_total_amount,
                    'currency': grand_total_currency,
                },
                'balance_remaining': {
                    'amount': balance_amount,
                    'currency': balance_currency,
                },
            },
            'payments': {
                'last_payment_date': request.form.get('last_payment_date', '').strip() or None,
                'last_payment_method': request.form.get('last_payment_method', '').strip() or None,
                'transactions': payments_transactions,
            },
            'status': {
                'stage': request.form.get('status_stage', '').strip() or None,
                'documents_issued': request.form.get('documents_issued') == 'true',
                'travel_completed': request.form.get('travel_completed') == 'true',
            },
            'notes': (request.form.get('notes_field') or '').strip() or None,
            'assistant_notes': None,
        }

        payload = payload_candidate

        if error_message is None:
            metadata = {
                'raw_response': draft.get('raw_response'),
                'transcript': draft.get('transcript'),
                'notes': payload_candidate.get('notes'),
                'original_filename': draft.get('original_filename'),
                'saved_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            }
            pdf_path: Path = draft['pdf_path']

            try:
                persist_booking(lead_id, payload_candidate, pdf_source=pdf_path, metadata=metadata)
            except ValueError as exc:
                error_message = str(exc)
            else:
                delete_booking_draft(draft_id)
                return redirect(url_for('lead_detail', record_type='booking', record_id=lead_id))

    payments = payload.get('payments') or {}
    transactions = payments.get('transactions') or []
    if not transactions:
        transactions = [{}]

    return render_template(
        'booking_confirm.html',
        draft_id=draft_id,
        payload=payload,
        notes=draft.get('notes'),
        original_filename=draft.get('original_filename'),
        error_message=error_message,
        raw_response=draft.get('raw_response'),
        transcript=draft.get('transcript'),
        transactions=transactions,
    )


@app.route('/leads/quote/confirm/<draft_id>/pdf')
def quote_draft_pdf(draft_id: str):
    draft = load_quote_draft(draft_id)
    if not draft:
        abort(404)
    filename = secure_filename(draft.get('original_filename') or 'quote.pdf') or 'quote.pdf'
    return send_file(draft['pdf_path'], mimetype='application/pdf', download_name=filename)


@app.route('/leads/quote/<record_id>/document/<path:filename>')
def quote_document(record_id: str, filename: str):
    directory = (get_record_directory(QUOTE_DIR, record_id) / 'documents').resolve()
    file_path = (directory / filename).resolve()
    if not str(file_path).startswith(str(directory)) or not file_path.exists():
        abort(404)
    return send_file(file_path, mimetype='application/pdf', download_name=file_path.name)


@app.route('/leads/booking/confirm/<draft_id>/pdf')
def booking_draft_pdf(draft_id: str):
    draft = load_booking_draft(draft_id)
    if not draft:
        abort(404)
    filename = secure_filename(draft.get('original_filename') or 'booking.pdf') or 'booking.pdf'
    return send_file(draft['pdf_path'], mimetype='application/pdf', download_name=filename)


@app.route('/leads/booking/<record_id>/document/<path:filename>')
def booking_document(record_id: str, filename: str):
    directory = (get_record_directory(BOOKING_DIR, record_id) / 'documents').resolve()
    file_path = (directory / filename).resolve()
    if not str(file_path).startswith(str(directory)) or not file_path.exists():
        abort(404)
    return send_file(file_path, mimetype='application/pdf', download_name=file_path.name)


@app.route('/leads/enquiry/<record_id>/document/<path:filename>')
def enquiry_document(record_id: str, filename: str):
    directory = (get_record_directory(ENQUIRY_DIR, record_id) / 'documents').resolve()
    file_path = (directory / filename).resolve()
    if not str(file_path).startswith(str(directory)) or not file_path.exists():
        abort(404)
    # Best-effort content type; let browser infer. Use octet-stream for safety.
    return send_file(file_path, mimetype='application/octet-stream', download_name=file_path.name)

@app.route('/leads/<record_type>/<record_id>', methods=['GET', 'POST'])
def lead_detail(record_type: str, record_id: str):
    record_type = record_type.lower()
    directory = LEAD_DIRECTORIES.get(record_type)
    if not directory:
        abort(404)

    payload_path = get_record_payload_path(directory, record_id)
    if not payload_path.exists():
        abort(404)

    try:
        with payload_path.open('r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        abort(404)

    default_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
    record_dir = get_record_directory(directory, record_id)
    record_dir = get_record_directory(directory, record_id)

    def apply_journal_update() -> Optional[str]:
        form_type = request.form.get('form_type', 'notes')

        if form_type == 'notes':
            payload['notes'] = (request.form.get('notes') or '').strip()
            return 'notes'

        if form_type == 'log':
            comm_index_path = record_dir / COMMUNICATIONS_FILENAME
            index = _load_json_object(comm_index_path)
            # derive next numeric key
            next_idx = 1
            if index:
                try:
                    next_idx = max(int(k) for k in index.keys() if str(k).isdigit()) + 1
                except ValueError:
                    next_idx = 1

            actor_raw = (request.form.get('actor') or '').strip().lower()
            direction_raw = (request.form.get('log_direction') or '').strip().lower()
            if not actor_raw:
                actor_raw = 'consultant' if direction_raw == 'outgoing' else 'customer'
            entry = {
                'who': 'consultant' if actor_raw == 'consultant' else 'customer',
                'method': (request.form.get('log_method') or 'Unspecified').strip(),
                'body': (request.form.get('log_body') or '').strip(),
            }
            index[str(next_idx)] = entry
            try:
                _save_json_object(comm_index_path, index)
            except OSError:
                flash('Could not save the communication log.', 'error')
            return 'log'

        if form_type == 'todo_add':
            text = (request.form.get('todo_text') or '').strip()
            if not text:
                return 'todo_add'

            # Build inputs for LLM
            lead_id_for_todo = record_id
            if record_type in {'quote', 'booking'}:
                lead_id_for_todo = record_id  # directory name is the 7-digit lead id
            today_str = datetime.utcnow().strftime('%d-%m-%Y')

            try:
                todo = process_todo_submission(lead_id=lead_id_for_todo, today=today_str, text=text)
            except LLMNotConfigured as exc:
                # Fallback: store raw text locally without LLM enrichment
                todos = payload.setdefault('todos', [])
                todos.append(
                    {
                        'id': uuid4().hex,
                        'text': text,
                        'done': False,
                        'created_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                    }
                )
                flash(str(exc), 'error')
                return 'todo_add'
            except Exception as exc:  # pragma: no cover - external service dependent
                flash(f'Unable to process task via assistant: {exc}', 'error')
                return 'todo_add'

            # Persist to standalone todos.json within the record directory
            todos_index_path = record_dir / TODOS_FILENAME
            existing = _load_json_object(todos_index_path)
            next_idx = 1
            if existing:
                try:
                    next_idx = max(int(k) for k in existing.keys() if str(k).isdigit()) + 1
                except ValueError:
                    next_idx = 1
            entry_key = str(next_idx)
            client_now = (request.form.get('client_now') or '').strip() or None
            created_at = client_now or datetime.utcnow().isoformat(timespec='seconds')
            existing[entry_key] = {
                'text': todo.task if 'todo' in locals() else text,
                'due_date': (todo.date_to_be_done if 'todo' in locals() else None) or None,
                'status': 'Active',
                'created_at': created_at,
            }
            try:
                _save_json_object(todos_index_path, existing)
            except OSError:
                flash('Could not save the To Do file.', 'error')
            return 'todo_add'

        if form_type == 'todo_toggle':
            todo_id = (request.form.get('todo_id') or '').strip()
            desired_str = (request.form.get('done') or '').strip().lower()
            desired = True if desired_str in {'1', 'true', 'yes', 'on'} else False
            todos_index_path = record_dir / TODOS_FILENAME
            existing = _load_json_object(todos_index_path)
            if todo_id in existing:
                existing[todo_id]['status'] = 'Completed' if desired else 'Active'
            else:
                for key, item in existing.items():
                    if isinstance(item, dict) and item.get('id') == todo_id:
                        item['status'] = 'Completed' if desired else 'Active'
                        break
            try:
                _save_json_object(todos_index_path, existing)
            except OSError:
                flash('Could not update the To Do file.', 'error')
            return 'todo_toggle'

        if form_type == 'todo_delete':
            todo_id = (request.form.get('todo_id') or '').strip()
            todos_index_path = record_dir / TODOS_FILENAME
            existing = _load_json_object(todos_index_path)
            if todo_id in existing:
                existing.pop(todo_id, None)
            else:
                to_remove = None
                for key, item in existing.items():
                    if isinstance(item, dict) and item.get('id') == todo_id:
                        to_remove = key
                        break
                if to_remove:
                    existing.pop(to_remove, None)
            try:
                _save_json_object(todos_index_path, existing)
            except OSError:
                flash('Could not update the To Do file.', 'error')
            return 'todo_delete'

        if form_type == 'document_upload':
            file = request.files.get('document_file')
            if not file or not file.filename:
                flash('Please choose a document to upload.', 'error')
                return None
            name = secure_filename(file.filename) or 'upload'
            documents_dir = record_dir / 'documents'
            documents_dir.mkdir(parents=True, exist_ok=True)
            target = documents_dir / name
            if target.exists():
                stem = target.stem
                suffix = target.suffix
                idx = 2
                while True:
                    candidate = documents_dir / f"{stem} ({idx}){suffix}"
                    if not candidate.exists():
                        target = candidate
                        break
                    idx += 1
            try:
                file.save(target)
            except Exception:
                flash('Could not save the uploaded file.', 'error')
                return None
            return 'document_upload'

        return None

    if record_type in {'enquiry', 'quote', 'booking'} and request.method == 'POST':
        update_kind = apply_journal_update()
        if update_kind:
            try:
                with payload_path.open('w', encoding='utf-8') as handle:
                    json.dump(payload, handle, indent=2)
            except OSError:
                abort(500)
            else:
                if update_kind == 'notes':
                    flash('Notes saved to the SkyDesk archive.', 'success')
                elif update_kind == 'log':
                    flash('Communication log updated for this lead.', 'success')
                elif update_kind == 'todo_add':
                    flash('To Do added to this lead.', 'success')
                elif update_kind == 'todo_toggle':
                    flash('To Do updated for this lead.', 'success')
                elif update_kind == 'todo_delete':
                    flash('To Do removed from this lead.', 'success')
                elif update_kind == 'document_upload':
                    flash('Document uploaded to this lead.', 'success')
        # Support optional redirect back (e.g., dashboard actions)
        next_url = (request.form.get('next') or '').strip()
        if next_url.startswith('/') and '//' not in next_url:
            return redirect(next_url)
        return redirect(url_for('lead_detail', record_type=record_type, record_id=record_id))

    # Prefer external communications index if available
    comm_index_path = (get_record_directory(directory, record_id) / COMMUNICATIONS_FILENAME)
    comm_index = _load_json_object(comm_index_path)
    communications_source = comm_index if comm_index else (payload.get('communications', []) or [])
    communications_display = build_communication_entries(communications_source)

    if record_type == 'quote':
        record_dir = get_record_directory(directory, record_id)
        metadata = {}
        metadata_path = record_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with metadata_path.open('r', encoding='utf-8') as handle:
                    metadata = json.load(handle)
            except (OSError, json.JSONDecodeError):
                metadata = {}

        documents: List[str] = []
        documents_dir = record_dir / 'documents'
        if documents_dir.exists():
            documents = [item.name for item in documents_dir.iterdir() if item.is_file()]

        timeline_entries = build_quote_timeline(payload)

        # Build To Dos for UI from external file if available
        todos_index = _load_json_object(record_dir / TODOS_FILENAME)
        todos_ui: List[dict] = []
        if todos_index:
            for key in sorted((k for k in todos_index.keys() if str(k).isdigit()), key=lambda x: int(x)):
                item = todos_index.get(key) or {}
                if isinstance(item, dict):
                    todos_ui.append({
                        'id': key,
                        'text': item.get('text') or '',
                        'due_date': item.get('due_date') or None,
                        'done': (item.get('status') or '').lower() == 'completed',
                    })
        else:
            for item in payload.get('todos') or []:
                if isinstance(item, dict):
                    todos_ui.append(item)

        return render_template(
            'record_detail.html',
            record_type='quote',
            record_id=record_id,
            record=payload,
            metadata=metadata,
            documents=documents,
            timeline_entries=timeline_entries,
            communications=communications_display,
            default_timestamp=default_timestamp,
            payments=None,
            status=None,
            todos=todos_ui,
        )

    if record_type == 'booking':
        record_dir = get_record_directory(directory, record_id)
        metadata = {}
        metadata_path = record_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with metadata_path.open('r', encoding='utf-8') as handle:
                    metadata = json.load(handle)
            except (OSError, json.JSONDecodeError):
                metadata = {}

        documents: List[str] = []
        documents_dir = record_dir / 'documents'
        if documents_dir.exists():
            documents = [item.name for item in documents_dir.iterdir() if item.is_file()]

        payments = payload.get('payments') or {}
        status = payload.get('status') or {}
        timeline_entries = build_booking_timeline(payload)

        # Build To Dos for UI from external file if available
        todos_index = _load_json_object(record_dir / TODOS_FILENAME)
        todos_ui: List[dict] = []
        if todos_index:
            for key in sorted((k for k in todos_index.keys() if str(k).isdigit()), key=lambda x: int(x)):
                item = todos_index.get(key) or {}
                if isinstance(item, dict):
                    todos_ui.append({
                        'id': key,
                        'text': item.get('text') or '',
                        'due_date': item.get('due_date') or None,
                        'done': (item.get('status') or '').lower() == 'completed',
                    })
        else:
            for item in payload.get('todos') or []:
                if isinstance(item, dict):
                    todos_ui.append(item)

        return render_template(
            'record_detail.html',
            record_type='booking',
            record_id=record_id,
            record=payload,
            metadata=metadata,
            documents=documents,
            payments=payments,
            status=status,
            timeline_entries=timeline_entries,
            communications=communications_display,
            default_timestamp=default_timestamp,
            todos=todos_ui,
        )

    if record_type != 'enquiry':
        abort(404)

    schedule = payload.get('schedule', {}) or {}
    travel_display, _ = build_travel_dates(schedule)

    trip_length_value = schedule.get('trip_length_value')
    trip_length_unit = schedule.get('trip_length_unit')
    trip_length_display = None
    if trip_length_value:
        unit = trip_length_unit or 'days'
        trip_length_display = f"{trip_length_value} {unit}"

    travellers = payload.get('travellers', {}) or {}
    traveller_fields = [
        ('Adults', travellers.get('adults', 0)),
        ('Children', travellers.get('children', 0)),
        ('Infants', travellers.get('infants', 0)),
    ]

    # To Dos for enquiry
    todos_index = _load_json_object((get_record_directory(directory, record_id) / TODOS_FILENAME))
    todos_ui: List[dict] = []
    if todos_index:
        for key in sorted((k for k in todos_index.keys() if str(k).isdigit()), key=lambda x: int(x)):
            item = todos_index.get(key) or {}
            if isinstance(item, dict):
                todos_ui.append({
                    'id': key,
                    'text': item.get('text') or '',
                    'due_date': item.get('due_date') or None,
                    'done': (item.get('status') or '').lower() == 'completed',
                })
    else:
        for item in payload.get('todos') or []:
            if isinstance(item, dict):
                todos_ui.append(item)

    # Enquiry documents list
    documents: List[str] = []
    documents_dir = record_dir / 'documents'
    if documents_dir.exists():
        documents = [item.name for item in documents_dir.iterdir() if item.is_file()]

    lead_context = {
        'record_id': record_id,
        'record_type': record_type,
        'name_display': payload.get('name') or 'N/A',
        'phone': payload.get('phone') or 'N/A',
        'email': payload.get('email') or 'N/A',
        'destination': payload.get('destination') or 'N/A',
        'submitted_at_display': format_submitted_date(payload.get('submitted_at')),
        'travel_dates': travel_display,
        'departure_date': schedule.get('departure_date'),
        'return_date': schedule.get('return_date'),
        'flex_month': schedule.get('flex_month'),
        'trip_length_display': trip_length_display,
        'notes': payload.get('notes') or '',
        'todos': todos_ui,
    }

    return render_template(
        'leads_detail.html',
        lead=lead_context,
        travellers=traveller_fields,
        record_type_title=record_type.capitalize(),
        communications=communications_display,
        default_timestamp=default_timestamp,
        documents=documents,
    )

def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    """Best-effort parser for ISO-ish datetime strings."""
    if not value:
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    if cleaned.endswith('Z'):
        cleaned = cleaned[:-1]

    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        formats = (
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M',
        )
        for fmt in formats:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue

    return None


def build_communication_entries(raw_entries) -> List[dict]:
    """Normalise persisted communication entries for template rendering.

    Supports two shapes:
    - Legacy list of dicts with keys: timestamp, method, direction, note
    - New dict index {"1": {who, method, body}, ...}
    """
    # If provided a dict (new storage), convert to ordered list
    if isinstance(raw_entries, dict):
        items: List[dict] = []
        for key in sorted((k for k in raw_entries.keys() if str(k).isdigit()), key=lambda x: int(x), reverse=True):
            entry = raw_entries.get(key) or {}
            if not isinstance(entry, dict):
                continue
            who = (entry.get('who') or 'customer').strip().lower()
            direction = 'outgoing' if who == 'consultant' else 'incoming'
            items.append(
                {
                    'timestamp': None,
                    'method': (entry.get('method') or 'Unspecified').strip(),
                    'direction': direction,
                    'note': (entry.get('body') or '').strip(),
                    '_seq_hint': int(key),
                }
            )
        raw_entries = items

    if not isinstance(raw_entries, list):
        return []

    direction_styles = {
        # Higher-contrast pills for quick scanning
        'incoming': ('Customer', 'border-emerald-400 bg-emerald-500/30 text-emerald-100'),
        'outgoing': ('Consultant', 'border-accent bg-accent/80 text-white'),
    }

    prepared: List[dict] = []

    for index, entry in enumerate(raw_entries):
        if not isinstance(entry, dict):
            continue

        timestamp_raw = entry.get('timestamp')
        timestamp_value = parse_iso_datetime(timestamp_raw)
        timestamp_display = '—' if timestamp_raw is None else 'Unknown time'
        sort_ts = ''
        sort_key = datetime.min
        if timestamp_value:
            timestamp_display = timestamp_value.strftime('%d %b %Y at %H:%M')
            sort_key = timestamp_value
            sort_ts = timestamp_value.isoformat()

        method_raw = (entry.get('method') or 'Unspecified').strip()
        method_display = f"via {method_raw}" if method_raw else 'via Unspecified'

        direction_key = (entry.get('direction') or 'incoming').strip().lower()
        badge_text, badge_class = direction_styles.get(direction_key, direction_styles['incoming'])

        # Use numeric key hint when available to improve relative ordering
        seq_value = entry.get('_seq_hint') if isinstance(entry.get('_seq_hint'), int) else index

        prepared.append(
            {
                'badge_text': badge_text,
                'badge_class': badge_class,
                'timestamp_display': timestamp_display,
                'method_display': method_display,
                'note': (entry.get('note') or '').strip(),
                'sort_ts': sort_ts,
                'seq': seq_value,
                # Default newest-first: sort by timestamp desc, then seq desc
                '_sort_key': (sort_key, seq_value),
            }
        )

    prepared.sort(key=lambda item: item['_sort_key'], reverse=True)
    for item in prepared:
        item.pop('_sort_key', None)

    return prepared


def collect_active_todos(*, type_labels: Dict[str, str]) -> List[dict]:
    """Scan all records and collect active (not done) To Dos for dashboard display."""
    results: List[dict] = []

    def _parse_due(value: Optional[str]) -> datetime:
        if not value:
            return datetime.max
        for fmt in ('%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return datetime.max

    for record_type, directory in LEAD_DIRECTORIES.items():
        if not directory.exists():
            continue
        for record_dir in directory.iterdir():
            if not record_dir.is_dir():
                continue
            payload_path = record_dir / RECORD_FILENAME
            if not payload_path.exists():
                continue
            try:
                with payload_path.open('r', encoding='utf-8') as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue

            # Prefer external todos index if available
            todos_path = record_dir / TODOS_FILENAME
            todos_index = _load_json_object(todos_path)
            todos: List[dict] = []
            if todos_index:
                for key in todos_index.keys():
                    item = todos_index.get(key) or {}
                    if isinstance(item, dict):
                        todos.append({
                            'text': item.get('text') or '',
                            'due_date': item.get('due_date') or None,
                            'done': (item.get('status') or '').lower() == 'completed',
                            'todo_id': str(key),
                        })
            else:
                todos = payload.get('todos') or []
                if not isinstance(todos, list):
                    todos = []
            name_display = payload.get('name') or (payload.get('client') or {}).get('name') or 'N/A'
            for item in todos:
                if not isinstance(item, dict):
                    continue
                if item.get('done') is True:
                    continue
                text = (item.get('text') or '').strip()
                if not text:
                    continue
                due = (item.get('due_date') or '').strip()
                results.append(
                    {
                        'record_id': record_dir.name,
                        'record_type': record_type,
                        'type_label': type_labels.get(record_type, record_type.title()),
                        'text': text,
                        'due_display': due or None,
                        'due_sort': _parse_due(due),
                        'name_display': name_display,
                        'detail_url': url_for('lead_detail', record_type=record_type, record_id=record_dir.name),
                        'todo_id': item.get('todo_id') or item.get('id') or '',
                    }
                )

    results.sort(key=lambda x: (x['due_sort'], x['type_label'], x['name_display'].lower()))
    for item in results:
        item.pop('due_sort', None)
    return results


def generate_record_id() -> str:
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    return f"{timestamp}_{uuid4().hex}"


def build_enquiry_payload(form) -> Tuple[dict, Dict[str, str]]:
    def clean_text(key: str) -> str:
        return (form.get(key) or '').strip()

    def clean_int(key: str, default: int = 0) -> int:
        value = clean_text(key)
        if not value:
            return default
        try:
            return max(int(value), 0)
        except ValueError:
            return default

    def clean_positive_int_or_none(key: str):
        value = clean_text(key)
        if not value:
            return None
        try:
            parsed = int(value)
        except ValueError:
            return None
        return parsed if parsed >= 0 else None

    name = clean_text('name')
    phone = clean_text('phone')
    email = clean_text('email')
    departure_date = clean_text('departure_date') or None
    return_date = clean_text('return_date') or None
    flex_month_month = clean_text('flex_month_month')
    flex_month_year = clean_text('flex_month_year')
    flex_month = None
    if flex_month_month and flex_month_year:
        if re.match(r'^(0[1-9]|1[0-2])$', flex_month_month) and re.match(r'^\d{4}$', flex_month_year):
            flex_month = f"{flex_month_month}/{flex_month_year}"
    trip_length_value = clean_positive_int_or_none('trip_length_value')
    trip_length_unit_raw = clean_text('trip_length_unit').lower()
    allowed_units = {'days', 'weeks', 'months'}
    trip_length_unit = trip_length_unit_raw if trip_length_unit_raw in allowed_units else None
    if trip_length_value is None:
        trip_length_unit = None
    elif trip_length_unit is None:
        trip_length_unit = 'days'

    payload = {
        'record_type': 'enquiry',
        'submitted_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'name': name,
        'phone': phone,
        'email': email,
        'destination': clean_text('destination'),
        'travellers': {
            'adults': clean_int('travellers_adults', default=1),
            'children': clean_int('travellers_children'),
            'infants': clean_int('travellers_infants'),
        },
        'schedule': {
            'departure_date': departure_date or None,
            'return_date': return_date or None,
            'flex_month': flex_month or None,
            'flex_month_month': flex_month_month or None,
            'flex_month_year': flex_month_year or None,
            'trip_length_value': trip_length_value,
            'trip_length_unit': trip_length_unit,
        },
        'notes': clean_text('notes') or None,
    }

    field_errors: dict[str, str] = {}

    if not name:
        field_errors['name'] = 'Name is required.'
    if not email:
        field_errors['email'] = 'Email is required.'
    if not phone:
        field_errors['phone'] = 'Phone number is required.'

    # Basic format validation (defensive; UI also guides input)
    if email:
        # very lightweight email format check
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            field_errors['email'] = 'Please enter a valid email address.'
    if phone:
        # allow digits, space, +, -, parentheses; require at least 7 digits
        digits_only = re.sub(r"\D", "", phone)
        if len(digits_only) < 7:
            field_errors['phone'] = 'Please enter a valid phone number.'

    return payload, field_errors


def persist_enquiry(record_id: str, payload: dict) -> None:
    ENQUIRY_DIR.mkdir(parents=True, exist_ok=True)
    record_dir = ENQUIRY_DIR / record_id
    record_dir.mkdir(parents=True, exist_ok=True)
    target_path = record_dir / RECORD_FILENAME

    with target_path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)


def default_enquiry_form() -> dict:
    return {
        'name': '',
        'phone': '',
        'email': '',
        'destination': '',
        'travellers_adults': '1',
        'travellers_children': '0',
        'travellers_infants': '0',
        'departure_date': '',
        'return_date': '',
        'flex_month_month': '',
        'flex_month_year': '',
        'trip_length_value': '',
        'trip_length_unit': 'days',
        'notes': '',
    }


def get_month_options() -> List[Tuple[str, str]]:
    return [
        ('', 'Month'),
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ]


def get_year_options(span: int = 6) -> List[str]:
    current_year = datetime.utcnow().year
    return [str(current_year + offset) for offset in range(span)]


def load_leads(record_type: str) -> List[dict]:
    directory = LEAD_DIRECTORIES.get(record_type)
    if not directory or not directory.exists():
        return []

    records: List[dict] = []
    for record_dir in sorted(directory.iterdir(), reverse=True):
        if not record_dir.is_dir():
            continue

        payload_path = record_dir / RECORD_FILENAME
        if not payload_path.exists():
            continue

        try:
            with payload_path.open('r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue

        trip_locations: List[str] = []
        travel_display = 'N/A'
        travel_value = 'zzzz'

        submitted_raw = payload.get('submitted_at')
        submitted_display = format_submitted_date(submitted_raw)
        submitted_value = submitted_raw or ''

        if record_type == 'enquiry':
            schedule = payload.get('schedule', {}) or {}
            travel_display, travel_value = build_travel_dates(schedule)
            trip_locations = [payload.get('destination')] if payload.get('destination') else []
        else:
            trip = payload.get('trip', {}) or {}
            trip_locations = trip.get('locations') or []
            dates = trip.get('dates', {}) or {}
            start = dates.get('start')
            end = dates.get('end')
            if start and end:
                travel_display = f"{format_travel_date(start)} - {format_travel_date(end)}"
                travel_value = f"{start}|{end}"
            elif dates.get('nights'):
                travel_display = f"{dates.get('nights')} nights"
            submitted_display = payload.get('issued_at') or submitted_display
            submitted_value = payload.get('issued_at') or submitted_value

        name_display = payload.get('name') or payload.get('client', {}).get('name') or 'N/A'
        destination_display = payload.get('destination') or ', '.join(filter(None, trip_locations)) or 'N/A'

        records.append(
            {
                'record_id': record_dir.name,
                'record_type': record_type,
                'submitted_at_display': submitted_display,
                'submitted_at_value': submitted_value,
                'name_display': name_display,
                'name_value': name_display.lower(),
                'destination_display': destination_display,
                'destination_value': destination_display.lower(),
                'travel_dates_display': travel_display,
                'travel_dates_value': travel_value,
            }
        )

    return records


def build_travel_dates(schedule: dict) -> Tuple[str, str]:
    departure = schedule.get('departure_date')
    return_date = schedule.get('return_date')
    if departure and return_date:
        departure_fmt = format_travel_date(departure)
        return_fmt = format_travel_date(return_date)
        return f"{departure_fmt} - {return_fmt}", f"{departure}|{return_date}"

    flex_month = schedule.get('flex_month')
    if flex_month:
        month = schedule.get('flex_month_month')
        year = schedule.get('flex_month_year')
        if month and year:
            value = f"{year}-{month}"
        else:
            parts = flex_month.split('/')
            value = f"{parts[1]}-{parts[0]}" if len(parts) == 2 else flex_month
        return f"Flex {flex_month}", value

    return "N/A", "zzzz"


def format_travel_date(raw: str) -> str:
    for fmt in ('%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(raw, fmt).strftime('%d %b %Y')
        except (TypeError, ValueError):
            continue
    return raw or "N/A"


def format_submitted_date(raw: Optional[str]) -> str:
    if not raw:
        return "N/A"

    try:
        cleaned = raw.replace('Z', '+00:00') if raw.endswith('Z') else raw
        dt_value = datetime.fromisoformat(cleaned)
        return dt_value.strftime('%d %b %Y')
    except ValueError:
        return raw or "N/A"


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):  # type: ignore[unused-argument]
    """Provide a friendly message when uploads exceed MAX_CONTENT_LENGTH."""
    try:
        flash('Upload too large. Maximum allowed size is 10MB.', 'error')
        # Redirect back to new lead intake if relevant; otherwise generic 413
        from flask import request
        if request.path.startswith('/leads/new'):
            return redirect(url_for('leads_new'))
    except Exception:
        pass
    return ('File too large. Maximum allowed size is 10MB.', 413)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8008, debug=True)










