from typing import Any

from pydantic import BaseModel, Field


class ConciergeResponse(BaseModel):
    message: str = Field(description="Reply to the guest in their language.")

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: Any = None,
    ) -> "ConciergeResponse":
        if not json_data or not str(json_data).strip():
            return cls(message="")
        return super().model_validate_json(json_data, strict=strict, context=context)
