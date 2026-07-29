"""Standard API response envelopes mandated by AGENTS.md."""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Canonical successful API response envelope."""

    success: bool = True
    message: str = ""
    data: DataT | dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    """Detailed validation or domain error item."""

    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """Canonical failed API response envelope."""

    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)
