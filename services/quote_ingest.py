"""Pipeline used when a new quote PDF is submitted."""

from __future__ import annotations

import json
from dataclasses import dataclass
import re
from pathlib import Path
from typing import Optional

from . import llm_client

PROMPT_PATH = Path('ops/assistants/quote_parser.md')


@dataclass(frozen=True)
class QuoteDraft:
    """Output of the quote ingestion pipeline before user confirmation."""

    parsed: dict
    raw_response: str
    transcript: str


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding='utf-8').strip()


def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader  # lazy import to avoid boot-time crash
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            'PDF ingestion requires the pypdf package. Install with: pip install pypdf'
        ) from exc

    reader = PdfReader(str(pdf_path))
    return '\n'.join(page.extract_text() or '' for page in reader.pages)


def _build_messages(prompt: str, transcript: str, notes: Optional[str]) -> list[dict[str, str]]:
    user_content = transcript
    if notes:
        user_content = f"{user_content}\n\nCONSULTANT_NOTES:\n{notes.strip()}"
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]


def process_quote_submission(pdf_path: Path, *, notes: Optional[str] = None) -> QuoteDraft:
    """Convert a submitted PDF into structured JSON via LLM."""

    transcript = _extract_pdf_text(pdf_path)
    prompt = _read_prompt()
    messages = _build_messages(prompt, transcript, notes)
    response = llm_client.chat(messages, enforce_json=True)

    # Be resilient if the model adds pre/post text or code fences
    parsed = _coerce_json_object(response.content)

    if not isinstance(parsed, dict):
        raise ValueError('LLM response must be a JSON object for quote ingestion.')

    return QuoteDraft(parsed=parsed, raw_response=response.content, transcript=transcript)


def _coerce_json_object(text: str) -> dict:
    """Attempt to parse JSON, tolerating code fences or surrounding prose."""
    # 1) Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Code fences (```json ... ``` or ``` ... ```)
    for pattern in (r"```json\s*(.*?)```", r"```\s*(.*?)```"):
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        for block in matches:
            try:
                return json.loads(block.strip())
            except Exception:
                continue

    # 3) Largest brace-delimited block
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # If all attempts fail, raise a clear error
    raise ValueError('LLM response was not valid JSON.')
