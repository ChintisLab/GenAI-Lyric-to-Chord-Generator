from types import SimpleNamespace

import pytest

from lyric_to_chord.generator import generate_chord_plan
from lyric_to_chord.models import SongRequest


def make_response(content: str) -> SimpleNamespace:
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


class DummyCompletions:
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.calls = 0

    def create(self, **kwargs):  # noqa: ANN003
        index = min(self.calls, len(self.outputs) - 1)
        output = self.outputs[index]
        self.calls += 1
        return make_response(output)


class DummyClient:
    def __init__(self, outputs: list[str]):
        completions = DummyCompletions(outputs)
        self.chat = SimpleNamespace(completions=completions)
        self.completions = completions


VALID_JSON = """
{
  "mood": "hopeful",
  "key": "C major",
  "tempo_bpm": 96,
  "time_signature": "4/4",
  "progression": {
    "verse": ["C", "G", "Am", "F"],
    "chorus": ["F", "G", "C", "Am"]
  },
  "line_chords": [
    {"line_number": 1, "lyric": "hello world", "chords": ["C", "G"]},
    {"line_number": 2, "lyric": "sunlight comes", "chords": ["Am", "F"]}
  ],
  "notes": "Keep strumming simple."
}
""".strip()


def test_generate_chord_plan_success() -> None:
    client = DummyClient([VALID_JSON])
    request = SongRequest(lyrics="hello world\nsunlight comes")

    plan = generate_chord_plan(
        request,
        api_key="test-key",
        client=client,  # type: ignore[arg-type]
    )

    assert plan.mood == "hopeful"
    assert len(plan.line_chords) == 2
    assert client.completions.calls == 1


def test_generate_chord_plan_retries_after_invalid_json() -> None:
    invalid = "not-json"
    client = DummyClient([invalid, VALID_JSON])
    request = SongRequest(lyrics="hello world\nsunlight comes")

    plan = generate_chord_plan(
        request,
        api_key="test-key",
        client=client,  # type: ignore[arg-type]
        max_retries=1,
    )

    assert plan.key == "C major"
    assert client.completions.calls == 2


def test_generate_chord_plan_raises_when_alignment_is_wrong() -> None:
    bad_alignment_json = """
    {
      "mood": "hopeful",
      "key": "C major",
      "tempo_bpm": 96,
      "time_signature": "4/4",
      "progression": {"verse": ["C", "G", "Am", "F"]},
      "line_chords": [
        {"line_number": 1, "lyric": "hello world", "chords": ["C", "G"]}
      ],
      "notes": "Simple arrangement."
    }
    """.strip()
    client = DummyClient([bad_alignment_json])
    request = SongRequest(lyrics="hello world\nsunlight comes")

    with pytest.raises(ValueError):
        generate_chord_plan(
            request,
            api_key="test-key",
            client=client,  # type: ignore[arg-type]
            max_retries=0,
        )
