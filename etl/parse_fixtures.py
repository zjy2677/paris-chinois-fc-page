import re
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .config import SourceConfig
from .parse_standings import Standing

MONTHS = {
    "janv": 1,
    "févr": 2,
    "mars": 3,
    "avr": 4,
    "mai": 5,
    "juin": 6,
    "juil": 7,
    "août": 8,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "déc": 12,
}


@dataclass(frozen=True)
class Fixture:
    source_key: str
    home_id: int
    away_id: int
    matchday: int | None
    leg: str
    kickoff: datetime | None
    stadium: str
    address: str
    status: str
    home_score: int | None
    away_score: int | None
    competition_kind: str = "league"
    stage: str = ""


def clean_address(address: str, stadium: str) -> str:
    # Maps query repeats the venue name and sometimes postcode/city at its tail.
    address = " ".join(address.split())
    if stadium and address.startswith(stadium):
        address = address[len(stadium) :].lstrip(" ,")
    # Remove only an exact repeated postcode/city suffix, not a city name
    # that also happens to occur in the street (e.g. rue de Paris).
    duplicate = re.fullmatch(
        r"(.*\b(\d{5})\s+([^,]+)),\s*\2,\s*\3", address, re.IGNORECASE
    )
    return duplicate[1] if duplicate else address


def parse_fixtures(html: str, standings: list[Standing], config: SourceConfig):
    soup = BeautifulSoup(html, "html.parser")
    names = {r.name.upper(): r.team_id for r in standings}
    names.update(config.aliases)
    names.update({name.upper(): id for id, name in config.cup_teams.items()})
    unique = {}
    skipped = 0
    cards = soup.select('[data-testid="rencontre"]')
    if not cards:
        raise ValueError("No fixture cards found")
    for card in cards:
        text = card.get_text(" ", strip=True)
        is_cup = text.startswith("Coupe ")
        if not is_cup and not text.startswith("Championnat "):
            raise ValueError("Unrecognized competition card")
        if (config.cup_name if is_cup else config.championship_name) not in text:
            raise ValueError("Unexpected competition in team fixtures")
        stage = ""
        if is_cup:
            heading = card.find("div").get_text(" ", strip=True)
            stage = (
                heading.removeprefix("Coupe ").removeprefix(config.cup_name).strip(" —")
            )
            stage = re.sub(r"\s+(Domicile|Extérieur)$", "", stage).strip()
            if not stage:
                raise ValueError("Missing cup stage")
        round_match = re.search(r"Journée (\d+)", text)
        leg_match = re.search(r"\b(Aller|Retour)\b", text)
        opponent = next(
            (
                p.get_text(" ", strip=True)
                for p in card.select("p")
                if p.get_text(strip=True).startswith(("Reçoit ", "Se déplace chez "))
            ),
            None,
        )
        if not opponent or (not is_cup and (not round_match or not leg_match)):
            raise ValueError("Missing fixture identity")
        at_home = opponent.startswith("Reçoit ")
        name = (
            opponent.removeprefix("Reçoit ")
            .removeprefix("Se déplace chez ")
            .strip()
            .upper()
        )
        if name not in names:
            raise ValueError(f"Unmapped opponent: {name}")
        home, away = (
            (config.team_id, names[name]) if at_home else (names[name], config.team_id)
        )
        day, leg = (None, stage) if is_cup else (int(round_match[1]), leg_match[1])
        source_key = (
            f"cup:{config.cup_id}:{config.season_id}:{home}:{away}:{stage}"
            if is_cup
            else f"{config.championship_id}:{config.season_id}:{home}:{away}:{day}:{leg}"
        )
        dt = re.search(
            r"(\d{1,2}) (janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.? (\d{4})",
            text,
        )
        tm = re.search(r"(\d{1,2})h(\d{2})", text)
        kickoff = None
        if dt and tm:
            kickoff = datetime(
                int(dt[3]),
                MONTHS[dt[2]],
                int(dt[1]),
                int(tm[1]),
                int(tm[2]),
                tzinfo=ZoneInfo("Europe/Paris"),
            )
            start_year = int(config.season_label[:4])
            if (
                not datetime(start_year, 7, 1, tzinfo=kickoff.tzinfo)
                <= kickoff
                < datetime(start_year + 1, 7, 1, tzinfo=kickoff.tzinfo)
            ):
                raise ValueError("Fixture date outside configured season")
        elif not re.search(r"(à définir|à confirmer|reporté)", text, re.IGNORECASE):
            raise ValueError("Missing or unrecognized kickoff")
        venue = card.select_one('[data-testid="terrain-itineraire"]')
        stadium = (
            venue.get("title", "").removeprefix("Ouvrir l'itinéraire vers ")
            if venue
            else ""
        )
        address = (
            parse_qs(urlparse(venue["href"]).query).get("query", [""])[0]
            if venue
            else ""
        )
        address = clean_address(address, stadium)
        status = "unknown"
        home_score = away_score = None
        score_node = card.select_one('[data-testid="rencontre-score"]')
        score = (
            re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)", score_node.get_text(strip=True))
            if score_node
            else None
        )
        if score_node and not score:
            raise ValueError("Unrecognized result score")
        if score:
            # The V/N/D marker describes this club's result. Use it to resolve
            # score orientation without assuming the first number is the home team.
            marker = score_node.find_next_sibling("span")
            outcome = marker.get_text(strip=True) if marker else ""
            first, second = int(score[1]), int(score[2])
            if outcome == "N" and first == second:
                club_score = opponent_score = first
            elif outcome in {"V", "D"} and first != second:
                club_score, opponent_score = sorted(
                    (first, second), reverse=outcome == "V"
                )
            else:
                raise ValueError("Missing or inconsistent club result marker")
            home_score, away_score = (
                (club_score, opponent_score)
                if at_home
                else (opponent_score, club_score)
            )
            status = "final"
        elif "À jouer" in text:
            status = "scheduled"
        elif re.search("reporté", text, re.IGNORECASE):
            status = "postponed"
        elif re.search("annulé", text, re.IGNORECASE):
            status = "cancelled"
        item = Fixture(
            source_key,
            home,
            away,
            day,
            leg,
            kickoff,
            stadium,
            address,
            status,
            home_score,
            away_score,
            "cup" if is_cup else "league",
            stage,
        )
        if source_key in unique and unique[source_key] != item:
            raise ValueError("Conflicting repeated fixture")
        unique[source_key] = item
    if not unique:
        raise ValueError("No selected-championship fixtures found")
    return list(unique.values()), skipped
