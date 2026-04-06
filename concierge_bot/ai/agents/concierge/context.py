from dataclasses import dataclass

from aiogram import Bot

from concierge_bot.dao import HolderDao
from concierge_bot.dto import BookingDTO, GuestDTO, HotelDTO
from concierge_bot.services.booking import BookingService


@dataclass(frozen=True)
class ToolDeps:
    hotel: HotelDTO
    guest: GuestDTO
    dao: HolderDao
    booking_service: BookingService
    bot: Bot


@dataclass
class ConciergeState:
    last_booking: BookingDTO | None = None
