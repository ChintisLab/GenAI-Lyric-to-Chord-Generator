from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from .models import ChordPlan, SongRequest
from .preprocessing import format_lines_for_prompt, prepare_lyrics_with_limits

DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """
You are helping with songwriting and chord arrangement.
Given lyrics, return a musically coherent chord plan.

Rules:
- Return JSON only.
- Use common chord symbols (C, G, Am, F#, Bm7, D/F#).
- Keep line_chords aligned with the original lyric lines.
- line_number must start at 1 and be sequential.
- Keep chords practical for guitar or piano accompaniment.

Required JSON schema:
{
  "mood": "string",
  "key": "string",
  "tempo_bpm": 90,
  "time_signature": "4/4",
  "progression": {
    "verse": ["C", "G", "Am", "F"],
    "chorus": ["F", "G", "C", "Am"]
  },
  "line_chords": [
    {
      "line_number": 1,
      "lyric": "lyric line text",
      "chords": ["C", "G"]
    }
  ],
  "notes": "short arrangement notes"
}
""".strip()


def build_user_prompt(request: SongRequest, lines: list[str]) -> str:
    genre = request.genre or "Not specified"
    key_preference = request.key_preference or "No key preference"
    tempo_hint = str(request.tempo_hint) if request.tempo_hint else "No tempo preference"
    numbered_lines = format_lines_for_prompt(lines)

    return f"""
Song details:
- Genre: {genre}
- Key preference: {key_preference}
- Tempo hint: {tempo_hint}

Lyrics (numbered):
{numbered_lines}

Return JSON only. No markdown, no explanations.
""".strip()


def extract_json_payload(raw_content: str) -> dict[str, Any]:
    content = raw_content.strip()

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
    if fenced:
        content = fenced.group(1)
    else:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            content = content[start : end + 1]

    return json.loads(content)


def validate_line_alignment(source_lines: list[str], plan: ChordPlan) -> None:
    if len(source_lines) != len(plan.line_chords):
        raise ValueError("Line count mismatch between lyrics and generated chords.")

    for expected, line_data in enumerate(plan.line_chords, start=1):
        if line_data.line_number != expected:
            raise ValueError("Generated line numbers are not sequential.")


def generate_chord_plan(
    request: SongRequest,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
    max_retries: int = 1,
) -> ChordPlan:
    lines, _ = prepare_lyrics_with_limits(request.lyrics)
    if client is None:
        client = OpenAI(api_key=api_key)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(request, lines)},
    ]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""

        try:
            payload = extract_json_payload(content)
            plan = ChordPlan.model_validate(payload)
            validate_line_alignment(lines, plan)
            return plan
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            messages.append({"role": "assistant", "content": content[:3000]})
            messages.append(
                {
                    "role": "user",
                    "content": "Your response was invalid. Return only valid JSON that follows the schema exactly.",
                }
            )

    raise ValueError(f"Could not generate a valid chord plan. {last_error}") from last_error
