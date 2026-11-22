
import pandas as pd


def detect_temporal_conflicts(df):
    out = df.copy()

    out["temporal_flag"] = "No conflict detected"
    out["temporal_reason"] = ""

    valid = out[out["timestamp_utc"].notna()].copy()

    if "entity_key" in out.columns:
        for entity, group in valid.groupby("entity_key"):
            descriptions = group["event_description"].fillna("").astype(str)

            creations = group[
                descriptions.str.contains(
                    r"\bcreated?\b|\bcreation\b",
                    case=False,
                    regex=True,
                )
            ]

            accesses = group[
                descriptions.str.contains(
                    r"\baccessed?\b",
                    case=False,
                    regex=True,
                )
            ]

            if creations.empty:
                continue

            earliest_creation = creations["timestamp_utc"].min()

            for idx, row in accesses.iterrows():
                if row["timestamp_utc"] < earliest_creation:
                    out.at[idx, "temporal_flag"] = (
                        "Potential ordering conflict"
                    )
                    out.at[idx, "temporal_reason"] = (
                        f"Access precedes the earliest recorded creation "
                        f"for entity '{entity}'. Verify source semantics."
                    )

    # Exact repeated-event candidates; not proof of duplication.
    duplicate_columns = [
        "source_type",
        "event_description",
        "timestamp_utc",
        "entity_key",
    ]

    if all(col in out.columns for col in duplicate_columns):
        duplicate_mask = out.duplicated(
            subset=duplicate_columns,
            keep=False,
        )

        for idx in out.index[duplicate_mask]:
            if out.at[idx, "temporal_flag"] == "No conflict detected":
                out.at[idx, "temporal_flag"] = "Duplicate candidate"
                out.at[idx, "temporal_reason"] = (
                    "Matching source, description, timestamp and entity. "
                    "Check original records before concluding duplication."
                )

    return out
