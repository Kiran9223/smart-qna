from pydantic import BaseModel
from typing import Literal


class VoteRequest(BaseModel):
    type: Literal["UP", "DOWN"]


class VoteResponse(BaseModel):
    vote_count: int
    user_vote: str | None = None
