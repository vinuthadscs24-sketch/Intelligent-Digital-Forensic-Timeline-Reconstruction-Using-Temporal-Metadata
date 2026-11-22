
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

from timestamp_validation import validate_timestamps
from temporal_analysis import detect_temporal_conflicts

st.set_page_config(
    page_title="Digital Forensic Timeline",
    layout="wide",
)

st.title("Digital Forensic Timeline Analyzer")
st.caption(
    "Timestamp validation • Temporal analysis • "
    "Evidence review • Chronological reconstruction"
)

SAMPLE = Path(__file__).parent / "data" / "sample_events.csv"

uploaded = st.file_uploader(
    "Upload forensic events (CSV)",
    type=["csv"],
)

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

df["timestamp_original"] = (
    df["timestamp_original"].fillna("").astype(str).str.strip()
)
df["timezone"] = df["timezone"].fillna("").astype(str).str.strip()

# -----------------------------------------
# 1. Validate timestamps
# -----------------------------------------

try:
    df = validate_timestamps(df)
except Exception as e:
    st.error(f"Timestamp validation failed: {e}")
    st.stop()

# -----------------------------------------
# 2. Detect temporal conflicts
# -----------------------------------------

try:
    df = detect_temporal_conflicts(df)
except Exception as e:
    st.error(f"Temporal analysis failed: {e}")
    st.stop()

if "temporal_flag" not in df.columns:
    df["temporal_flag"] = "No conflict detected"

if "temporal_reason" not in df.columns:
    df["temporal_reason"] = ""

if "timezone_check" not in df.columns:
    df["timezone_check"] = ""

# -----------------------------------------
# 3. Highlight BOTH events in an ordering pair
# -----------------------------------------

# The initial rule flags the access event that precedes creation.
# Also mark the corresponding later creation event for review.
if "entity_key" in df.columns:
    for idx, row in df[
        df["temporal_flag"] == "Potential ordering conflict"
    ].iterrows():

        entity = row["entity_key"]
        access_time = row["timestamp_utc"]

        if pd.isna(access_time):
            continue

        descriptions = df["event_description"].fillna("").astype(str)

        creation_mask = (
            (df["entity_key"] == entity)
            & descriptions.str.contains(
                r"\bcreat(?:e|ed|ion)\b",
                case=False,
                regex=True,
            )
            & df["timestamp_utc"].notna()
            & (df["timestamp_utc"] > access_time)
        )

        for creation_idx in df.index[creation_mask]:
            if df.at[creation_idx, "temporal_flag"] == "No conflict detected":
                df.at[creation_idx, "temporal_flag"] = (
                    "Related ordering conflict"
                )
                df.at[creation_idx, "temporal_reason"] = (
                    "This creation event occurs after an access event "
                    "for the same entity that was flagged for review. "
                    "Review both source records."
                )

# -----------------------------------------
# 4. Assign review categories
# -----------------------------------------

df["review_category"] = "Normal — parsed, not verified"

timestamp_issues = df["timestamp_status"] != "OK"

df.loc[timestamp_issues, "review_category"] = (
    "Timestamp issue"
)

df.loc[
    df["temporal_flag"] == "Potential ordering conflict",
    "review_category",
] = "Ordering conflict"

df.loc[
    df["temporal_flag"] == "Related ordering conflict",
    "review_category",
] = "Related event — review"

df.loc[
    df["temporal_flag"] == "Duplicate candidate",
    "review_category",
] = "Duplicate candidate"

df["requires_review"] = (
    timestamp_issues
    | df["temporal_flag"].isin([
        "Potential ordering conflict",
        "Related ordering conflict",
        "Duplicate candidate",
    ])
)

# -----------------------------------------
# 5. Summary metrics
# -----------------------------------------

review_count = int(df["requires_review"].sum())
valid_count = int(df["timestamp_utc"].notna().sum())

ordering_count = int(
    (df["temporal_flag"] == "Potential ordering conflict").sum()
)

related_count = int(
    (df["temporal_flag"] == "Related ordering conflict").sum()
)

duplicate_count = int(
    (df["temporal_flag"] == "Duplicate candidate").sum()
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total events", len(df))
c2.metric("Parsed timestamps", valid_count)
c3.metric("Events requiring review", review_count)
c4.metric("Ordering conflicts", ordering_count + related_count)

st.caption(
    f"Timestamp issues: {int(timestamp_issues.sum())} · "
    f"Ordering pairs: {ordering_count} primary, "
    f"{related_count} related · "
    f"Duplicate candidates: {duplicate_count}"
)

# -----------------------------------------
# 6. Styling for review tables
# -----------------------------------------

def highlight_review(row):
    category = row["review_category"]

    if category == "Timestamp issue":
        style = (
            "background-color: #FCE4E4; color: #8B1E1E;"
        )
    elif category == "Ordering conflict":
        style = (
            "background-color: #FFD8B2; color: #713900;"
        )
    elif category == "Related event — review":
        style = (
            "background-color: #FFF0C2; color: #704D00;"
        )
    elif category == "Duplicate candidate":
        style = (
            "background-color: #E8DDFC; color: #492580;"
        )
    else:
        style = ""

    return [style] * len(row)


# -----------------------------------------
# 7. All event records
# -----------------------------------------

st.subheader("Event Records")

st.markdown(
    """
    <span style="background:#FCE4E4;padding:4px 8px;border-radius:4px;">
    Timestamp issue
    </span>
    &nbsp;
    <span style="background:#FFD8B2;padding:4px 8px;border-radius:4px;">
    Ordering conflict
    </span>
    &nbsp;
    <span style="background:#FFF0C2;padding:4px 8px;border-radius:4px;">
    Related event
    </span>
    &nbsp;
    <span style="background:#E8DDFC;padding:4px 8px;border-radius:4px;">
    Duplicate candidate
    </span>
    """,
    unsafe_allow_html=True,
)

display_df = df.copy()
display_df["timestamp_utc"] = display_df["timestamp_utc"].astype(str)

st.dataframe(
    display_df.style.apply(highlight_review, axis=1),
    use_container_width=True,
    hide_index=True,
)

# -----------------------------------------
# 8. Chronological event timeline
# -----------------------------------------

st.subheader("Chronological Event Timeline")

valid = (
    df[df["timestamp_utc"].notna()]
    .sort_values("timestamp_utc")
    .copy()
)

if not valid.empty:
    # Each event receives its own row. Time progresses left to right.
    valid["timeline_label"] = (
        valid["event_id"].astype(str)
        + " · "
        + valid["event_description"].fillna("").astype(str)
    )

    ordered_labels = valid["timeline_label"].tolist()

    fig = px.scatter(
        valid,
        x="timestamp_utc",
        y="timeline_label",
        color="review_category",
        category_orders={"timeline_label": ordered_labels},
        hover_data=[
            col for col in [
                "event_id",
                "event_description",
                "source_type",
                "timestamp_original",
                "timezone",
                "timestamp_status",
                "temporal_reason",
            ]
            if col in valid.columns
        ],
        title="Investigation timeline — chronological order",
        labels={
            "timestamp_utc": "Normalized time (UTC)",
            "timeline_label": "Event",
            "review_category": "Review status",
        },
    )

    fig.update_traces(
        marker=dict(size=12, line=dict(width=1, color="white"))
    )

    fig.update_layout(
        height=max(450, len(valid) * 30),
        yaxis_title="Events (earliest to latest)",
        xaxis_title="Time (UTC)",
        legend_title="Review status",
        hovermode="closest",
        margin=dict(l=20, r=20, t=60, b=30),
    )

    # Earliest event at the top; latest at the bottom.
    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Each point represents one event. Horizontal position shows "
        "normalized UTC time; colors indicate review status. "
        "A flagged event is an investigative lead, not proof of tampering."
    )

    st.subheader("Chronological Event List")

    chronological = valid.copy()
    chronological["timestamp_utc"] = (
        chronological["timestamp_utc"].astype(str)
    )

    columns = [
        col for col in [
            "timestamp_utc",
            "event_id",
            "source_type",
            "event_description",
            "review_category",
            "temporal_reason",
        ]
        if col in chronological.columns
    ]

    st.dataframe(
        chronological[columns].style.apply(highlight_review, axis=1),
        use_container_width=True,
        hide_index=True,
    )

else:
    st.info("No valid timestamps are available for the timeline.")

# -----------------------------------------
# 9. Dedicated review queue
# -----------------------------------------

st.subheader("⚠️ Events Requiring Review")

flagged = df[df["requires_review"]].copy()

if flagged.empty:
    st.success("No events were flagged by the current rules.")
else:
    st.warning(
        f"{len(flagged)} event(s) require examination. "
        "These findings are not proof of malicious activity."
    )

    flagged["timestamp_utc"] = flagged["timestamp_utc"].astype(str)

    st.dataframe(
        flagged.style.apply(highlight_review, axis=1),
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------------------
# 10. Interpretation and limitations
# -----------------------------------------

with st.expander("How to interpret the findings"):
    st.markdown(
        """
        - **Timestamp issue:** Missing, invalid, unknown, or inconsistent
          timestamp information requires examination.
        - **Ordering conflict:** An access event precedes the earliest
          recorded creation event for the same entity.
        - **Related event:** The corresponding creation event is also
          highlighted to help examine the full event pair.
        - **Duplicate candidate:** Matching fields suggest that records
          should be compared against their original sources.
        - **Normal — parsed, not verified:** Parsing succeeded, but
          authenticity and clock accuracy have not been established.
        """
    )

st.warning(
    "This is a rule-based prototype. It does not prove timestamp "
    "tampering or independently verify system clocks. Clock drift, "
    "copying, synchronization, timezone assumptions, and source "
    "metadata conventions can affect event order. Preserve and examine "
    "the original evidence before drawing conclusions."
)
