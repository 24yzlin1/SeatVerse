from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ResponsePayload(BaseModel, Generic[T]):
    code: int
    message: str
    payload: T
