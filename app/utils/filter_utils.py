import json
from typing import Any, Dict, Type
from sqlalchemy.orm import Query
from sqlalchemy import cast, String, Integer, Date


def apply_filters(
    model: Type[Any],
    filter_args: Dict[str, Any],
    query: Query,
) -> Query:
    if isinstance(filter_args, str):
        try:
            filter_args = json.loads(filter_args)
        except json.JSONDecodeError:
            return query

    for key in filter_args:
        filters = filter_args[key]
        name = filters.get("name")
        value = filters.get("value")

        if not name or value is None:
            continue

        column = getattr(model, name, None)

        if column is None:
            continue

        if isinstance(column.type, Integer):
            try:
                min_val_str, *max_val_list = value.split("-")
                max_val_str = max_val_list[0] if max_val_list else None
                min_val = int(min_val_str)

                if max_val_str in ("", None):
                    query = query.filter(column >= min_val)
                else:
                    query = query.filter(column >= min_val, column <= int(max_val_str))
            except (ValueError, IndexError):

                return query

        elif isinstance(column.type, Date):
            if " to " in value:
                try:
                    start_date, end_date = value.split(" to ")
                    query = query.filter(column >= start_date, column <= end_date)
                except ValueError:
                    return query
            else:
                query = query.filter(column == value)

        else:
            query = query.filter(cast(column, String).ilike(f"%{value}%"))

    return query
