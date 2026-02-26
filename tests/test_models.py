import pytest
from pydantic import ValidationError

from lyric_to_chord.models import ChordPlan, SongRequest


def test_song_request_strips_optional_fields() -> None:
    request = SongRequest(
        lyrics="hello",
        genre="  pop  ",
        key_preference="   ",
        tempo_hint=100,
    )
    assert request.genre == "pop"
    assert request.key_preference is None


def test_chord_plan_requires_progression_data() -> None:
    payload = {
        "mood": "calm",
        "key": "C",
        "tempo_bpm": 90,
        "time_signature": "4/4",
        "progression": {},
        "line_chords": [{"line_number": 1, "lyric": "hello", "chords": ["C"]}],
        "notes": "simple voicings",
    }
    with pytest.raises(ValidationError):
        ChordPlan.model_validate(payload)
