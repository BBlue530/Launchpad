from datetime import datetime, timezone

def format_timestamp(timestamp):
    created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    delta = now - created

    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60

    if days > 0:
        return f"{days}d"
    if hours > 0:
        return f"{hours}h"
    return f"{minutes}m"

def age_to_minutes(age_str: str) -> int:
    value = int(age_str[:-1])
    unit = age_str[-1]

    if unit == "d":
        return value * 24 * 60
    if unit == "h":
        return value * 60
    if unit == "m":
        return value
    return 0