

import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Digital Forensic Timeline", layout="wide")
st.title("Automated Framework for Digital Forensic Timeline Analysis")
st.caption(
    "Partial prototype: timestamp normalization, validation, "
    "temporal inconsistency checks, and chronological event view."
)

SAMPLE = Path(__file__).parent / "data" / "sample_events.csv"

uploaded = st.file_uploader("Upload forensic events (CSV)", type=["csv"])

try:
    df = pd.read_csv(uploaded) if uploaded else pd.read_csv(SAMPLE)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

required = {
    "event_id",
    "source_type",
    "event_description",
    "timestamp_original",
    "timezone",
}
missing = required - set(df.columns)

if missing:
    st.error("Missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

# Preserve original values and clean timestamp fields.
df["timestamp_original"] = (
    df["timestamp_original"].fillna("").astype(str).str.strip()
)
df["timezone"] = df["timezone"].fillna("").astype(str).str.strip()


def parse_with_offset(row):
    raw = row["timestamp_original"]
    tz = row["timezone"]

    if not raw or raw.lower() in {"nan", "none"}:
        return pd.NaT, "Missing timestamp"

    try:
        ts = pd.Timestamp(raw)
    except Exception:
        return pd.NaT, "Invalid timestamp"

    if not tz or tz.lower() in {"nan", "none", "unknown"}:
        return pd.NaT, "Timezone unknown"

    try:
        if ts.tzinfo is None:
            ts = ts.tz_localize(tz)
        else:
            ts = ts.tz_convert(tz)

        return ts.tz_convert("UTC"), "OK"

    except Exception:
        return pd.NaT, "Invalid/unsupported timezone"


parsed = df.apply(parse_with_offset, axis=1, result_type="expand")

df["timestamp_utc"] = parsed[0]
df["timestamp_status"] = parsed[1]

df["review_flag"] = df["timestamp_status"].map(
    lambda status: (
        "Needs review"
        if status != "OK"
        else "Parsed; not independently verified"
    )
)

# -----------------------------------------
# Rule-based temporal inconsistency detection
# -----------------------------------------

df["temporal_flag"] = "No rule-based conflict detected"
df["temporal_reason"] = ""

# Flag missing, invalid, or unknown timestamps.
for idx, row in df.iterrows():
    if row["timestamp_status"] != "OK":
        df.at[idx, "temporal_flag"] = "Needs review"
        df.at[idx, "temporal_reason"] = (
            f"Timestamp validation issue: {row['timestamp_status']}"
        )

# Check creation/access ordering for matching entities.
if "entity_key" in df.columns:
    df["_entity_check"] = (
        df["entity_key"].fillna("").astype(str).str.strip()
    )

    for entity, group in df[
        (df["_entity_check"] != "")
        & df["timestamp_utc"].notna()
    ].groupby("_entity_check"):

        descriptions = group["event_description"].fillna("").astype(str)

        creation_rows = group[
            descriptions.str.contains(
                r"\bcreat(?:e|ed|ion)\b",
                case=False,
                na=False,
                regex=True,
            )
        ]

        access_rows = group[
            descriptions.str.contains(
                r"\baccess(?:ed)?\b",
                case=False,
                na=False,
                regex=True,
            )
        ]

        if creation_rows.empty or access_rows.empty:
            continue

        earliest_creation = creation_rows["timestamp_utc"].min()

        for idx, row in access_rows.iterrows():
            if row["timestamp_utc"] < earliest_creation:
                df.at[idx, "temporal_flag"] = (
                    "Potential ordering conflict"
                )

                df.at[idx, "temporal_reason"] = (
                    "Access timestamp precedes the earliest recorded "
                    f"creation timestamp for entity '{entity}'. "
                    "Check source records and metadata conventions."
                )

                df.at[idx, "review_flag"] = (
                    "Needs review: temporal conflict"
                )

    df.drop(columns=["_entity_check"], inplace=True)

# -----------------------------------------
# Summary metrics
# -----------------------------------------

conflict_count = int(
    (df["temporal_flag"] == "Potential ordering conflict").sum()
)

needs_review_count = int(
    (df["temporal_flag"] == "Needs review").sum()
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Events loaded", len(df))

c2.metric(
    "Validly parsed timestamps",
    int(df["timestamp_utc"].notna().sum()),
)

c3.metric("Events needing review", needs_review_count)

c4.metric("Potential ordering conflicts", conflict_count)

# -----------------------------------------
# Event records and validation
# -----------------------------------------

st.subheader("Event records and validation")

show = df.copy()
show["timestamp_utc"] = (
    show["timestamp_utc"].astype(str).replace("NaT", "")
)

st.dataframe(
    show,
    use_container_width=True,
    hide_index=True,
)

# -----------------------------------------
# Chronological timeline
# -----------------------------------------

valid = df[df["timestamp_utc"].notna()].sort_values(
    "timestamp_utc"
)

if not valid.empty:
    st.subheader("Chronological timeline (valid timestamps only)")

    hover_columns = [
        col
        for col in [
            "event_id",
            "event_description",
            "entity_key",
            "temporal_flag",
            "temporal_reason",
        ]
        if col in valid.columns
    ]

    fig = px.scatter(
        valid,
        x="timestamp_utc",
        y="source_type",
        hover_data=hover_columns,
        title="Events ordered by normalized UTC time",
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No valid timestamps to display yet.")

# -----------------------------------------
# Records flagged for review
# -----------------------------------------

st.subheader("Events flagged for review")

flagged = df[
    df["temporal_flag"] != "No rule-based conflict detected"
].copy()

if flagged.empty:
    st.info("No records were flagged by the current rules.")
else:
    flagged["timestamp_utc"] = (
        flagged["timestamp_utc"].astype(str).replace("NaT", "")
    )

    st.dataframe(
        flagged,
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------------------
# Limitations and explanation
# -----------------------------------------

st.warning(
    "Important limitation: this prototype checks timestamp parsing "
    "and a narrow creation/access ordering rule. It does not prove "
    "timestamp tampering or independently verify system clocks. "
    "Copying files, synchronization, and metadata conventions can "
    "also explain unusual event ordering."
)

st.subheader("How to explain the output")

st.markdown(
    "- **OK:** The timestamp was parsed and converted using the "
    "provided timezone. This does not prove authenticity.\n"
    "- **Missing/Invalid timestamp:** The record is preserved and "
    "flagged for review.\n"
    "- **Potential ordering conflict:** An access event appears "
    "earlier than the earliest recorded creation event for the "
    "same entity. Investigate the source records before concluding.\n"
    "- **Traceability:** Original timestamps and source fields "
    "remain visible for comparison."
)
