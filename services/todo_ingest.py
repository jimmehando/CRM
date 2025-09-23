"""Pipeline to create a structured To Do via LLM from free text."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
    due = str(parsed.get('date_to_be_done') or '').strip()
    return TodoItem(lead_id=lead, task=task, date_to_be_done=due)

