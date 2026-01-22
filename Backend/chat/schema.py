from pydantic import BaseModel, Field
from typing import Optional, List

class ChatMessageRequest(BaseModel):
    message: str = Field(
        ...,
        description="User question for the PDF-based chat"
    )

    # Optional — future-proofing (safe to ignore for now)
    stream: bool = Field(
        default=True,
        description="Whether response should be streamed token by token"
    )