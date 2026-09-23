from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class SearchType(StrEnum):
    URL = "url"
    EMAIL = "email"
    EMAIL_DOMAIN = "email_domain"
    USERNAME = "username"
    PASSWORD = "password"
    IP = "ip"


class DataType(StrEnum):
    STEALERLOG = "stealerlog"
    COMBO = "combo"


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Hit(APIModel):
    id: str
    data_type: str = Field(alias="dataType")
    origin: str
    login: str
    password: str
    source: str
    time_ingested: str = Field(default="", alias="timeIngested")
    time_posted: str = Field(default="", alias="timePosted")


class SearchResponse(APIModel):
    hits: list[Hit] = Field(default_factory=list)


class Credential(APIModel):
    origin: str
    login: str
    password: str
    file: str = ""
    category: str = ""
    tags: list[str] = Field(default_factory=list)
    host: str = ""
    reused: bool = False
    reuse_count: int = Field(default=0, alias="reuseCount")


class Cookie(APIModel):
    domain: str
    path: str
    name: str
    value: str
    expires: int = 0
    secure: bool = False
    expired: bool = False
    file: str = ""


class File(APIModel):
    name: str
    path: str
    size: int | None = None
    type: str
    hash: str = ""
    content: str = ""


class CredentialsResponse(APIModel):
    kind: str = ""
    count: int
    page: int
    has_next: bool = Field(alias="hasNext")
    has_prev: bool = Field(alias="hasPrev")
    items: list[Credential] = Field(default_factory=list)


class CookiesResponse(APIModel):
    kind: str = ""
    count: int
    page: int
    has_next: bool = Field(alias="hasNext")
    has_prev: bool = Field(alias="hasPrev")
    items: list[Cookie] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)


class FilesResponse(APIModel):
    kind: str = ""
    count: int
    page: int
    has_next: bool = Field(alias="hasNext")
    has_prev: bool = Field(alias="hasPrev")
    items: list[File] = Field(default_factory=list)


class SearchLimits(APIModel):
    searches_per_day: int = Field(alias="searchesPerDay")
    searches_used: int = Field(alias="searchesUsed")
    searches_remaining: int = Field(alias="searchesRemaining")
    resets_at: str = Field(alias="resetsAt")


class Account(APIModel):
    plan: str
    plan_name: str = Field(alias="planName")
    active: bool
    expires_at: str = Field(alias="expiresAt")
    days_left: int = Field(alias="daysLeft")
    limits: SearchLimits
