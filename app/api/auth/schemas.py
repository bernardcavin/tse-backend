from uuid import UUID

from app.core.schema_operations import BaseModel


class UserSchema(BaseModel):
    id: UUID
    name: str
    username: str


# Define a Pydantic model for the JSON payload
class TokenRequest(BaseModel):
    username: str
    password: str


class TokenSchema(BaseModel):
    token_type: str
    access_token: str
