import json
from typing import Any, Dict, Type

from fastapi import Request
from sqlalchemy import Date, Integer, String, asc, cast, desc
from sqlalchemy.orm import Query, Session


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


def get_paginated_data(
    db: Session, request: Request, model, schema, initial_sorted_column, base_query=None
):
    # Extract pagination and sorting parameters from the request
    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    sort = request.query_params.get("sort", f"{initial_sorted_column}:desc")
    filter_param = request.query_params.get("filter", None)
    sort_column, sort_order = sort.split(":")

    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Base query - use provided query or create new one
    query = base_query if base_query is not None else db.query(model)

    # Apply filters if provided
    if filter_param:
        query = apply_filters(model, filter_param, query)

    # Apply sorting
    if sort_column and sort_order:
        if sort_order.lower() == "asc":
            query = query.order_by(asc(getattr(model, sort_column)))
        else:
            query = query.order_by(desc(getattr(model, sort_column)))

    # Get total count of Contractor records
    total_count = query.count()

    # Apply pagination
    data = query.offset(offset).limit(limit).all()

    # Validate Contractor data using the schema and convert to JSON-serializable dicts
    data = [schema.model_validate(contractor).model_dump(mode='json') for contractor in data]

    # Compute pagination metadata
    last_page = (total_count + limit - 1) // limit
    url = str(request.url).split("?")[0]

    meta = {
        "total": total_count,
        "perPage": limit,
        "currentPage": page,
        "lastPage": last_page,
        "firstPage": 1,
        "firstPageUrl": f"{url}?page=1&limit={limit}",
        "lastPageUrl": f"{url}?page={last_page}&limit={limit}",
        "nextPageUrl": f"{url}?page={min(page + 1, last_page)}&limit={limit}",
        "previousPageUrl": f"{url}?page={max(page - 1, 1)}&limit={limit}",
    }

    return {"meta": meta, "data": data}


def get_options(
    db: Session,
    model,
    label_column: str,
    value_column: str = "id",
):
    options = db.query(
        getattr(model, label_column).label("label"),
        getattr(model, value_column).label("value"),
    ).all()

    return [{"label": option.label, "value": option.value} for option in options]
