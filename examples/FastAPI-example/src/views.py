import uuid

from sqlalchemy import Integer, String, desc, select, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.expression import case, func, literal_column
from src.tables import GameMatch, User

from sqlalchemy_view_orm import ViewBase, ViewConfig

LB_DAYS = 30


def get_leaderboard_select(dialect_name: str):
    if "sqlite" in dialect_name:
        filters = [
            GameMatch.created >= func.date(func.now(), f"-{int(LB_DAYS)} days"),
            GameMatch.finished == True,
        ]
    else:
        filters = [
            GameMatch.created >= func.now() - text(f"INTERVAL '{LB_DAYS} days'"),
            GameMatch.finished == True,
        ]

    q_u1 = select(
        GameMatch.player_1_uid.label("uid"),
        (
            GameMatch.bet_coin_amount
            * case(
                (GameMatch.player_1_win, 1),
                (GameMatch.player_2_win, -1),
                else_=0,
            )
        ).label("bet_coin_amount"),
    ).filter(*filters)

    q_u2 = select(
        GameMatch.player_2_uid.label("uid"),
        (
            GameMatch.bet_coin_amount
            * case(
                (GameMatch.player_1_win, -1),
                (GameMatch.player_2_win, 1),
                else_=0,
            )
        ).label("bet_coin_amount"),
    ).filter(*filters)
    q_ua = q_u1.union_all(q_u2)

    # Group and detail
    q = (
        select(
            literal_column("q_ua.uid").label("uid"),
            func.max(User.name).label("name"),
            func.count().label("match_count"),
            func.sum(literal_column("q_ua.bet_coin_amount")).label("coin_amount"),
        )
        .group_by(literal_column("q_ua.uid"))
        .select_from(q_ua.subquery("q_ua"))
        .join(User, literal_column("q_ua.uid") == User.uid)
    )
    q = q.order_by(text("coin_amount DESC"))

    sub = q.subquery()
    q = select(
        sub,
        func.row_number()
        .over(
            order_by=(
                desc(literal_column("coin_amount")),
                desc(literal_column("match_count")),
            )
        )
        .label("position"),
    )
    return q


class LeaderboardMV(ViewBase):
    __tablename__ = "leaderboard_mv"
    __view_config__ = ViewConfig(
        definer=get_leaderboard_select,
        materialized=True,
        materialized_as_table=True,  # For tests on SQLite
    )

    uid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=64), nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, nullable=False)
    coin_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)

    def __repr__(self):
        return (
            f"{self.__class__.__name__} (#{self.position},"
            f" uid={self.uid}, name={self.name!r},"
            f" coins={self.coin_amount}, count={self.match_count})"
        )


async def create_all_mv(conn: AsyncConnection):
    for view_cls in ViewBase.get_children():
        for cmd in view_cls.get_create_cmds(conn.engine):
            await conn.execute(cmd)


async def drop_all_mv(conn: AsyncConnection):
    for view_cls in ViewBase.get_children():
        for cmd in view_cls.get_drop_cmds(conn.engine):
            await conn.execute(cmd)


async def refresh_all_mv(session: AsyncSession):
    for view_cls in ViewBase.get_children():
        for cmd in view_cls.get_refresh_cmds(session.get_bind()):
            await session.execute(cmd)
