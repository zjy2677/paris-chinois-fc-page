from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    CompetitionSeason,
    FormationPlacement,
    Match,
    MatchPlayerRating,
    Player,
    PlayerPhoto,
    SquadMembership,
    User,
)
from .schemas import MyRating, PlayerRatingDetail, PlayerRatingSummary, RatingInput, RatingItem


def finished_match(db: Session, match_id: UUID) -> Match:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(404, "Match not found")
    if match.status != "final":
        raise HTTPException(409, "Ratings open after the match is final")
    return match


def summaries(db: Session, match_id: UUID) -> list[PlayerRatingSummary]:
    match = finished_match(db, match_id)
    season = db.get(CompetitionSeason, match.competition_season_id)
    totals = (
        select(
            MatchPlayerRating.player_id.label("player_id"),
            func.avg(MatchPlayerRating.stars).label("average_stars"),
            func.count(MatchPlayerRating.id).label("rating_count"),
        )
        .where(MatchPlayerRating.match_id == match_id)
        .group_by(MatchPlayerRating.player_id)
        .subquery()
    )
    has_photo = select(PlayerPhoto.player_id).where(PlayerPhoto.player_id == Player.id).exists()
    rows = db.execute(
        select(
            Player,
            SquadMembership,
            FormationPlacement,
            has_photo,
            totals.c.average_stars,
            totals.c.rating_count,
        )
        .outerjoin(
            SquadMembership,
            (SquadMembership.player_id == Player.id)
            & (SquadMembership.season_label == season.season_label),
        )
        .outerjoin(
            FormationPlacement,
            and_(
                FormationPlacement.player_id == Player.id,
                FormationPlacement.match_id == match_id,
            ),
        )
        .outerjoin(totals, totals.c.player_id == Player.id)
        .where(
            or_(
                and_(Player.active.is_(True), SquadMembership.id.is_not(None)),
                FormationPlacement.player_id.is_not(None),
            )
        )
        .order_by(Player.display_name, Player.id)
    ).all()
    items = [
        PlayerRatingSummary(
            player_id=player.id,
            display_name=player.display_name,
            chinese_name=player.chinese_name,
            photo_url=player.photo_url,
            has_uploaded_photo=has_photo,
            shirt_number=membership.shirt_number if membership else None,
            participation=(
                "start"
                if placement and placement.placement == "pitch"
                else "sub"
                if placement
                else "absent"
            ),
            average_stars=round(float(average), 1) if average is not None else None,
            rating_count=count or 0,
        )
        for player, membership, placement, has_photo, average, count in rows
    ]
    return sorted(
        items,
        key=lambda item: (
            item.average_stars is None,
            -(item.average_stars or 0),
            item.display_name.casefold(),
        ),
    )


def summary(db: Session, match_id: UUID, player_id: UUID) -> PlayerRatingSummary:
    for item in summaries(db, match_id):
        if item.player_id == player_id:
            return item
    raise HTTPException(404, "Player is not in this match squad")


def detail(db: Session, match_id: UUID, player_id: UUID) -> PlayerRatingDetail:
    player = summary(db, match_id, player_id)
    rows = db.scalars(
        select(MatchPlayerRating)
        .where(MatchPlayerRating.match_id == match_id, MatchPlayerRating.player_id == player_id)
        .order_by(MatchPlayerRating.created_at.desc(), MatchPlayerRating.id.desc())
    ).all()
    return PlayerRatingDetail(
        summary=player,
        ratings=[
            RatingItem(
                id=row.id,
                stars=row.stars,
                comment=row.comment,
                author_name=(
                    " ".join(part for part in (row.author.first_name, row.author.last_name) if part)
                    or "Club member"
                ),
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
    )


def mine(db: Session, match_id: UUID, player_id: UUID, user: User) -> MyRating | None:
    summary(db, match_id, player_id)
    rating = db.scalar(
        select(MatchPlayerRating).where(
            MatchPlayerRating.match_id == match_id,
            MatchPlayerRating.player_id == player_id,
            MatchPlayerRating.user_id == user.id,
        )
    )
    return MyRating(stars=rating.stars, comment=rating.comment) if rating else None


def save(db: Session, match_id: UUID, player_id: UUID, user: User, body: RatingInput):
    summary(db, match_id, player_id)
    rating = db.scalar(
        select(MatchPlayerRating).where(
            MatchPlayerRating.match_id == match_id,
            MatchPlayerRating.player_id == player_id,
            MatchPlayerRating.user_id == user.id,
        )
    )
    if rating is None:
        rating = MatchPlayerRating(match_id=match_id, player_id=player_id, user_id=user.id)
        db.add(rating)
    rating.stars = body.stars
    rating.comment = body.comment
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            409, "Your rating was saved in another request; please retry"
        ) from error


def delete(db: Session, match_id: UUID, player_id: UUID, user: User):
    summary(db, match_id, player_id)
    rating = db.scalar(
        select(MatchPlayerRating).where(
            MatchPlayerRating.match_id == match_id,
            MatchPlayerRating.player_id == player_id,
            MatchPlayerRating.user_id == user.id,
        )
    )
    if rating is None:
        raise HTTPException(404, "Your rating was not found")
    db.delete(rating)
    db.commit()
