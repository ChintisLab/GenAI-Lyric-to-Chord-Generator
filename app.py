from __future__ import annotations

import json
import os

import streamlit as st
from dotenv import load_dotenv

from lyric_to_chord.generator import DEFAULT_MODE, DEFAULT_SENTIMENT_MODEL, generate_chord_plan
from lyric_to_chord.models import ChordPlan, SongRequest
from lyric_to_chord.preprocessing import MAX_INPUT_CHARS, MAX_INPUT_LINES, prepare_lyrics_with_limits

load_dotenv()

SAMPLE_LYRICS = """I walked through the midnight city lights
Trying to make peace with my restless mind
Every broken memory starts to fade
When the morning sun calls out my name"""


def get_sentiment_model_name() -> str:
    try:
        secret_value = st.secrets.get("HF_SENTIMENT_MODEL")
    except Exception:
        secret_value = None
    return secret_value or os.getenv("HF_SENTIMENT_MODEL", DEFAULT_SENTIMENT_MODEL)


def render_progression(plan: ChordPlan) -> None:
    st.subheader("Section Progression")
    for section, chords in plan.progression.items():
        st.markdown(f"**{section.title()}**: {' - '.join(chords)}")


def render_line_chords(plan: ChordPlan) -> None:
    st.subheader("Line by Line Chords")
    for item in plan.line_chords:
        chord_text = " - ".join(item.chords)
        st.markdown(f"**{item.line_number}. [{chord_text}]** {item.lyric}")


def render_chorded_text(plan: ChordPlan) -> str:
    rendered_lines = []
    for item in plan.line_chords:
        chord_text = " - ".join(item.chords)
        rendered_lines.append(f"[{chord_text}] {item.lyric}")
    return "\n".join(rendered_lines)


def main() -> None:
    st.set_page_config(page_title="Lyric-to-Chord Generator", page_icon="🎵", layout="wide")

    st.title("GenAI Lyric-to-Chord Generator")
    st.caption("Paste lyrics, generate chord suggestions with free local models, and export structured JSON.")

    if "lyrics_input" not in st.session_state:
        st.session_state["lyrics_input"] = ""

    with st.sidebar:
        st.header("Song Controls")
        genre = st.text_input("Genre (optional)", value="Pop")
        key_preference = st.text_input("Key preference (optional)", value="")
        tempo_enabled = st.toggle("Use tempo hint", value=False)
        tempo_hint = st.number_input("Tempo (BPM)", min_value=40, max_value=220, value=100, disabled=not tempo_enabled)
        sentiment_model = st.text_input(
            "Sentiment model",
            value=get_sentiment_model_name(),
            help="Default uses DistilBERT from Hugging Face.",
        )
        if st.button("Use sample lyrics"):
            st.session_state["lyrics_input"] = SAMPLE_LYRICS

    lyrics = st.text_area(
        "Lyrics",
        key="lyrics_input",
        height=260,
        placeholder="Paste your song lyrics here...",
    )

    generate_clicked = st.button("Generate Chords", type="primary")

    if generate_clicked:
        try:
            prepared_lines, was_truncated = prepare_lyrics_with_limits(lyrics)
            if was_truncated:
                st.warning(
                    f"I trimmed the lyrics to fit limits ({MAX_INPUT_CHARS} chars / {MAX_INPUT_LINES} lines)."
                )

            request = SongRequest(
                lyrics="\n".join(prepared_lines),
                genre=genre,
                key_preference=key_preference,
                tempo_hint=int(tempo_hint) if tempo_enabled else None,
            )
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

        st.info("First run may take a little longer while the free model downloads.")

        with st.spinner("Generating chord plan..."):
            try:
                chord_plan = generate_chord_plan(
                    request,
                    model=DEFAULT_MODE,
                    sentiment_model=sentiment_model,
                )
            except Exception as exc:
                st.error(f"Generation failed: {exc}")
                st.stop()

        st.session_state["latest_plan"] = chord_plan.model_dump()

    latest_plan_payload = st.session_state.get("latest_plan")
    if latest_plan_payload:
        plan = ChordPlan.model_validate(latest_plan_payload)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mood", plan.mood)
        col2.metric("Key", plan.key)
        col3.metric("Tempo", f"{plan.tempo_bpm} BPM")
        col4.metric("Time", plan.time_signature)

        render_progression(plan)
        render_line_chords(plan)

        st.subheader("Arrangement Notes")
        st.write(plan.notes or "No extra notes.")

        json_data = json.dumps(plan.model_dump(), indent=2)
        chorded_text = render_chorded_text(plan)

        st.download_button(
            "Download JSON",
            data=json_data,
            file_name="chord_plan.json",
            mime="application/json",
        )
        st.download_button(
            "Download Chorded Text",
            data=chorded_text,
            file_name="chorded_lyrics.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
