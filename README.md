# GenAI Lyric-to-Chord Generator

## Description
This project converts raw song lyrics into structured chord suggestions in a Streamlit web app.
It is designed to help songwriters quickly move from words to a playable harmonic sketch.
The app uses a free sentiment model (DistilBERT) to estimate song mood and then applies music-theory rules to build progressions and line-level chord recommendations.
Outputs can be exported as JSON and plain text for reuse in other tools.

## Features
- Paste lyrics and generate chord suggestions in one click
- Mood classification using a free Hugging Face DistilBERT model
- Song-level output: mood, key, tempo, and time signature
- Section-level progression (verse, chorus, bridge when available)
- Line-by-line chords aligned with each lyric line
- Download output as JSON or chorded text
- Input validation and truncation guardrails

## Tech Stack
- Python 3.11+
- Streamlit
- Hugging Face Transformers (DistilBERT sentiment model)
- PyTorch
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
5. (Optional) Add environment config:
```bash
cp .env.example .env
```

## Usage
Run the app:
```bash
streamlit run app.py
```

Run tests:
```bash
pytest
```

Notes:
- No paid API key is required.
- On first run, the sentiment model downloads automatically and may take extra time.

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
  "mood": "uplifting",
  "key": "C major",
  "tempo_bpm": 112,
  "time_signature": "4/4",
  "progression": {
    "verse": ["C", "G", "Am", "F"],
    "chorus": ["F", "G", "C", "Am"]
  },
  "line_chords": [
    {"line_number": 1, "lyric": "I walked through the midnight city lights", "chords": ["C", "G"]},
    {"line_number": 2, "lyric": "Trying to make peace with my restless mind", "chords": ["Am", "F"]}
  ],
  "notes": "Keep strumming bright and add more rhythmic drive in the chorus."
}
```

### UI Screenshot
Add your latest Streamlit app screenshot here.

## Future Improvements
- Add lead-sheet PDF or MusicXML export
- Add chord difficulty modes (beginner, intermediate, advanced)
- Add section tagging in UI (verse, pre-chorus, chorus, bridge)
- Add support for alternate tunings and capo suggestions
- Add save/load project history

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss the update.

## License
No license file is currently included. Add a `LICENSE` file before public distribution.
