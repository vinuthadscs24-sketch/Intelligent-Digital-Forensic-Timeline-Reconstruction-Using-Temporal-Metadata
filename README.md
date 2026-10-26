# Digital Forensic Timeline Analysis — Partial Prototype

## What it demonstrates
- Loads a sample CSV or a user's CSV.
- Parses timestamps and applies the supplied timezone offset.
- Converts parseable timestamps to UTC while preserving original values.
- Flags missing, invalid, or unknown timezone values.
- Displays a table and a simple chronological plot.

## Run on Windows
1. Install Python 3.10+ if it is not already installed.
2. Extract this ZIP.
3. Open Command Prompt in the extracted folder.
4. Run:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. Open the local URL shown in the terminal (usually http://localhost:8501).

If `py` does not work, try `python` instead.

## CSV columns required
event_id, source_type, event_description, timestamp_original, timezone
Optional useful columns: entity_key, notes

Timezone examples: +05:30, +00:00, -04:00. Use `unknown` when the timezone is genuinely unknown; do not guess it.

## Honest project limitations
This is a partial implementation, not a complete forensic tool. Parsing a timestamp does not establish that it is accurate. True clock-offset detection needs a trusted time anchor or reference event. Cross-artifact correlation, event dependency graphs, tamper detection, and formal evaluation are future modules.
