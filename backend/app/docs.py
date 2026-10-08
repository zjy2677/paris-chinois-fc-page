"""Documentation access uses existing active admin accounts, independently of cookies."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .auth.dependencies import DB, throttle
from .auth.service import authenticate

basic = HTTPBasic(auto_error=False, realm="Admin API documentation")
PRIVATE_HEADERS = {"Cache-Control": "no-store", "Vary": "Authorization"}


def docs_admin(
    request: Request,
    credentials: Annotated[HTTPBasicCredentials | None, Depends(basic)],
    db: DB,
):
    try:
        throttle(request)
        if credentials is None:
            raise HTTPException(401, "Admin credentials required")
        user = authenticate(db, credentials.username, credentials.password)
        if user.role != "admin":
            raise HTTPException(403, "Admin access required")
    except HTTPException as exc:
        headers = {**(exc.headers or {}), **PRIVATE_HEADERS}
        if exc.status_code == 401:
            headers["WWW-Authenticate"] = 'Basic realm="Admin API documentation"'
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
