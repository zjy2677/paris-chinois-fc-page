from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..models import Match, MatchGoal, Player
from .schemas import GoalCreate, GoalUpdate


def get_match(db: Session, match_id: UUID) -> Match:
    """Return the match or raise HTTP 404 when it does not exist."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(404, "Match not found")
    return match


def list_goals(db: Session, match_id: UUID):
    """Return goals with player details, ordered by time with unknown minutes last."""
    return db.scalars(
        select(MatchGoal)
        .where(MatchGoal.match_id == match_id)
        .options(joinedload(MatchGoal.scorer), joinedload(MatchGoal.assist_player))
        .order_by(
            MatchGoal.minute.asc().nulls_last(),
            MatchGoal.stoppage_minute.asc().nulls_first(),
            MatchGoal.created_at,
            MatchGoal.id,
        )
    ).all()


def validate_references(db: Session, match: Match, body: GoalCreate):
    """Raise HTTP 422 unless the credited team participates and referenced players exist."""
    if body.team_id not in (match.home_team_id, match.away_team_id):
        raise HTTPException(422, "Credited team must participate in this match")
    for player_id in (body.scorer_id, body.assist_player_id):
        if player_id is not None and db.get(Player, player_id) is None:
            raise HTTPException(422, "Player not found")


def save_goal(db: Session, goal: MatchGoal) -> MatchGoal:
    """Commit and refresh a goal, rolling back integrity failures as HTTP 422."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(422, "Invalid goal references or values") from None
    db.refresh(goal)
    return goal


def create_goal(db: Session, match_id: UUID, body: GoalCreate) -> MatchGoal:
    """Validate match and player references, then persist and return a new goal."""
    validate_references(db, get_match(db, match_id), body)
    goal = MatchGoal(match_id=match_id, **body.model_dump())
    db.add(goal)
    return save_goal(db, goal)


def get_goal(db: Session, match_id: UUID, goal_id: UUID) -> MatchGoal:
    """Lock and return a goal in the specified match, or raise HTTP 404."""
    goal = db.scalar(
        select(MatchGoal)
        .where(MatchGoal.id == goal_id, MatchGoal.match_id == match_id)
        .with_for_update()
    )
    if goal is None:
        raise HTTPException(404, "Goal not found in this match")
    return goal


def update_goal(db: Session, match_id: UUID, goal_id: UUID, body: GoalUpdate) -> MatchGoal:
    """Validate the merged goal fields and references before committing a partial update."""
    match = get_match(db, match_id)
    goal = get_goal(db, match_id, goal_id)
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Provide at least one goal field")
    # Validate the complete record so partial edits cannot break cross-field rules.
    values = {name: getattr(goal, name) for name in GoalCreate.model_fields}
    try:
        validated = GoalCreate.model_validate(values | changes)
    except ValidationError:
        raise HTTPException(422, "Invalid goal fields or scorer/assist combination") from None
    validate_references(db, match, validated)
    for name, value in changes.items():
        setattr(goal, name, value)
    return save_goal(db, goal)


def delete_goal(db: Session, match_id: UUID, goal_id: UUID):
    """Delete and commit a goal in the specified match, or raise HTTP 404."""
    get_match(db, match_id)
    db.delete(get_goal(db, match_id, goal_id))
    db.commit()
