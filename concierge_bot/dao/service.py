from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from concierge_bot.dao.base import BaseDAO
from concierge_bot.db.models import Service
from concierge_bot.dto import ServiceDTO


class ServiceDao(BaseDAO[Service]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Service, session)

    async def get_by_id(self, service_id: UUID) -> ServiceDTO | None:
        row = await self._get_by_id(service_id)
        return ServiceDTO.model_validate(row) if row else None

    async def get_active_by_hotel(self, hotel_id: UUID) -> list[ServiceDTO]:
        result = await self.session.scalars(
            select(Service).where(
                Service.hotel_id == hotel_id,
                Service.is_active.is_(True),
            ),
        )
        return [ServiceDTO.model_validate(r) for r in result.all()]

    async def get_by_category(self, hotel_id: UUID, category: str) -> list[ServiceDTO]:
        result = await self.session.scalars(
            select(Service).where(
                Service.hotel_id == hotel_id,
                Service.category == category,
            ),
        )
        return [ServiceDTO.model_validate(r) for r in result.all()]

    async def search(self, hotel_id: UUID, query: str) -> list[ServiceDTO]:
        pattern = f"%{query}%"
        result = await self.session.scalars(
            select(Service).where(
                Service.hotel_id == hotel_id,
                or_(
                    Service.name.ilike(pattern),
                    Service.description.ilike(pattern),
                ),
            ),
        )
        return [ServiceDTO.model_validate(r) for r in result.all()]

    async def create(self, **kwargs: object) -> ServiceDTO:
        service = Service(**kwargs)  # type: ignore[arg-type]
        self._save(service)
        await self._flush()
        return ServiceDTO.model_validate(service)

    async def update(self, service_id: UUID, **kwargs: object) -> ServiceDTO:
        service = await self._get_by_id(service_id)
        if service is None:
            msg = f"Service {service_id} not found"
            raise ValueError(msg)  # dao-raise-ok: guard when service id missing in update
        for k, v in kwargs.items():
            setattr(service, k, v)
        await self._flush()
        return ServiceDTO.model_validate(service)

    async def delete(self, service_id: UUID) -> None:
        service = await self._get_by_id(service_id)
        if service is None:
            msg = f"Service {service_id} not found"
            raise ValueError(msg)  # dao-raise-ok: guard when service id missing in delete
        await self._delete(service)
        await self._flush()
