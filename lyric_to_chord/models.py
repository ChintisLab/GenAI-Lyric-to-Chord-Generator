from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SongRequest(BaseModel):
    lyrics: str = Field(min_length=1)
    genre: Optional[str] = None
    key_preference: Optional[str] = None
    tempo_hint: Optional[int] = Field(default=None, ge=40, le=220)

    @field_validator("lyrics")
    @classmethod
    def lyrics_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Lyrics cannot be blank.")
        return stripped

    @field_validator("genre", "key_preference")
    @classmethod
    def optional_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class LineChord(BaseModel):
    line_number: int = Field(ge=1)
    lyric: str = Field(min_length=1)
    chords: list[str] = Field(min_length=1, max_length=6)

    @field_validator("lyric")
    @classmethod
    def lyric_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Lyric text cannot be blank.")
        return stripped

    @field_validator("chords")
    @classmethod
    def chords_not_empty(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        if not cleaned:
            raise ValueError("Each line should have at least one chord.")
        return cleaned


class ChordPlan(BaseModel):
    mood: str = Field(min_length=1)
    key: str = Field(min_length=1)
    tempo_bpm: int = Field(ge=40, le=240)
    time_signature: str = Field(min_length=1)
    progression: dict[str, list[str]] = Field(min_length=1)
    line_chords: list[LineChord] = Field(min_length=1)
    notes: str = Field(default="")

    @field_validator("progression")
    @classmethod
    def progression_has_data(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        cleaned: dict[str, list[str]] = {}
        for section, chords in value.items():
            section_name = section.strip()
            cleaned_chords = [chord.strip() for chord in chords if chord and chord.strip()]
            if section_name and cleaned_chords:
                cleaned[section_name] = cleaned_chords
        if not cleaned:
            raise ValueError("Progression must include at least one non-empty section.")
        return cleaned
