from __future__ import annotations

import re

MAX_INPUT_CHARS = 5000
MAX_INPUT_LINES = 120
WHITESPACE_RE = re.compile(r"\s+")


def normalize_line(line: str) -> str:
    return WHITESPACE_RE.sub(" ", line).strip()


def prepare_lyrics_with_limits(
    raw: str,
    *,
    max_chars: int = MAX_INPUT_CHARS,
    max_lines: int = MAX_INPUT_LINES,
) -> tuple[list[str], bool]:
    if raw is None:
        raise ValueError("Please paste your lyrics before generating chords.")

    text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        raise ValueError("Please paste your lyrics before generating chords.")

    truncated = False
    if len(text) > max_chars:
        text = text[:max_chars]
        truncated = True

    lines = [normalize_line(line) for line in text.split("\n")]
    lines = [line for line in lines if line]

    if not lines:
        raise ValueError("The input only contains blank lines.")

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True

    return lines, truncated


def prepare_lyrics(raw: str) -> list[str]:
    lines, _ = prepare_lyrics_with_limits(raw)
    return lines


def format_lines_for_prompt(lines: list[str]) -> str:
    return "\n".join(f"{idx}. {line}" for idx, line in enumerate(lines, start=1))
