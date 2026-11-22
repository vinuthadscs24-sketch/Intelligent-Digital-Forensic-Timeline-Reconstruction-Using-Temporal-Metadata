# Digital Forensic Timeline Analysis — Project Context

## 1. Project Overview

**Project Title:** Automated Framework for Digital Forensic Timeline Analysis

This project is a Python-based digital forensics prototype that processes forensic event records, validates timestamps, detects potential temporal inconsistencies, and displays events in chronological order through an interactive Streamlit dashboard.

The goal is to help investigators identify records that require further examination. Flags indicate potential issues and must not be treated as proof of malicious activity or tampering.

## 2. Technology Stack

- Python
- Streamlit — interactive dashboard
- Pandas — data processing and timestamp handling
- Plotly — interactive timeline visualization
- Pytest — automated testing

## 3. Project Structure

```text
project-root/
├── app.py
├── timestamp_validation.py
├── temporal_analysis.py
├── context.md
├── README.md
├── requirements.txt
├── data/
│   ├── sample_events.csv
│   └── ground_truth.csv
└── tests/
    └── test_temporal_analysis.py
```

The test file may need to be created if it does not already exist.

## 4. Main Files

### `app.py`

The main Streamlit application. It:
- Loads uploaded CSV files or the default sample dataset.
- Checks that required columns exist.
- Validates and normalizes timestamps.
- Detects potential temporal inconsistencies.
- Highlights events that require review.
- Displays summary metrics and flagged events.
- Shows events on an interactive chronological timeline.
- Provides a chronological event list and review queue.

### `timestamp_validation.py`

Responsible for validating timestamps and producing:
- `timestamp_utc`
- `timestamp_status`

Expected timestamp statuses include:
- `OK`
- `Missing timestamp`
- `Invalid timestamp`
- `Timezone unknown`
- `Invalid/unsupported timezone`

Unknown or invalid timezones must not be silently guessed.

### `temporal_analysis.py`

Responsible for detecting potential temporal inconsistencies, including:
- Access events occurring before the earliest recorded creation event for the same entity.
- Records that match on source type, event description, timestamp, and entity key.

Duplicate detection must label records as **duplicate candidates**, not confirmed duplicates.

### `data/sample_events.csv`

Contains 20 synthetic forensic events, E001–E020. The dataset includes normal events, timestamp validation issues, an ordering-conflict test, unusual-hour examples, and a repeated event.

### `data/ground_truth.csv`

Contains expected labels and explanations for the synthetic events. It is intended for testing and evaluating detection logic, not as input to the production detection process.

## 5. CSV Input Format

The required columns are:

| Column | Purpose |
|---|---|
| `event_id` | Unique event identifier |
| `source_type` | Source category, such as System, Browser, or File |
| `event_description` | Description of the recorded activity |
| `timestamp_original` | Original timestamp string |
| `timezone` | Timezone or UTC offset associated with the timestamp |

Optional columns include:
- `entity_key` — identifies the file, user, device, or other entity associated with an event.
- `notes` — additional record information.

The application must clearly report missing required columns and avoid crashing on invalid CSV input.

## 6. Important Sample Events

- **E012:** Invalid timestamp (`not-a-time`).
- **E013:** Missing timestamp.
- **E014:** Unknown timezone (`UNKNOWN`).
- **E015:** Synthetic file creation event at 10:00.
- **E016:** Synthetic file access event at 09:55 for the same file.

E016 should be identified as the **primary potential ordering conflict** because its access timestamp precedes the recorded creation timestamp.

E015 may be highlighted as a **related event** to make the ordering inconsistency easier to understand.

E005 and E019 represent matching browser events and may be marked as duplicate candidates. A matching record does not automatically mean that the event is duplicated or fraudulent.

E017 and E018 occur at unusual hours. Unusual timing alone must not be interpreted as evidence of wrongdoing.

## 7. Review Highlighting

The dashboard should visually distinguish:
- Timestamp validation issues.
- Primary ordering conflicts.
- Related events involved in an ordering conflict.
- Duplicate candidates.
- Events with no detected rule-based issue.

The review queue should make important events easy to locate.

The intended ordering-conflict presentation is:
- E016 — primary conflict.
- E015 — related creation event.

Timestamp issues for E012, E013, and E014 should remain visible.

## 8. Chronological Timeline Requirements

The timeline should:
- Convert valid timestamps to UTC for consistent comparison.
- Sort valid events chronologically from earliest to latest.
- Display event IDs and descriptions clearly.
- Use colors to distinguish review categories.
- Keep invalid or missing timestamps visible in a separate review section rather than assigning fabricated times.
- Explain that timestamp normalization does not independently verify the authenticity of source records.

## 9. Technical Constraints

When modifying the project:

1. Keep the existing project structure unless a change is necessary.
2. Do not invent CSV columns or API request/response fields.
3. Do not silently guess unknown timezones.
4. Do not use ground-truth labels to determine production flags.
5. Do not describe potential conflicts as confirmed tampering.
6. Preserve the original timestamps for reference.
7. Avoid unnecessary changes to working functionality.
8. Provide complete, copyable code when replacing a file.
9. Explain any required installation or run commands clearly.
10. Keep the implementation beginner-friendly.

## 10. Installation and Execution

Install dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

Run automated tests if the tests have been implemented:

```bash
python -m pytest -q
```

## 11. Current Project Status

The Streamlit dashboard has been run successfully. The current development focus is improving review highlighting, making the chronological representation clearer, and ensuring that E016 is the primary ordering conflict while E015 is shown as its related event.

Future work may include:
- Automated evaluation against `ground_truth.csv`.
- Better timeline filtering and sorting.
- Improved timestamp validation and timezone handling.
- Unit tests for timestamp and temporal analysis functions.
- Potential FastAPI integration in a later phase.

Any future enhancements should preserve the project's existing behavior unless a specific change is requested.
