from typing import Any, Self

from pydantic import BaseModel, Field


class ConciergeResponse(BaseModel):
    message: str = Field(description="Reply to the guest in their language.")

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        **kwargs: Any,
    ) -> Self:
        if not json_data or not str(json_data).strip():
            return cls(message="")
        return super().model_validate_json(json_data, **kwargs)
