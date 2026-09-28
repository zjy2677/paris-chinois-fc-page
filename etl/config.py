from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceConfig:
    team_id: int = 322
    championship_id: int = 14
    season_id: int = 2
    season_label: str = "2026/2027"
    championship_name: str = "Foot à 7 - Vendredi - 1ère division Elite"
    fixtures_url: str = "https://football-loisir-amateur.fr/teams/322"
    standings_url: str = "https://football-loisir-amateur.fr/championships/14?season=2"
    cup_id: int = 1
    cup_name: str = "COUPE A 7 VENDREDI"
    # Verified through the official /teams?search= directory, distinct from AS SAMSTAG A.
    cup_teams: dict[int, str] = field(default_factory=lambda: {60: "AS SAMSTAG B", 30: "MOBDIN"})
    # Explicitly reviewed FLA display aliases, not fuzzy matching.
    aliases: dict[str, int] = field(
        default_factory=lambda: {
            "ASTERIA": 8,
            "AS SAMSTAG A": 58,
            "TEAM Z FOOTBALL CLUB M": 140,
            "JOGA F.": 199,
            "LES JACKS": 292,
        }
    )
