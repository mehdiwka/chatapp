import secrets
from typing import Optional, Dict, Any

from fastapi.responses import JSONResponse


def create_success_response(data: dict = None, message: str = "Success"):
    message_body = {"message": message, "status": True, "data": data if data is not None else {}}
    return JSONResponse(
        status_code=200,
        content=message_body,
    )


def raise_http_exception(status_code: int, message: str, data: Optional[Dict[str, Any]] = None) -> JSONResponse:
    data = data or {}
    content = {"message": message, "status": False, "data": data}

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


def create_session_token():
    return secrets.token_hex(16)