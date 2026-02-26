# GenAI Lyric-to-Chord Generator

## Description
GenAI Lyric-to-Chord Generator is a web app that converts raw song lyrics into practical chord suggestions.
It helps songwriters and learners quickly get a playable harmonic structure instead of manually mapping chords line by line.
The app analyzes lyrical context, proposes a song-level progression, and returns line-wise chord guidance.
It also supports structured JSON export for reuse in other music workflows.

## Features
- Paste lyrics and generate chord suggestions in one click
- Song-level output: mood, key, tempo, and time signature
- Section-level chord progression (verse, chorus, bridge when available)
- Line-by-line chord suggestions aligned with lyrics
- Download outputs as JSON and plain text
- Input validation, truncation guardrails, and error handling

## Tech Stack
- Python 3.11+
- Streamlit
- OpenAI API
- Pydantic
- Pytest
- python-dotenv

## Installation
1. Clone the repository:
```bash
git clone https://github.com/<your-username>/GenAI-Lyric-to-Chord-Generator.git
```
2. Move into the project directory:
```bash
cd GenAI-Lyric-to-Chord-Generator
```
3. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```
4. Install dependencies:
```bash
pip install -r requirements.txt
```
5. Configure environment variables:
```bash
cp .env.example .env
```
Then set `OPENAI_API_KEY` in `.env`.

## Usage
Run the Streamlit app:
```bash
streamlit run app.py
```

Run tests:
```bash
pytest
```

## Project Structure
```text
GenAI-Lyric-to-Chord-Generator/
├── app.py
├── lyric_to_chord/
│   ├── __init__.py
│   ├── generator.py
│   ├── models.py
│   └── preprocessing.py
├── tests/
│   ├── test_generator.py
│   ├── test_models.py
│   └── test_preprocessing.py
├── .streamlit/
│   └── secrets.toml.example
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Example Output / Screenshots
### Sample JSON Output
```json
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
    {"line_number": 1, "lyric": "I walked through the midnight city lights", "chords": ["C", "G"]},
    {"line_number": 2, "lyric": "Trying to make peace with my restless mind", "chords": ["Am", "F"]}
  ],
  "notes": "Use light down-up strumming in verse and fuller voicings in chorus."
}
```

### UI Screenshot

## Future Improvements
- Add PDF or MusicXML lead-sheet export
- Add genre-specific chord style presets
- Add optional chord complexity controls (beginner/intermediate/advanced)
- Add song section tagging in the UI
- Add history and saved project support

## Contributing
Contributions are welcome. For major changes, please open an issue first to discuss the proposed update.
