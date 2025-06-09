import datetime as dt
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

UTC = dt.timezone(dt.timedelta(0), "UTC")


def now_utc() -> dt.datetime:
    return dt.datetime.now(tz=UTC)


class Base(DeclarativeBase, AsyncAttrs):
    __abstract__ = True


class ZonedDateTime(TypeDecorator):
    """For SQLite to have fake timezone support."""

    impl = DateTime
    cache_ok = True
    LOCAL_TIMEZONE = dt.datetime.now().astimezone().tzinfo

    def process_bind_param(self, value: dt.datetime, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            # value = value.astimezone(self.LOCAL_TIMEZONE)
            value = value.astimezone(dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if value.tzinfo is None:
            return value.replace(tzinfo=dt.timezone.utc)
        return value.astimezone(dt.timezone.utc)


class TrackingBase(Base):
    __abstract__ = True

    uid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    created: Mapped[dt.datetime] = mapped_column(
        ZonedDateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated: Mapped[dt.datetime] = mapped_column(
        ZonedDateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def created_age(self) -> dt.timedelta:
        return now_utc() - self.created

    @property
    def updated_age(self) -> dt.timedelta:
        return now_utc() - self.updated

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(uid={self.uid},"
            f" c={self.created.strftime('%Y.%m.%d %H:%M')})"
        )


class User(TrackingBase):
    __tablename__ = "users"

    username: Mapped[str | None] = mapped_column(
        String(length=32), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    lang: Mapped[str] = mapped_column(String(length=8), nullable=False)
    photo_url: Mapped[str] = mapped_column(
        String(length=128), nullable=True, default=None
    )

    source: Mapped[str | None] = mapped_column(
        String, index=True, default=None, nullable=True
    )
    referrer_uid: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uid"),
        index=True,
        default=None,
        nullable=True,
    )
    referrer = relationship("User", remote_side="users.c.uid", backref="referred")


class GameMatch(TrackingBase):
    __tablename__ = "gamematch"

    player_1_uid: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(User.uid), nullable=False
    )
    player_1: Mapped[User] = relationship(foreign_keys=[player_1_uid])

    player_2_uid: Mapped[uuid.UUID] = mapped_column(ForeignKey(User.uid), nullable=True)
    player_2: Mapped[User] = relationship(foreign_keys=[player_2_uid])

    bet_coin_amount: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    finished: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    player_1_win: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    player_2_win: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
