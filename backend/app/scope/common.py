from typing import TypeVar
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.common import AppError
from app.types.common import ResponsePayload

T = TypeVar("T")


def ok(payload: T, message: str = "ok") -> ResponsePayload[T]:
    return ResponsePayload(code=200, message=message, payload=payload)


def error_handler(request: Request, exception: Exception) -> JSONResponse:
    if isinstance(exception, AppError):
        return JSONResponse(
            status_code=200,
            content=ResponsePayload[None](
                code=exception.code,
                message=exception.message,
                payload=None,
            ).model_dump(mode="json"),
        )

    if isinstance(exception, SyntaxError) and getattr(exception, "status", None) == 400:
        return JSONResponse(
            status_code=200,
            content=ResponsePayload[None](
                code=400, message="Invalid JSON body", payload=None
            ).model_dump(mode="json"),
        )

    return JSONResponse(
        status_code=200,
        content=ResponsePayload[None](
            code=500, message="Internal server error", payload=None
        ).model_dump(mode="json"),
    )
