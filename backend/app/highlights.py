"""Trusted YouTube URL normalization; no arbitrary iframe URLs or HTML."""

import re
from urllib.parse import parse_qs, urlparse


def youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        raise ValueError("Use an HTTPS YouTube URL")
    if parsed.hostname == "youtu.be":
        value = parsed.path.removeprefix("/")
    elif parsed.hostname in {"youtube.com", "www.youtube.com"} and parsed.path == "/watch":
        value = parse_qs(parsed.query).get("v", [""])[0]
    else:
        raise ValueError("Unsupported YouTube URL")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        raise ValueError("Invalid YouTube video identifier")
    return value


def canonical_url(url: str) -> str:
    return f"https://www.youtube.com/watch?v={youtube_id(url)}"


def embed_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        return f"https://www.youtube-nocookie.com/embed/{youtube_id(url)}?playsinline=1&rel=0"
    except ValueError:
        return None
