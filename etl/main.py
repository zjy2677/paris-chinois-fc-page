import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.database import get_engine
from app.models import SyncRun
from sqlalchemy.orm import Session

from .config import SourceConfig
from .fetch import check_robots, fetch
from .load import load
from .parse_fixtures import parse_fixtures
from .parse_standings import parse_standings


def main():
    parser = argparse.ArgumentParser(description="Manually import the configured FLA championship")
    parser.add_argument("--standings-file", type=Path)
    parser.add_argument("--fixtures-file", type=Path)
    parser.add_argument(
        "--write", action="store_true", help="Commit validated data; default is dry run"
    )
    args = parser.parse_args()
    if bool(args.standings_file) != bool(args.fixtures_file):
        parser.error("Supply both saved HTML files or neither")
    config = SourceConfig()
    try:
        if args.standings_file:
            standings_html = args.standings_file.read_text()
            fixtures_html = args.fixtures_file.read_text()
        else:
            check_robots([config.standings_url, config.fixtures_url])
            standings_html, fixtures_html = (
                fetch(config.standings_url),
                fetch(config.fixtures_url),
            )
        rows = parse_standings(standings_html, config)
        fixtures, skipped = parse_fixtures(fixtures_html, rows, config)
    except Exception as exc:  # noqa: BLE001 - record a failed import without exposing driver details
        if args.write:
            with Session(get_engine()) as db, db.begin():
                db.add(
                    SyncRun(
                        dataset="league",
                        source_url=config.standings_url,
                        status="failed",
                        finished_at=datetime.now(timezone.utc),
                        error_summary=type(exc).__name__,
                    )
                )
        raise SystemExit(
            f"FLA extraction failed ({type(exc).__name__}); no league data published"
        ) from None
    result = (
        load(get_engine(), config, rows, fixtures)
        if args.write
        else {"dry_run": True, "matches": len(fixtures), "standings": len(rows)}
    )
    print(json.dumps({**result, "skipped_non_league_cards": skipped}))


if __name__ == "__main__":
    main()
