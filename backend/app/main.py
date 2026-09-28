from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .config import get_settings
from .routers import router

app = FastAPI(title="Paris Chinois FC API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

app.include_router(auth_router)
