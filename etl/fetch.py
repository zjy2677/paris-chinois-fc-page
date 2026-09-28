import time
from urllib.robotparser import RobotFileParser

import httpx

USER_AGENT = "ParisChinoisFC-ETL/0.1"
MAX_BYTES = 2_000_000


def fetch(url: str) -> str:
    for attempt in range(3):
        try:
            with httpx.Client(
                timeout=20, follow_redirects=False, headers={"User-Agent": USER_AGENT}
            ) as client:
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    chunks, size = [], 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("Source response too large")
                        chunks.append(chunk)
                    return b"".join(chunks).decode("utf-8")
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == 2:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Source unavailable")


def check_robots(urls: list[str]):
    robots = RobotFileParser()
    try:
        content = fetch("https://football-loisir-amateur.fr/robots.txt")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        return
    robots.parse(content.splitlines())
    if any(not robots.can_fetch(USER_AGENT, url) for url in urls):
        raise ValueError("robots.txt disallows this source")
