
import pandas as pd
import streamlit as st
import plotly.express as px
from pathlib import Path

from timestamp_validation import validate_timestamps
from temporal_analysis import detect_temporal_conflicts


# -----------------------------------------
# 1. Application setup
# -----------------------------------------

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


# -----------------------------------------
# 2. Upload dataset
# -----------------------------------------

uploaded = st.file_uploader(
    "Upload forensic events (CSV)",
    type=["csv"],
)

try:
    df = pd.read_csv(uploaded) if uploaded else pd.read_csv(SAMPLE)

except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()


# -----------------------------------------
# 3. Validate required columns
# -----------------------------------------

required = {
    "event_id",
    "source_type",
    "event_description",
    "timestamp_original",
    "timezone",
}

missing = required - set(df.columns)

if missing:
    st.error(
        "Missing required columns: "
        + ", ".join(sorted(missing))
    )
    st.stop()


df["timestamp_original"] = (
    df["timestamp_original"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["timezone"] = (
    df["timezone"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# -----------------------------------------
# 4. Validate timestamps
# -----------------------------------------

try:
    df = validate_timestamps(df)

except Exception as e:
    st.error(f"Timestamp validation failed: {e}")
    st.stop()


# -----------------------------------------
# 5. Detect temporal conflicts
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
# 6. Highlight both events in an ordering pair
# -----------------------------------------

if "entity_key" in df.columns:

    conflict_rows = df[
        df["temporal_flag"] == "Potential ordering conflict"
    ]

    for idx, row in conflict_rows.iterrows():

        entity = row["entity_key"]
        access_time = row["timestamp_utc"]

        if pd.isna(access_time):
            continue

        descriptions = (
            df["event_description"]
            .fillna("")
            .astype(str)
        )

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

            if (
                df.at[creation_idx, "temporal_flag"]
                == "No conflict detected"
            ):

                df.at[creation_idx, "temporal_flag"] = (
                    "Related ordering conflict"
                )

                df.at[creation_idx, "temporal_reason"] = (
                    "This creation event occurs after an access event "
                    "for the same entity that was flagged for review. "
                    "Review both source records."
                )


# -----------------------------------------
# 7. Assign review categories
# -----------------------------------------

df["review_category"] = "Normal — parsed, not verified"

timestamp_issues = (
    df["timestamp_status"] != "OK"
)

df.loc[
    timestamp_issues,
    "review_category"
] = "Timestamp issue"


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
# 8. Summary metrics
# -----------------------------------------

review_count = int(df["requires_review"].sum())

valid_count = int(
    df["timestamp_utc"].notna().sum()
)

local_count = (
    int(df["timestamp_local"].notna().sum())
    if "timestamp_local" in df.columns
    else 0
)

ordering_count = int(
    (
        df["temporal_flag"]
        == "Potential ordering conflict"
    ).sum()
)

related_count = int(
    (
        df["temporal_flag"]
        == "Related ordering conflict"
    ).sum()
)

duplicate_count = int(
    (
        df["temporal_flag"]
        == "Duplicate candidate"
    ).sum()
)


c1, c2, c3, c4 = st.columns(4)

c1.metric("Total events", len(df))
c2.metric("UTC timestamps", valid_count)
c3.metric("Events requiring review", review_count)
c4.metric(
    "Ordering conflicts",
    ordering_count + related_count,
)

st.caption(
    f"Parsed local timestamps: {local_count} · "
    f"Timestamp issues: {int(timestamp_issues.sum())} · "
    f"Ordering pairs: {ordering_count} primary, "
    f"{related_count} related · "
    f"Duplicate candidates: {duplicate_count}"
)


# -----------------------------------------
# 9. Styling for review tables
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
# 10. All event records
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

display_df["timestamp_utc"] = (
    display_df["timestamp_utc"].astype(str)
)

MAX_DISPLAY_ROWS = 1000

display_preview = display_df.head(MAX_DISPLAY_ROWS)

st.dataframe(
    display_preview.style.apply(highlight_review, axis=1),
    use_container_width=True,
    hide_index=True,
)

if len(display_df) > MAX_DISPLAY_ROWS:
    st.info(
        f"Showing {MAX_DISPLAY_ROWS:,} of "
        f"{len(display_df):,} events. "
        "All events are still processed by the analysis."
    )


# -----------------------------------------
# 11. Chronological event timeline
# -----------------------------------------

st.subheader("Chronological Event Timeline")

MAX_TIMELINE_DISPLAY = 300


def show_timeline(
    data,
    time_column,
    title,
    axis_label,
    time_note,
):

    timeline_data = (
        data.sort_values(time_column)
        .copy()
    )

    total_events = len(timeline_data)

    # Limit visualization size for large datasets
    timeline_preview = timeline_data.head(
        MAX_TIMELINE_DISPLAY
    ).copy()

    timeline_preview["timeline_label"] = [
    f"Record {i + 1}"
    for i in range(len(timeline_preview))
]


    ordered_labels = (
        timeline_preview["timeline_label"].tolist()
    )

    fig = px.scatter(
        timeline_preview,
        x=time_column,
        y="timeline_label",
        color="review_category",
        category_orders={
            "timeline_label": ordered_labels
        },
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
            if col in timeline_preview.columns
        ],
        title=title,
        labels={
            time_column: axis_label,
            "timeline_label": "Event",
            "review_category": "Review status",
        },
    )

    fig.update_traces(
        marker=dict(
            size=10,
            line=dict(width=1, color="white"),
        )
    )

    fig.update_layout(
        height=max(
            450,
            min(1000, len(timeline_preview) * 25),
        ),
        yaxis_title="Events (earliest to latest)",
        xaxis_title=axis_label,
        legend_title="Review status",
        hovermode="closest",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=30,
        ),
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.caption(
        f"{time_note} "
        f"Showing {len(timeline_preview):,} "
        f"of {total_events:,} events in chronological order."
    )

    # Display chronological event records
    columns = [
        col for col in [
            time_column,
            "event_id",
            "source_type",
            "event_description",
            "review_category",
            "temporal_reason",
        ]
        if col in timeline_preview.columns
    ]

    st.dataframe(
        timeline_preview[columns],
        use_container_width=True,
        hide_index=True,
    )


# A. Timeline using verified timezone information

utc_valid = df[
    df["timestamp_utc"].notna()
].copy()

if not utc_valid.empty:

    show_timeline(
        utc_valid,
        "timestamp_utc",
        "Investigation Timeline — UTC",
        "Normalized time (UTC)",
        "Timestamps with known and successfully converted timezone.",
    )


# B. Separate timeline for parsed timestamps with unknown timezone

if "timestamp_local" in df.columns:

    local_valid = df[
        df["timestamp_local"].notna()
        & df["timestamp_utc"].isna()
    ].copy()

    if not local_valid.empty:

        st.markdown("### Local-Time Timeline")

        st.info(
            "These timestamps were successfully parsed, but their "
            "timezone is unknown. This timeline shows recorded local "
            "times only. It must not be interpreted as UTC."
        )

        show_timeline(
            local_valid,
            "timestamp_local",
            "Investigation Timeline — Unverified Local Time",
            "Recorded local time (timezone unknown)",
            "Unverified local-time ordering.",
        )


# C. Handle datasets without usable timestamps

if (
    utc_valid.empty
    and (
        "timestamp_local" not in df.columns
        or df["timestamp_local"].notna().sum() == 0
    )
):

    st.warning(
        "No parseable timestamps are available for the timeline."
    )


# -----------------------------------------
# 12. Dedicated review queue
# -----------------------------------------

st.subheader("⚠️ Events Requiring Review")

flagged = df[
    df["requires_review"]
].copy()

if flagged.empty:

    st.success(
        "No events were flagged by the current rules."
    )

else:

    st.warning(
        f"{len(flagged)} event(s) require examination. "
        "These findings are not proof of malicious activity."
    )

    flagged["timestamp_utc"] = (
        flagged["timestamp_utc"].astype(str)
    )

    MAX_FLAGGED_DISPLAY = 1000

    flagged_preview = flagged.head(
        MAX_FLAGGED_DISPLAY
    )

    st.dataframe(
        flagged_preview,
        use_container_width=True,
        hide_index=True,
    )

    if len(flagged) > MAX_FLAGGED_DISPLAY:

        st.info(
            f"Showing {MAX_FLAGGED_DISPLAY:,} of "
            f"{len(flagged):,} events requiring examination."
        )


# -----------------------------------------
# 13. Interpretation and limitations
# -----------------------------------------

with st.expander("How to interpret the findings"):

    st.markdown(
        """
        - **Timestamp issue:** Missing, invalid, unknown, or
          inconsistent timestamp information requires examination.

        - **Ordering conflict:** An access event precedes the earliest
          recorded creation event for the same entity.

        - **Related event:** The corresponding creation event is also
          highlighted to help examine the full event pair.

        - **Duplicate candidate:** Matching fields suggest that records
          should be compared against their original sources.

        - **Normal — parsed, not verified:** Parsing succeeded, but
          authenticity and clock accuracy have not been established.

        - **Unverified local-time timeline:** Events are arranged using
          their recorded local timestamps without assuming a timezone.
        """
    )


st.warning(
    "This is a rule-based prototype. It does not prove timestamp "
    "tampering or independently verify system clocks. Clock drift, "
    "copying, synchronization, timezone assumptions, and source "
    "metadata conventions can affect event order. Preserve and examine "
    "the original evidence before drawing conclusions."
)

