from lyric_to_chord.generator import generate_chord_plan, parse_key_preference
from lyric_to_chord.models import SongRequest


def positive_detector(_lyrics: str, _model: str) -> tuple[str, float]:
    return "POSITIVE", 0.93


def negative_detector(_lyrics: str, _model: str) -> tuple[str, float]:
    return "NEGATIVE", 0.9


def test_generate_chord_plan_builds_line_level_output() -> None:
    request = SongRequest(
        lyrics="hello world\nsunlight comes\nwe keep moving\ninto the dawn",
        genre="Pop",
    )
    plan = generate_chord_plan(request, mood_detector=positive_detector)

    assert plan.mood == "uplifting"
    assert plan.key.endswith("major")
    assert len(plan.line_chords) == 4
    assert plan.line_chords[0].line_number == 1
    assert len(plan.line_chords[0].chords) == 2


def test_generate_chord_plan_respects_key_and_tempo_hints() -> None:
    request = SongRequest(
        lyrics="night falls\nstreets are quiet",
        key_preference="Dm",
        tempo_hint=72,
        genre="Ballad",
    )
    plan = generate_chord_plan(request, mood_detector=negative_detector)

    assert plan.key == "D minor"
    assert plan.tempo_bpm == 72


def test_parse_key_preference_supports_shorthand() -> None:
    assert parse_key_preference("Am") == ("A", "minor")
    assert parse_key_preference("F# major") == ("F#", "major")
    assert parse_key_preference("Bb min") == ("A#", "minor")
