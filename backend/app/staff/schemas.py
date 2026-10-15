from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

StaffRole = Literal["admin", "officer"]


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)


class StaffUserOut(BaseModel):
    id: int
    email: str
    name: str
    role: StaffRole


class StaffUserListItem(StaffUserOut):
    active: bool
    last_login_at: datetime | None


class StaffUserListResponse(BaseModel):
    items: list[StaffUserListItem]
