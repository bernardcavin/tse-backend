from app.api.services.models import Service
from app.core.schema_operations import BaseModel


class ServiceSchema(BaseModel):
    name: str
    category: str
    description: str
    duration_minutes: float
    price: float
    is_active: bool

    class Meta:
        orm_model = Service