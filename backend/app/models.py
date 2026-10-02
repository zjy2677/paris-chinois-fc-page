import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Identity:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Team(Identity, Base):
    __tablename__ = "teams"
    fla_team_id: Mapped[int | None] = mapped_column(unique=True)
    name: Mapped[str] = mapped_column(String(200))
    short_name: Mapped[str | None] = mapped_column(String(50))
    logo_url: Mapped[str | None] = mapped_column(Text)


class CompetitionSeason(Identity, Base):
    __tablename__ = "competition_seasons"
    __table_args__ = (
        UniqueConstraint("fla_championship_id", "fla_season_id"),
        UniqueConstraint("fla_cup_id", "fla_season_id", name="uq_cup_season"),
        CheckConstraint(
            "NOT (fla_championship_id IS NOT NULL AND fla_cup_id IS NOT NULL)",
            name="one_competition_source",
        ),
    )
    fla_championship_id: Mapped[int | None]
    fla_cup_id: Mapped[int | None]
    fla_season_id: Mapped[int]
    competition_name: Mapped[str] = mapped_column(String(200))
    division: Mapped[str] = mapped_column(String(100))
    season_label: Mapped[str] = mapped_column(String(20))


class Venue(Identity, Base):
    __tablename__ = "venues"
    __table_args__ = (UniqueConstraint("name", "address"),)
    name: Mapped[str] = mapped_column(String(250))
    address: Mapped[str] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Paris")


class Match(Identity, Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("competition_season_id", "source_key"),
        CheckConstraint("home_team_id <> away_team_id", name="different_teams"),
        CheckConstraint("home_score IS NULL OR home_score >= 0", name="home_score_nonnegative"),
        CheckConstraint("away_score IS NULL OR away_score >= 0", name="away_score_nonnegative"),
        CheckConstraint("(home_score IS NULL) = (away_score IS NULL)", name="paired_scores"),
        CheckConstraint("status <> 'final' OR home_score IS NOT NULL", name="final_has_score"),
        CheckConstraint(
            "status IN ('scheduled','final','postponed','cancelled','unknown')", name="match_status"
        ),
        CheckConstraint("source_type IN ('synced','manual')", name="match_source_type"),
        Index("ix_matches_competition_kickoff", "competition_season_id", "kickoff_at"),
    )
    competition_season_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("competition_seasons.id"))
    source_key: Mapped[str] = mapped_column(String(200))
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    venue_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("venues.id"), index=True)
    matchday: Mapped[int | None]
    leg: Mapped[str] = mapped_column(String(200))
    kickoff_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20))
    home_score: Mapped[int | None]
    away_score: Mapped[int | None]
    source_url: Mapped[str] = mapped_column(Text)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(String(20), default="synced", server_default="synced")


class MatchReport(Identity, Base):
    __tablename__ = "match_reports"
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MatchEvent(Identity, Base):
    __tablename__ = "match_events"
    __table_args__ = (
        CheckConstraint("event_type IN ('goal','yellow_card','red_card')", name="event_type"),
        CheckConstraint("minute IS NULL OR minute BETWEEN 0 AND 130", name="event_minute"),
        CheckConstraint(
            "event_type = 'goal' OR assist_player_id IS NULL", name="assist_only_for_goal"
        ),
        CheckConstraint("player_id <> assist_player_id", name="scorer_not_assistant"),
        Index("ix_match_events_match_sequence", "match_id", "sequence"),
    )
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(20))
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT")
    )
    assist_player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT")
    )
    minute: Mapped[int | None]
    sequence: Mapped[int]


class MatchGoal(Identity, Base):
    __tablename__ = "match_goals"
    __table_args__ = (
        CheckConstraint("goal_type IN ('regular','penalty','own_goal')", name="goal_type_valid"),
        CheckConstraint("minute IS NULL OR minute >= 0", name="goal_minute_valid"),
        CheckConstraint(
            "stoppage_minute IS NULL OR (minute IS NOT NULL AND stoppage_minute > 0)",
            name="goal_stoppage_valid",
        ),
        CheckConstraint("scorer_id <> assist_player_id", name="goal_different_players"),
        CheckConstraint(
            "goal_type <> 'own_goal' OR assist_player_id IS NULL", name="own_goal_no_assist"
        ),
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), index=True
    )
    scorer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"), index=True
    )
    assist_player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="RESTRICT"), index=True
    )
    minute: Mapped[int | None]
    stoppage_minute: Mapped[int | None]
    goal_type: Mapped[str] = mapped_column(String(20), default="regular", server_default="regular")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    scorer: Mapped["Player | None"] = relationship(foreign_keys=[scorer_id])
    assist_player: Mapped["Player | None"] = relationship(foreign_keys=[assist_player_id])


class SyncRun(Identity, Base):
    __tablename__ = "sync_runs"
    dataset: Mapped[str] = mapped_column(String(30))
    source_url: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20))
    inserted_count: Mapped[int] = mapped_column(default=0)
    updated_count: Mapped[int] = mapped_column(default=0)
    error_summary: Mapped[str | None] = mapped_column(Text)


class StandingsSnapshot(Identity, Base):
    __tablename__ = "standings_snapshots"
    competition_season_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("competition_seasons.id"), index=True
    )
    sync_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sync_runs.id"), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    content_hash: Mapped[str] = mapped_column(String(64))


class StandingsRow(Base):
    __tablename__ = "standings_rows"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "position"),
        CheckConstraint("played = wins + draws + losses", name="played_total"),
        CheckConstraint(
            "position > 0 AND played >= 0 AND wins >= 0 AND draws >= 0 AND losses >= 0",
            name="valid_standing_counts",
        ),
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("standings_snapshots.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), primary_key=True, index=True)
    position: Mapped[int]
    played: Mapped[int]
    wins: Mapped[int]
    draws: Mapped[int]
    losses: Mapped[int]
    goal_difference: Mapped[int]
    points: Mapped[int]


class Player(Identity, Base):
    __tablename__ = "players"
    display_name: Mapped[str] = mapped_column(String(150))
    photo_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)


class SquadMembership(Identity, Base):
    __tablename__ = "squad_memberships"
    __table_args__ = (
        UniqueConstraint("player_id", "season_label"),
        UniqueConstraint("season_label", "shirt_number"),
        CheckConstraint(
            "position IN ('Goalkeepers','Defenders','Midfielders','Forwards')",
            name="player_position",
        ),
        CheckConstraint("shirt_number IS NULL OR shirt_number > 0", name="shirt_positive"),
    )
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"), index=True)
    season_label: Mapped[str] = mapped_column(String(20))
    shirt_number: Mapped[int | None]
    position: Mapped[str] = mapped_column(String(30))


class ContactMessage(Identity, Base):
    __tablename__ = "contact_messages"
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HomepageLike(Identity, Base):
    __tablename__ = "homepage_likes"
    __table_args__ = (UniqueConstraint("visitor_hash", name="uq_homepage_like_visitor"),)

    visitor_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BlogPost(Identity, Base):
    __tablename__ = "blog_posts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','pending','published','rejected')", name="blog_post_status"
        ),
        Index("ix_blog_posts_status_published", "status", "published_at"),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(180))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GuestbookMessage(Identity, Base):
    __tablename__ = "guestbook_messages"
    __table_args__ = (
        CheckConstraint("status IN ('visible','hidden')", name="guestbook_message_status"),
        Index("ix_guestbook_status_created", "status", "created_at"),
    )

    nickname: Mapped[str] = mapped_column(String(30))
    body: Mapped[str] = mapped_column(String(300))
    visitor_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="visible", server_default="visible")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Accounts and revocable authentication sessions.
class User(Identity, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'player', 'admin')", name="user_role"),
        CheckConstraint("age_at_registration BETWEEN 1 AND 120", name="user_age"),
    )
    first_name: Mapped[str | None] = mapped_column(String(80))
    last_name: Mapped[str | None] = mapped_column(String(80))
    age_at_registration: Mapped[int | None] = mapped_column(Integer)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    normalized_email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="user", server_default="user")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    avatar: Mapped["UserAvatar | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserAvatar(Identity, Base):
    __tablename__ = "user_avatars"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    content_type: Mapped[str] = mapped_column(String(50))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    user: Mapped[User] = relationship(back_populates="avatar")


class SessionToken(Identity, Base):
    __tablename__ = "sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AccountToken(Identity, Base):
    __tablename__ = "account_tokens"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(30))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MatchVideo(Identity, Base):
    __tablename__ = "match_videos"
    __table_args__ = (
        CheckConstraint("size_bytes > 0", name="video_size_positive"),
        CheckConstraint(
            "(video_url IS NOT NULL AND object_key IS NULL) OR (video_url IS NULL AND object_key IS NOT NULL AND uploaded_by IS NOT NULL AND content_type IS NOT NULL AND size_bytes IS NOT NULL)",
            name="video_source",
        ),
        UniqueConstraint("match_id", "video_url", name="uq_match_video_url"),
        CheckConstraint("status IN ('pending','ready','failed')", name="video_status"),
        Index("ix_video_match_status", "match_id", "status"),
    )
    match_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("matches.id", ondelete="RESTRICT"))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    video_url: Mapped[str | None] = mapped_column(Text)
    object_key: Mapped[str | None] = mapped_column(Text, unique=True)
    title: Mapped[str | None] = mapped_column(String(200))
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
