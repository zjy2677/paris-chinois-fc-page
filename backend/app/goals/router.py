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
    service.get_match(db, match_id)
    return service.list_goals(db, match_id)


@router.post("", response_model=GoalResponse, status_code=201, dependencies=admin_mutation)
def create_goal(match_id: UUID, body: GoalCreate, db: DB):
    return service.create_goal(db, match_id, body)


@router.patch("/{goal_id}", response_model=GoalResponse, dependencies=admin_mutation)
def update_goal(match_id: UUID, goal_id: UUID, body: GoalUpdate, db: DB):
    return service.update_goal(db, match_id, goal_id, body)


@router.delete("/{goal_id}", status_code=204, dependencies=admin_mutation)
def delete_goal(match_id: UUID, goal_id: UUID, db: DB):
    service.delete_goal(db, match_id, goal_id)
