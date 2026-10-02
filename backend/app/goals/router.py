from uuid import UUID

from fastapi import APIRouter, Depends

from ..auth.dependencies import DB, no_store, require_role, throttle, trusted_origin
from . import service
from .schemas import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/api/matches/{match_id}/goals", tags=["Match goals"])
admin_mutation = [
    Depends(require_role("admin")),
    Depends(trusted_origin),
    Depends(throttle),
    Depends(no_store),
]


@router.get("", response_model=list[GoalResponse])
def goals(match_id: UUID, db: DB):
    """Return goals for an existing match in match-time order."""
    service.get_match(db, match_id)
    return service.list_goals(db, match_id)


@router.post("", response_model=GoalResponse, status_code=201, dependencies=admin_mutation)
def create_goal(match_id: UUID, body: GoalCreate, db: DB):
    """Create a goal for a match after the admin mutation checks pass."""
    return service.create_goal(db, match_id, body)


@router.patch("/{goal_id}", response_model=GoalResponse, dependencies=admin_mutation)
def update_goal(match_id: UUID, goal_id: UUID, body: GoalUpdate, db: DB):
    """Apply a partial goal update after the admin mutation checks pass."""
    return service.update_goal(db, match_id, goal_id, body)


@router.delete("/{goal_id}", status_code=204, dependencies=admin_mutation)
def delete_goal(match_id: UUID, goal_id: UUID, db: DB):
    """Delete a goal belonging to the match after the admin mutation checks pass."""
    service.delete_goal(db, match_id, goal_id)
