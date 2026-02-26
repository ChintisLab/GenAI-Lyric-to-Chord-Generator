from __future__ import annotations

from functools import lru_cache
import re
from typing import Callable

from .models import ChordPlan, LineChord, SongRequest
from .preprocessing import prepare_lyrics_with_limits

try:
    from transformers import pipeline
except Exception:  # pragma: no cover - fallback path only used when dependency is missing
    pipeline = None


DEFAULT_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
DEFAULT_MODE = "local-free"

NOTE_ORDER = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT_TO_SHARP = {
    "Db": "C#",
    "Eb": "D#",
    "Gb": "F#",
    "Ab": "G#",
    "Bb": "A#",
}

MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]

ROMAN_TO_DEGREE = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
}

ENERGY_HINTS = {"dance", "fire", "run", "alive", "tonight", "wild", "high", "light"}
POSITIVE_HINTS = {"love", "hope", "bright", "smile", "home", "sun", "rise"}
NEGATIVE_HINTS = {"alone", "cry", "pain", "dark", "empty", "lost", "broken"}

GENRE_TEMPO = {
    "pop": 104,
    "rock": 120,
    "indie": 102,
    "rnb": 92,
    "hiphop": 88,
    "folk": 86,
    "ballad": 74,
}

MoodDetector = Callable[[str, str], tuple[str, float]]


@lru_cache(maxsize=2)
def get_sentiment_pipeline(model_name: str):
    if pipeline is None:
        return None
    try:
        return pipeline("sentiment-analysis", model=model_name)
    except Exception:
        return None


def normalize_note(note: str) -> str:
    cleaned = note.strip().capitalize()
    if len(cleaned) >= 2 and cleaned[1] in {"b", "#"}:
        cleaned = cleaned[0].upper() + cleaned[1]
    else:
        cleaned = cleaned[0].upper()
    return FLAT_TO_SHARP.get(cleaned, cleaned)


def parse_key_preference(key_text: str | None) -> tuple[str, str] | None:
    if not key_text:
        return None

    cleaned = key_text.strip()
    pattern = re.compile(r"^([A-Ga-g])([#b]?)(?:\s*(major|maj|minor|min|m)?)?$")
    match = pattern.match(cleaned)
    if not match:
        return None

    root = normalize_note(f"{match.group(1).upper()}{match.group(2) or ''}")
    if root not in NOTE_ORDER:
        return None
    suffix = (match.group(3) or "").lower()

    if suffix in {"minor", "min", "m"}:
        mode = "minor"
    else:
        mode = "major"
    return root, mode


def build_scale(root: str, mode: str) -> list[str]:
    if root not in NOTE_ORDER:
        raise ValueError(f"Unsupported key root: {root}")

    root_index = NOTE_ORDER.index(root)
    steps = MAJOR_STEPS if mode == "major" else MINOR_STEPS
    return [NOTE_ORDER[(root_index + step) % 12] for step in steps]


def chord_from_token(token: str, scale: list[str]) -> str:
    cleaned = token.replace("°", "").strip()
    upper = cleaned.upper()
    degree = ROMAN_TO_DEGREE.get(upper)
    if degree is None:
        raise ValueError(f"Unsupported progression token: {token}")

    root_note = scale[degree - 1]
    if token.endswith("°"):
        return f"{root_note}dim"
    if cleaned.isupper():
        return root_note
    return f"{root_note}m"


def progression_templates(mode: str, mood: str) -> dict[str, list[str]]:
    if mode == "major":
        if mood == "uplifting":
            return {
                "verse": ["I", "V", "vi", "IV"],
                "chorus": ["IV", "V", "I", "vi"],
                "bridge": ["ii", "IV", "I", "V"],
            }
        if mood == "hopeful":
            return {
                "verse": ["I", "vi", "IV", "V"],
                "chorus": ["I", "V", "IV", "V"],
                "bridge": ["vi", "IV", "I", "V"],
            }
        return {
            "verse": ["I", "IV", "ii", "V"],
            "chorus": ["IV", "I", "V", "vi"],
            "bridge": ["ii", "V", "I", "I"],
        }

    if mood == "melancholic":
        return {
            "verse": ["i", "VI", "III", "VII"],
            "chorus": ["VI", "VII", "i", "v"],
            "bridge": ["iv", "i", "VII", "III"],
        }
    return {
        "verse": ["i", "iv", "VI", "VII"],
        "chorus": ["III", "VII", "i", "VI"],
        "bridge": ["iv", "VII", "III", "VI"],
    }


def score_text_hints(lyrics_text: str, words: set[str]) -> int:
    lowered_words = set(re.findall(r"[a-zA-Z']+", lyrics_text.lower()))
    return len(lowered_words.intersection(words))


def fallback_sentiment(lyrics_text: str) -> tuple[str, float]:
    positive_hits = score_text_hints(lyrics_text, POSITIVE_HINTS)
    negative_hits = score_text_hints(lyrics_text, NEGATIVE_HINTS)

    if negative_hits > positive_hits:
        return "NEGATIVE", min(0.95, 0.55 + 0.1 * (negative_hits - positive_hits))
    return "POSITIVE", min(0.95, 0.55 + 0.1 * (positive_hits - negative_hits))


def detect_sentiment(lyrics_text: str, model_name: str) -> tuple[str, float]:
    classifier = get_sentiment_pipeline(model_name)
    if classifier is None:
        return fallback_sentiment(lyrics_text)

    output = classifier(lyrics_text[:1800], truncation=True)[0]
    label = str(output.get("label", "POSITIVE")).upper()
    score = float(output.get("score", 0.6))
    return label, score


def sentiment_to_mood(label: str, score: float, lyrics_text: str) -> str:
    energy_hits = score_text_hints(lyrics_text, ENERGY_HINTS)
    exclamation_hits = lyrics_text.count("!")

    if label.startswith("NEG"):
        return "melancholic" if score >= 0.8 else "reflective"

    if score >= 0.87 or energy_hits >= 2 or exclamation_hits >= 2:
        return "uplifting"
    return "hopeful"


def choose_default_key(mode: str, genre: str | None) -> str:
    genre_name = (genre or "").lower().replace("-", "").replace(" ", "")
    if mode == "minor":
        if "rock" in genre_name:
            return "E"
        if "rnb" in genre_name:
            return "F#"
        return "A"

    if "folk" in genre_name:
        return "G"
    if "rock" in genre_name:
        return "D"
    if "rnb" in genre_name:
        return "F"
    return "C"


def estimate_tempo(genre: str | None, mood: str, tempo_hint: int | None) -> int:
    if tempo_hint:
        return tempo_hint

    genre_name = (genre or "").lower().replace("-", "").replace(" ", "")
    base_tempo = 98
    for key, value in GENRE_TEMPO.items():
        if key in genre_name:
            base_tempo = value
            break

    if mood == "uplifting":
        return min(160, base_tempo + 8)
    if mood == "melancholic":
        return max(62, base_tempo - 10)
    return base_tempo


def estimate_time_signature(genre: str | None) -> str:
    genre_name = (genre or "").lower()
    if "waltz" in genre_name:
        return "3/4"
    if "folk" in genre_name or "ballad" in genre_name:
        return "6/8"
    return "4/4"


def chord_progression_for_key(root: str, mode: str, mood: str, line_count: int) -> dict[str, list[str]]:
    templates = progression_templates(mode, mood)
    scale = build_scale(root, mode)

    progression = {
        section: [chord_from_token(token, scale) for token in tokens]
        for section, tokens in templates.items()
    }

    if line_count < 8:
        progression.pop("bridge", None)

    return progression


def build_line_chords(lines: list[str], progression: dict[str, list[str]]) -> list[LineChord]:
    verse = progression.get("verse") or ["C", "G", "Am", "F"]
    chorus = progression.get("chorus") or verse

    line_chords: list[LineChord] = []
    split_idx = max(1, int(round(len(lines) * 0.6)))

    for idx, line in enumerate(lines, start=1):
        section_pattern = verse if idx <= split_idx else chorus
        cursor = (idx - 1) * 2
        first_chord = section_pattern[cursor % len(section_pattern)]
        second_chord = section_pattern[(cursor + 1) % len(section_pattern)]
        line_chords.append(
            LineChord(
                line_number=idx,
                lyric=line,
                chords=[first_chord, second_chord],
            )
        )

    return line_chords


def build_notes(mood: str, mode: str, line_count: int) -> str:
    style_note = "Use gentle dynamics in the verse and stronger accents in the chorus."
    if mood == "uplifting":
        style_note = "Keep strumming bright and add more rhythmic drive in the chorus."
    if mood == "melancholic":
        style_note = "Use softer voicings and let chords ring for emotional phrasing."

    ending_note = "Add a bridge variation before the final chorus." if line_count >= 8 else "Repeat chorus progression for outro."
    mode_note = "Major-key voicings keep the progression open." if mode == "major" else "Minor-key voicings support a reflective tone."
    return f"{style_note} {mode_note} {ending_note}"


def generate_chord_plan(
    request: SongRequest,
    *,
    model: str = DEFAULT_MODE,
    sentiment_model: str = DEFAULT_SENTIMENT_MODEL,
    mood_detector: MoodDetector | None = None,
) -> ChordPlan:
    _ = model
    lines, _ = prepare_lyrics_with_limits(request.lyrics)
    lyrics_text = "\n".join(lines)

    detector = mood_detector or detect_sentiment
    sentiment_label, sentiment_score = detector(lyrics_text, sentiment_model)
    mood = sentiment_to_mood(sentiment_label, sentiment_score, lyrics_text)

    key_data = parse_key_preference(request.key_preference)
    if key_data is None:
        mode = "major" if mood in {"uplifting", "hopeful"} else "minor"
        root = choose_default_key(mode, request.genre)
    else:
        root, mode = key_data

    key_name = f"{root} {mode}"
    tempo_bpm = estimate_tempo(request.genre, mood, request.tempo_hint)
    time_signature = estimate_time_signature(request.genre)
    progression = chord_progression_for_key(root, mode, mood, len(lines))
    line_chords = build_line_chords(lines, progression)
    notes = build_notes(mood, mode, len(lines))

    return ChordPlan(
        mood=mood,
        key=key_name,
        tempo_bpm=tempo_bpm,
        time_signature=time_signature,
        progression=progression,
        line_chords=line_chords,
        notes=notes,
    )
