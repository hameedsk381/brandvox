from pydantic import BaseModel, Field
from typing import Optional

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

class MessageResponse(BaseModel):
    message: str
