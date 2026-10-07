from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .blog import router as blog_router
from .config import get_settings
from .goals.router import router as goals_router
from .guestbook import router as guestbook_router
from .media import router as media_router
from .players.router import router as players_router
from .profile import router as profile_router
from .routers import router

app = FastAPI(title="Paris Chinois FC API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(router)

app.include_router(auth_router)
app.include_router(blog_router)
app.include_router(guestbook_router)
app.include_router(media_router)
app.include_router(profile_router)
app.include_router(goals_router)

app.include_router(players_router)
