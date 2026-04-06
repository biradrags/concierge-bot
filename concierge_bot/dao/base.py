from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption

from concierge_bot.db.base import Base


class BaseDAO[Model_co: Base]:
    def __init__(self, model: type[Model_co], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def _get_all(
        self,
        options: Sequence[ORMOption] = (),
        limit: int | None = None,
    ) -> Sequence[Model_co]:
        q = select(self.model).options(*options)
        if limit is not None:
            q = q.limit(limit)
        result = await self.session.scalars(q)
        return result.all()

    async def _get_by_id(
        self,
        id_: UUID,
        options: Sequence[ORMOption] | None = None,
    ) -> Model_co | None:
        return await self.session.get(
            self.model,
            id_,
            options=options,
        )

    def _save(self, obj: Base) -> None:
        self.session.add(obj)

    async def _delete(self, obj: Base) -> None:
        await self.session.delete(obj)

    async def _delete_by_id(self, id_: UUID) -> None:
        await self.session.execute(delete(self.model).where(self.model.id == id_))

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(self.model.id)))
        return int(result.scalar_one())

    async def commit(self) -> None:
        await self.session.commit()

    async def _flush(self) -> None:
        await self.session.flush()
