from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ResponsePayload(BaseModel, Generic[T]):
    code: int
    message: str
    payload: T


class PaginatedPayload(BaseModel, Generic[T]):
    model_config = ConfigDict(populate_by_name=True)
    items: list[T]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")
