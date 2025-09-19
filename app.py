import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, redirect, request, url_for

app = Flask(__name__)

LEADS_DIR = Path(app.root_path) / 'leads'
LEADS_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/leads/new', methods=['GET', 'POST'])
def leads_new():
    if request.method == 'POST':
        lead = {
            'quote_id': request.form.get('quote_id', '').strip(),
            'lead_name': request.form.get('lead_name', '').strip(),
            'lead_email': request.form.get('lead_email', '').strip(),
            'lead_phone': request.form.get('lead_phone', '').strip(),
            'origin': request.form.get('origin', '').strip(),
            'departure': request.form.get('departure', '').strip(),
            'depart_date': request.form.get('depart_date', '').strip(),
            'return_date': request.form.get('return_date', '').strip(),
            'source': request.form.get('source', '').strip(),
            'status': request.form.get('status', '').strip(),
            'notes': request.form.get('notes', '').strip(),
            'submitted_at': datetime.utcnow().isoformat() + 'Z'
        }

        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        reference = lead['quote_id'] or f'lead-{timestamp}'
        safe_reference = re.sub(r'[^A-Za-z0-9_-]', '_', reference).strip('_') or f'lead-{timestamp}'

        filename = f"{safe_reference}.json"
        counter = 1
        path = LEADS_DIR / filename
        while path.exists():
            filename = f"{safe_reference}-{counter}.json"
            path = LEADS_DIR / filename
            counter += 1

        with path.open('w', encoding='utf-8') as handle:
            json.dump(lead, handle, indent=2)

        return redirect(url_for('dashboard'))

    return render_template('leads_new.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8008, debug=True)
