"""Lightweight LLM client wrapper so the app can talk to OpenAI generically."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional quality of life helper
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def _bootstrap_env() -> None:
    """Ensure .env variables are available even outside Flask."""

    if load_dotenv is not None:
        load_dotenv()
        return

    env_path = Path(__file__).resolve().parents[1] / '.env'
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


_bootstrap_env()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore


logger = logging.getLogger(__name__)


class LLMNotConfigured(RuntimeError):
    """Raised when the LLM SDK or credentials are unavailable."""


@dataclass(frozen=True)
class LLMResponse:
    """Minimal response container used across the app."""

    content: str


def _client() -> OpenAI:
    if OpenAI is None:
        raise LLMNotConfigured('Install the `openai` package to use LLM features.')

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise LLMNotConfigured('OPENAI_API_KEY missing; add it to your environment/.env.')

    return OpenAI(api_key=api_key)


def chat(
    messages: list[dict[str, str]],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    enforce_json: bool = True,
) -> LLMResponse:
    """Call the chat completion endpoint and return the text body."""

    client = _client()
    # Default to 4.1 nano unless overridden via OPENAI_MODEL or function arg
    model_name = model or os.getenv('OPENAI_MODEL', 'gpt-4.1-nano')
    temp = temperature if temperature is not None else float(os.getenv('OPENAI_TEMPERATURE', '0'))

    logger.debug('Calling OpenAI chat: model=%s temperature=%s enforce_json=%s', model_name, temp, enforce_json)

    kwargs = {
        'model': model_name,
        'temperature': temp,
        'messages': messages,
    }
    if enforce_json:
        # Use JSON response format when supported by the model; otherwise fallback below.
        kwargs['response_format'] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:  # pragma: no cover - SDK/model dependent
        if enforce_json:
            logger.warning('JSON response_format not supported, retrying without it: %s', exc)
            response = client.chat.completions.create(
                model=model_name, temperature=temp, messages=messages
            )
        else:
            raise

    content = response.choices[0].message.content or ''
    logger.debug('OpenAI response chars=%s', len(content))
    return LLMResponse(content=content.strip())
