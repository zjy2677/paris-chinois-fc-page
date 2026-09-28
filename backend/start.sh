#!/usr/bin/env sh
set -eu
# Render Free has no pre-deploy hook. One worker runs migrations before serving.
# A migration/configuration failure stops deployment instead of serving a stale schema.
python -c 'from app.config import get_settings; get_settings()'
alembic -c backend/alembic.ini upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
