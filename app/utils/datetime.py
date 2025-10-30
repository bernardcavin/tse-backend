import re
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class DateOnly:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            cls.validate, handler(date)
        )

    @classmethod
    def validate(cls, value) -> date:
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        elif isinstance(value, str):
            try:
                validated_date = validate_date(value)
                if validated_date:
                    return validated_date
                else:
                    raise TypeError(f"Invalid date string: {value}")
            except ValueError as e:
                raise TypeError(f"Invalid date string: {value}") from e
        raise TypeError("Invalid type: Expected a date, datetime, or string.")


def validate_time(v):
    if isinstance(v, str):
        v = v.rstrip("Z")

        datetime_match = re.match(
            r"(\d{4}-\d{2}-\d{2}T)?(\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?", v
        )
        if datetime_match:
            _, time_part, microsecond = datetime_match.groups()
            hour, minute, second = time_part.split(":")
            microsecond = microsecond or "0"
            microsecond = microsecond.ljust(6, "0")[:6]

            return time(int(hour), int(minute), int(second), int(microsecond))

        match = re.match(r"(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?", v)
        if match:
            hour, minute, second, microsecond = match.groups()
            microsecond = microsecond or "0"
            microsecond = microsecond.ljust(6, "0")[:6]

            return time(int(hour), int(minute), int(second), int(microsecond))

    if isinstance(v, datetime):
        return v.time()

    if isinstance(v, time):
        return v

    if v is None:
        return None

    raise ValueError(f"Invalid time: {v}")


def validate_date(v: Any) -> date | None:
    if isinstance(v, str):
        v = v.rstrip("Z")

        datetime_match = re.match(
            r"(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)?", v
        )
        if datetime_match:
            date_part, _ = datetime_match.groups()
            return datetime.strptime(date_part, "%Y-%m-%d").date()

        match = re.match(r"(\d{4}-\d{2}-\d{2})|(\d{2}/\d{2}/\d{4})", v)
        if match:
            date_part = match.group(0)
            if "-" in date_part:
                return datetime.strptime(date_part, "%Y-%m-%d").date()
            else:
                return datetime.strptime(date_part, "%d/%m/%Y").date()

    if isinstance(v, datetime):
        return v.date()

    if isinstance(v, date):
        return v

    if v is None:
        return None

    raise ValueError(f"Invalid date: {v}")


class EndTimeBeforeStartTime(Exception): ...


def daterange(date1, date2):
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + timedelta(n)


CURRENT_YEAR = datetime.now().year

# Custom type for Year
class Year(int):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_before_validator_function(
            cls.validate, handler(int)
        )

    @classmethod
    def validate(cls, value) -> int:
        if isinstance(value, str):
            value = value.strip()
            if value.isdigit():
                value = int(value)
            else:
                # try parsing ISO datetime
                try:
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    value = dt.year
                except ValueError:
                    raise ValueError("Year must be digits or ISO date string")
        elif isinstance(value, (date, datetime)):
            value = value.year
        elif not isinstance(value, int):
            raise ValueError("Year must be string, int, or date/datetime")

        if value < 1900 or value > CURRENT_YEAR + 10:
            raise ValueError(f"Year must be between 1900 and {CURRENT_YEAR + 10}")

        return int(value)