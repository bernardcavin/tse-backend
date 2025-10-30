import uuid
from datetime import datetime


def parse_string(string: str):
    s = string.strip()

    # Boolean
    if s.lower() in ["true", "false"]:
        return s.lower() == "true"

    # Integer
    if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
        return int(s)

    # Float
    try:
        return float(s)
    except ValueError:
        pass

    # UUID
    try:
        return uuid.UUID(s)
    except ValueError:
        pass

    # Date parsing (try several formats)
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%Y",
        "%d-%b-%Y",
        "%b %d, %Y",
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue

    # Default: string
    return s


def parse_input(data):
    # If it's a comma-separated string → split into list
    if isinstance(data, str) and "," in data:
        return [parse_string(item) for item in data.split(",")]
    # Normal single value
    return parse_string(data)
