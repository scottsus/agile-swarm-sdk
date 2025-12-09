from datetime import datetime, timezone


def utcnow() -> datetime:
    """Get current UTC time as timezone-aware datetime.

    Replacement for deprecated datetime.utcnow().

    Example:
        >>> now = utcnow()
        >>> now.tzinfo == timezone.utc
        True
    """
    return datetime.now(timezone.utc)


def timestamp_compact() -> str:
    """Get current UTC timestamp in compact format for IDs.

    Format: YYYYMMDD_HHMMSS (e.g., '20231215_143022')

    Example:
        >>> timestamp = timestamp_compact()
        >>> len(timestamp)
        15
    """
    return utcnow().strftime("%Y%m%d_%H%M%S")


def timestamp_readable() -> str:
    """Get current UTC timestamp in readable format for directories.

    Format: YYYY-MM-DD_HH:MM:SS (e.g., '2025-12-08_17:41:23')

    Example:
        >>> timestamp = timestamp_readable()
        >>> ":" in timestamp
        True
    """
    return utcnow().strftime("%Y-%m-%d_%H:%M:%S")


def timestamp_iso() -> str:
    """Get current UTC timestamp in ISO 8601 format with Z suffix.

    Format: YYYY-MM-DDTHH:MM:SS.ffffffZ (e.g., '2023-12-15T14:30:22.123456Z')

    Example:
        >>> timestamp = timestamp_iso()
        >>> timestamp.endswith("Z")
        True
    """
    return utcnow().isoformat() + "Z"
