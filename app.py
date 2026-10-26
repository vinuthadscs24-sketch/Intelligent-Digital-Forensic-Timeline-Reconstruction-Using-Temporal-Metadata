import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Digital Forensic Timeline", layout="wide")
st.title("Automated Framework for Digital Forensic Timeline Analysis")
st.caption("Partial prototype: timestamp normalization, validation flags, and chronological event view.")

SAMPLE = Path(__file__).parent / "data" / "sample_events.csv"

uploaded = st.file_uploader("Upload forensic events (CSV)", type=["csv"])
try:
    df = pd.read_csv(uploaded) if uploaded else pd.read_csv(SAMPLE)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

required = {"event_id", "source_type", "event_description", "timestamp_original", "timezone"}
missing = required - set(df.columns)
if missing:
    st.error("Missing required columns: " + ", ".join(sorted(missing)))
    st.stop()

df["timestamp_original"] = df["timestamp_original"].fillna("").astype(str).str.strip()
df["timezone"] = df["timezone"].fillna("").astype(str).str.strip()

# Parse ISO-like timestamps. Convert known offsets to UTC; unknown timezones are not guessed.
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
        # A supplied offset such as +05:30 is applied to a naive timestamp.
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
    lambda x: "Needs review" if x != "OK" else "Parsed; not independently verified"
)

c1, c2, c3 = st.columns(3)
c1.metric("Events loaded", len(df))
c2.metric("Validly parsed timestamps", int(df["timestamp_utc"].notna().sum()))
c3.metric("Events needing review", int((df["timestamp_status"] != "OK").sum()))

st.subheader("Event records and validation")
show = df.copy()
show["timestamp_utc"] = show["timestamp_utc"].astype(str).replace("NaT", "")
st.dataframe(show, use_container_width=True, hide_index=True)

valid = df[df["timestamp_utc"].notna()].sort_values("timestamp_utc")
if not valid.empty:
    st.subheader("Chronological timeline (valid timestamps only)")
    fig = px.scatter(
        valid,
        x="timestamp_utc",
        y="source_type",
        hover_data=["event_id", "event_description", "entity_key"],
        title="Events ordered by normalized UTC time"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No valid timestamps to display yet.")

st.warning(
    "Important limitation: this prototype checks parsing and timezone conversion only. "
    "It does not prove that a clock was correct or detect all timestamp tampering. "
    "Clock discrepancy detection requires a trusted reference/time anchor."
)
st.subheader("How to explain the output")
st.markdown(
    "- **OK** means the timestamp could be parsed and converted using the provided timezone; it does not prove authenticity.\n"
    "- **Missing/Invalid timestamp** records are preserved and excluded from the plotted chronology.\n"
    "- Original timestamps and source fields remain visible for traceability."
)
