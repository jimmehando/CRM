"""Pipeline to create a structured To Do via LLM from free text."""

from __future__ import annotations

import json
from dataclasses import dataclass
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import llm_client

PROMPT_PATH = Path('ops/assistants/todo_parser.md')


@dataclass(frozen=True)
class TodoItem:
    lead_id: str
    task: str
    date_to_be_done: str


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding='utf-8').strip()


def _build_messages(prompt: str, *, lead_id: str, today: str, text: str) -> list[dict[str, str]]:
    user_content = (
        f"LEAD_ID: {lead_id}\n"
        f"TODAY: {today}\n"
        f"TASK: {text.strip()}\n"
    )
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]


def _coerce_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        pass
    # Code fences fallback
    import re
    for pattern in (r"```json\s*(.*?)```", r"```\s*(.*?)```"):
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        for block in matches:
            try:
                return json.loads(block.strip())
            except Exception:
                continue
    # Largest brace object
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass
    raise ValueError('LLM response was not valid JSON.')


def process_todo_submission(*, lead_id: str, today: str, text: str) -> TodoItem:
    prompt = _load_prompt()
    messages = _build_messages(prompt, lead_id=lead_id, today=today, text=text)
    response = llm_client.chat(messages, enforce_json=True)
    parsed = _coerce_json_object(response.content)
    if not isinstance(parsed, dict):
        raise ValueError('LLM response must be a JSON object for todo generation.')
    # Basic shape validation; tolerate minor casing/spacing issues
    lead = str(parsed.get('lead_id') or lead_id)
    task = str(parsed.get('task') or text).strip()
    raw_due = str(parsed.get('date_to_be_done') or '').strip()
    due = _normalise_due_date(raw_due)
    return TodoItem(lead_id=lead, task=task, date_to_be_done=due)


def _normalise_due_date(value: str) -> str:
    """Best-effort normaliser to DD-MM-YYYY.

    Accepts common variants like:
    - DD-MM-YYYY, YYYY-MM-DD
    - DD/MM/YYYY, YYYY/MM/DD
    - MM/YYYY or M/YYYY (assumes day 01)
    - Month YYYY or 'Month of YYYY' (assumes day 01)
    Returns an empty string when the date cannot be parsed.
    """
    if not value:
        return ''

    s = value.strip()

    # Replace slashes with dashes for simpler matching later
    s2 = s.replace('/', '-')

    # 1) Direct parse with common formats
    for fmt_in in ('%d-%m-%Y', '%Y-%m-%d'):
        try:
            dt = datetime.strptime(s2, fmt_in)
            return dt.strftime('%d-%m-%Y')
        except ValueError:
            pass

    # 2) DD/MM/YYYY or YYYY/MM/DD (original s)
    for fmt_in in ('%d/%m/%Y', '%Y/%m/%d'):
        try:
            dt = datetime.strptime(s, fmt_in)
            return dt.strftime('%d-%m-%Y')
        except ValueError:
            pass

    # 3) MM-YYYY (or M-YYYY)
    m = re.fullmatch(r'(\d{1,2})[-/](\d{4})', s)
    if m:
        month = int(m.group(1))
        year = int(m.group(2))
        if 1 <= month <= 12:
            return f"01-{month:02d}-{year:04d}"

    # 4) Month words like "May 2027" or "May of 2027"
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    }
    word_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s*(?:of\s*)?(\d{4})', s, flags=re.IGNORECASE)
    if word_match:
        month = months[word_match.group(1).lower()]
        year = int(word_match.group(2))
        return f"01-{month:02d}-{year:04d}"

    # If unknown, return as-is (may still display but won’t sort well)
    return s
