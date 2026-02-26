import pytest

from lyric_to_chord.preprocessing import prepare_lyrics, prepare_lyrics_with_limits


def test_prepare_lyrics_removes_blank_lines_and_normalizes_spaces() -> None:
    raw = "  hello    world  \n\nthis   is   a line\r\nanother line   "
    result = prepare_lyrics(raw)
    assert result == ["hello world", "this is a line", "another line"]


def test_prepare_lyrics_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        prepare_lyrics("   \n \r\n")


def test_prepare_lyrics_with_limits_marks_truncation() -> None:
    raw = "\n".join(["line"] * 10)
    lines, truncated = prepare_lyrics_with_limits(raw, max_lines=3)
    assert lines == ["line", "line", "line"]
    assert truncated is True
