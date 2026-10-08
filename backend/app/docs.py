"""Documentation access uses existing active admin accounts, independently of cookies."""

from base64 import b64decode
from binascii import Error as Base64Error

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasicCredentials
from fastapi.security.utils import get_authorization_scheme_param

from .auth.dependencies import DB, throttle
from .auth.service import authenticate

PRIVATE_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}


def parse_credentials(request: Request) -> HTTPBasicCredentials:
    # Advertise UTF-8 and preserve the same password character set as registration.
    scheme, payload = get_authorization_scheme_param(request.headers.get("Authorization"))
    if scheme.lower() != "basic" or not payload:
        raise HTTPException(401, "Admin credentials required")
    try:
        decoded = b64decode(payload, validate=True).decode("utf-8")
    except (ValueError, UnicodeDecodeError, Base64Error):
        raise HTTPException(401, "Invalid admin credentials") from None
    username, separator, password = decoded.partition(":")
    if not separator:
        raise HTTPException(401, "Invalid admin credentials")
    return HTTPBasicCredentials(username=username, password=password)


def docs_admin(request: Request, db: DB):
    try:
        # Credentialless cross-origin GETs must not consume the shared login quota.
        credentials = parse_credentials(request)
        throttle(request)
        user = authenticate(db, credentials.username, credentials.password)
        if user.role != "admin":
            raise HTTPException(403, "Admin access required")
    except HTTPException as exc:
        headers = {**(exc.headers or {}), **PRIVATE_HEADERS}
        if exc.status_code == 401:
            headers["WWW-Authenticate"] = 'Basic realm="Admin API documentation", charset="UTF-8"'
        raise HTTPException(exc.status_code, exc.detail, headers=headers) from None


router = APIRouter(dependencies=[Depends(docs_admin)], include_in_schema=False)


@router.get("/docs")
def swagger(request: Request):
    response = get_swagger_ui_html(
        openapi_url=str(request.url_for("private_openapi")),
        title=f"{request.app.title} - Swagger UI",
    )
    response.headers.update(PRIVATE_HEADERS)
    return response


@router.get("/redoc")
def redoc(request: Request):
    response = get_redoc_html(
        openapi_url=str(request.url_for("private_openapi")),
        title=f"{request.app.title} - ReDoc",
    )
    response.headers.update(PRIVATE_HEADERS)
    return response


@router.get("/openapi.json", name="private_openapi")
def openapi(request: Request):
    return JSONResponse(request.app.openapi(), headers=PRIVATE_HEADERS)
