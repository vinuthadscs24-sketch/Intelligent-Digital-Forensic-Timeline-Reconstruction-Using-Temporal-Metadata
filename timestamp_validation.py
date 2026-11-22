
import pandas as pd


def validate_timestamps(df):
    """
    Validate timestamps without guessing unknown timezones.

    timestamp_local: Parsed original clock time.
    timestamp_utc: UTC-normalized timestamp when timezone is known.
    timestamp_status: Validation result.
    """

    out = df.copy()

    statuses = []
    local_values = []
    utc_values = []

    for _, row in out.iterrows():

        raw = str(row.get("timestamp_original", "")).strip()
        tz = str(row.get("timezone", "")).strip()

        # Check missing timestamps
        if raw.lower() in {"", "nan", "none", "nat"}:

            statuses.append("Missing timestamp")
            local_values.append(pd.NaT)
            utc_values.append(pd.NaT)
            continue

        # Parse timestamp
        try:
            ts = pd.to_datetime(
                raw,
                format="%d.%m.%Y. %H:%M:%S",
                errors="raise",
            )

        except (ValueError, TypeError):

            try:
                ts = pd.Timestamp(raw)

            except (ValueError, TypeError, OverflowError):

                statuses.append("Invalid timestamp")
                local_values.append(pd.NaT)
                utc_values.append(pd.NaT)
                continue

        # Preserve the parsed original clock time
        local_values.append(ts)

        # Unknown timezone: do not guess UTC
        if tz.lower() in {"", "nan", "none", "unknown"}:

            statuses.append("Timezone unknown")
            utc_values.append(pd.NaT)
            continue

        # Convert using the supplied timezone
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

    out["timestamp_local"] = local_values
    out["timestamp_utc"] = utc_values
    out["timestamp_status"] = statuses

    return out
