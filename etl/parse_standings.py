import re
from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup

from .config import SourceConfig


@dataclass(frozen=True)
class Standing:
    team_id: int
    name: str
    position: int
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goal_difference: int


def parse_standings(html: str, config: SourceConfig) -> list[Standing]:
    soup = BeautifulSoup(html, "html.parser")
    season = soup.select_one('select[name="season"] option[selected]')
    if not season or season.get("value") != str(config.season_id):
        raise ValueError("Unexpected or missing source season")
    if season.get_text(strip=True).replace("-", "/") != config.season_label:
        raise ValueError("Source season label does not match configuration")
    headings = [x.get_text(" ", strip=True) for x in soup.select("h1")]
    if config.championship_name not in headings:
        raise ValueError("Unexpected championship")
    candidates = [
        t
        for t in soup.select("table")
        if [x.get_text(" ", strip=True) for x in t.select("thead th")]
        == ["Pos", "Équipe", "Pts", "J", "G", "N", "P", "Diff"]
    ]
    if len(candidates) != 1:
        raise ValueError("Expected exactly one complete standings table")
    rows = []
    for position, tr in enumerate(candidates[0].select("tbody tr"), 1):
        cells = tr.select("td")
        if len(cells) != 8:
            raise ValueError("Malformed standings row")
        link = cells[1].select_one("a[href]")
        match = re.search(r"/teams/(\d+)$", link["href"]) if link else None
        if not match:
            raise ValueError("Missing stable team identifier")
        displayed_rank = cells[0].get_text(strip=True)
        if displayed_rank and int(displayed_rank) != position:
            raise ValueError("Non-sequential source rank")
        if not displayed_rank and position > 3:
            raise ValueError("Unexpected missing rank")
        numbers = [int(c.get_text(strip=True).replace("−", "-")) for c in cells[2:]]
        row = Standing(int(match[1]), link.get_text(" ", strip=True), position, *numbers)
        if (
            min(row.played, row.wins, row.draws, row.losses) < 0
            or row.played != row.wins + row.draws + row.losses
        ):
            raise ValueError("Invalid standings totals")
        rows.append(row)
    ids = [r.team_id for r in rows]
    # Cross-check the independently listed team cards when present.
    team_links = {
        int(m[1]) for a in soup.select("a[href]") if (m := re.search(r"/teams/(\d+)$", a["href"]))
    }
    if len(rows) < 2 or len(ids) != len(set(ids)) or config.team_id not in ids:
        raise ValueError("Incomplete or duplicate standings")
    if team_links != set(ids):
        raise ValueError("Standings do not cover the listed championship teams")
    return rows


def canonical_rows(rows):
    return [asdict(row) for row in rows]
