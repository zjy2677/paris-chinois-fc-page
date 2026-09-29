from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .blog import router as blog_router
from .config import get_settings
from .guestbook import router as guestbook_router
from .profile import router as profile_router
from .routers import router

app = FastAPI(title="Paris Chinois FC API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

app.include_router(auth_router)
app.include_router(blog_router)
app.include_router(guestbook_router)
app.include_router(profile_router)
