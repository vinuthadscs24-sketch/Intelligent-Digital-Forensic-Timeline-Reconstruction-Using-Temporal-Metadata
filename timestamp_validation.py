import pandas as pd

def validate_timestamps(df):
    """Return a copy with parse status and UTC timestamp; never guess unknown timezones."""
    out = df.copy()
    statuses, utc_values = [], []
    for _, row in out.iterrows():
        raw = str(row.get("timestamp_original", "")).strip()
        tz = str(row.get("timezone", "")).strip()
        if raw.lower() in {"", "nan", "none"}:
            statuses.append("Missing timestamp")
            utc_values.append(pd.NaT)
            continue
        try:
            ts = pd.Timestamp(raw)
        except Exception:
            statuses.append("Invalid timestamp")
            utc_values.append(pd.NaT)
            continue
        if tz.lower() in {"", "nan", "none", "unknown"}:
            statuses.append("Timezone unknown")
            utc_values.append(pd.NaT)
            continue
        try:
            if ts.tzinfo is None:
                ts = ts.tz_localize(tz)
            else:
                ts = ts.tz_convert(tz)
            utc_values.append(ts.tz_convert("UTC"))
            statuses.append("OK")
        except Exception:
            statuses.append("Invalid/unsupported timezone")
            utc_values.append(pd.NaT)
    out["timestamp_utc"] = utc_values
    out["timestamp_status"] = statuses
    return out
