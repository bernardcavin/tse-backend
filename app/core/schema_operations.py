from typing import Any, Optional, Type, Union

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel as PydanticBaseModel
from pydantic import JsonValue, ValidationError


class BaseModel(PydanticBaseModel):
    class Config:
        from_attributes = True
        populate_by_name = True


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[Any] = None


def build_nested_model(model: type[BaseModel], data):
    result = {}

    for field, field_info in model.model_fields.items():
        field_type = field_info.annotation

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            result[field] = build_nested_model(field_type, data)
        else:
            result[field] = data.get(field)

    return result


def create_api_response(
    success: bool, message: str, data: Optional[Any] = "None", status_code: int = 200
):
    if not success:
        if status_code == 200:
            status_code = 500
        raise HTTPException(status_code=status_code, detail=message)

    output = {
        "success": success,
        "message": message,
    }

    if data != "None":
        output["data"] = data

    return output


class PlotlyJSONSchema(BaseModel):
    data: JsonValue
    layout: JsonValue


def is_pydantic(obj: object):
    """Checks whether an object is pydantic."""
    return type(obj).__class__.__name__ == "ModelMetaclass"

def model_from_dict(model, data: dict, exclude_ids: bool = False):
    """
    Creates a new SQLAlchemy model instance from a dictionary,
    ignoring keys not present on the model or set to None.
    Optionally strips 'id' fields.
    """
    new_data = {}
    for key, value in data.items():
        if exclude_ids and key == "id":
            continue
        if value is not None and hasattr(model, key):
            new_data[key] = value
    
    # print(new_data)

    return model(**new_data)


def parse_schema(schema, exclude_ids: bool = False):
    """
    Recursively converts a Pydantic schema (and nested schemas) 
    into dictionaries or SQLAlchemy model instances.

    - Nested lists of schemas are converted into lists of models.
    - Nested single schemas are converted into models.
    - Keys with None values are dropped.
    - If exclude_ids=True, any key named "id" is removed at all levels.
    """
    parsed_schema = dict(schema)  # clone to dict
    parsed_schema_copy = parsed_schema.copy()

    for key, value in parsed_schema_copy.items():
        # Drop "id" at this level
        if exclude_ids and key == "id":
            parsed_schema.pop(key, None)
            continue

        # Handle nested list of Pydantic schemas
        if isinstance(value, list) and value and is_pydantic(value[0]):
            child_parsed_schema = []
            for item in value:
                child_dict = parse_schema(item, exclude_ids=exclude_ids)
                if exclude_ids and "id" in child_dict:
                    child_dict.pop("id")
                child_parsed_schema.append(
                    model_from_dict(item.Meta.orm_model, child_dict, exclude_ids=exclude_ids)
                )
            parsed_schema[key] = child_parsed_schema

        # Handle nested single Pydantic schema
        elif not isinstance(value, list) and is_pydantic(value):
            child_dict = parse_schema(value, exclude_ids=exclude_ids)
            if exclude_ids and "id" in child_dict:
                child_dict.pop("id")
            parsed_schema[key] = model_from_dict(value.Meta.orm_model, child_dict, exclude_ids=exclude_ids)

        # Drop None values
        elif value is None:
            parsed_schema.pop(key, None)
            
    return parsed_schema

def parse_validation_error(exc: Union[ValidationError, RequestValidationError]):
    error_list = []

    for error in exc.errors():
        error_location = error["loc"][-1]

        error_list.append(
            f"Error at {error_location if isinstance(error_location, str) else error['loc'][-2]}: {error['msg']}, Your input was {error['input']}"
        )

    return error_list


def generate_custom_model(original_model: BaseModel, new_type: Type, model_name: str):
    # Dynamically create a dictionary for the new model annotations with the custom type
    annotations = {
        field: Optional[new_type] for field in original_model.__annotations__
    }

    # Create a new dictionary for fields with their original Field settings
    fields = {
        field: original_model.model_fields[field]
        for field in original_model.__annotations__
    }

    # Create the new Pydantic model dynamically with the custom model name, annotations, and fields
    return type(
        model_name,  # New model name as input
        (BaseModel,),  # Base class
        {
            "__annotations__": annotations,  # Set annotations to the new type
            **fields,  # Copy the fields from the original model
        },
    )


# class AllRequired(ModelMetaclass):
#     def __new__(self, name, bases, namespaces, **kwargs):
#         annotations = namespaces.get('__annotations__', {})
#         print(annotations)
#         for base in bases:
#             annotations.update(base.__annotations__)
#         for field in annotations:
#             if not field.startswith('__'):
#                 if getattr(annotations[field], '_name', None) is "Optional":
#                     annotations[field] = get_args(annotations[field])[0]
#                 else:
#                     annotations[field] = annotations[field]
#         namespaces['__annotations__'] = annotations
#         return super().__new__(self, name, bases, namespaces, **kwargs)


def parse_data_from_schema(data: list, schema) -> list[dict]:
    if data:
        return [schema.model_validate(d).model_dump() for d in data]
    else:
        return []
