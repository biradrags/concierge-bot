from concierge_bot.dto import HotelDTO


def build_system_prompt(hotel: HotelDTO) -> str:
    extra = (hotel.system_prompt or "").strip()
    base = (
        f"You are an AI concierge for {hotel.name}.\n"
        "You help guests find and book services: restaurants, tours, transport, spa.\n"
        "Be friendly, concise, respond in the guest's language.\n"
        "Use tools search_services and create_booking when the guest wants to find or book.\n"
    )
    if extra:
        base += f"\nHotel-specific instructions:\n{extra}\n"
    return base
