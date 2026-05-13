from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GroupToolInput(BaseModel):
    endpoint: str = Field(..., description="The endpoint URL within the group.")
    filter_expression: Optional[str] = Field(default=None)
    query_params: Optional[Dict[str, Any]] = Field(default=None)


class NonFilterableToolInput(BaseModel):
    query_params: Optional[Dict[str, Any]] = Field(default=None)


class CreateToolInput(BaseModel):
    payload: Dict[str, Any] = Field(..., description="JSON payload for POST.")
