from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TypeVar
from urllib.parse import quote

import httpx
from pydantic import BaseModel

from stealerlogs.errors import (
    APIError,
    InvalidAPIKeyError,
    InvalidRequestError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from stealerlogs.models import (
    CookiesResponse,
    CredentialsResponse,
    File,
    FilesResponse,
    SearchResponse,
    SearchType,
)

DEFAULT_BASE_URL = "https://stealerlogs.com/api"
DEFAULT_TIMEOUT = 60.0

T = TypeVar("T", bound=BaseModel)


def _page(page: int | None) -> int:
    return 1 if page is None or page < 1 else page


def _error_message(body: str) -> str:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body.strip()
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, str) and error:
            return error
    return body.strip()


def raise_for_status(response: httpx.Response) -> None:
    if response.is_success:
        return

    message = _error_message(response.text)

    if response.status_code == 401:
        raise InvalidAPIKeyError(message or "invalid api key")
    if response.status_code == 429:
        raise RateLimitError(message or "rate limit reached")
    if response.status_code == 404:
        raise NotFoundError(message or "not found")
    if response.status_code == 400:
        raise APIError(400, message or "bad request")
    if not response.text.strip():
        raise ServerError("server returned an error")
    raise APIError(response.status_code, message)


class _RequestBuilder:
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def search_params(
        self,
        query: str,
        search_type: SearchType | str,
        regex: bool,
        files: bool,
    ) -> dict[str, str]:
        if not query:
            raise InvalidRequestError("query is required")
        if not search_type:
            raise InvalidRequestError("type is required")

        params = {"q": query, "type": str(search_type)}
        if regex:
            params["regex"] = "1"
        if files:
            params["files"] = "1"
        return params

    def log_path(self, log_id: str, suffix: str) -> str:
        if not log_id:
            raise InvalidRequestError("log id is required")
        return f"/logs/{quote(log_id, safe='')}/{suffix}"

    def cookie_params(
        self,
        page: int,
        domains: Sequence[str] | None,
        hide_expired: bool,
    ) -> dict[str, str]:
        params = {"page": str(_page(page))}
        if domains:
            params["domains"] = ",".join(domains)
        if hide_expired:
            params["hide_expired"] = "1"
        return params


class Client:
    """Synchronous stealerlogs.com API client."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http: httpx.Client | None = None,
    ) -> None:
        self._builder = _RequestBuilder(api_key, base_url)
        self._owns_http = http is None
        self._http = http or httpx.Client(
            base_url=self._builder.base_url,
            timeout=timeout,
        )

    @property
    def api_key(self) -> str:
        return self._builder.api_key

    @property
    def base_url(self) -> str:
        return self._builder.base_url

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def search(
        self,
        query: str,
        *,
        type: SearchType | str,
        regex: bool = False,
        files: bool = False,
    ) -> SearchResponse:
        params = self._builder.search_params(query, type, regex, files)
        return self._get("/search", params, SearchResponse)

    def credentials(self, log_id: str, *, page: int = 1) -> CredentialsResponse:
        path = self._builder.log_path(log_id, "credentials")
        return self._get(path, {"page": str(_page(page))}, CredentialsResponse)

    def cookies(
        self,
        log_id: str,
        *,
        page: int = 1,
        domains: Sequence[str] | None = None,
        hide_expired: bool = False,
    ) -> CookiesResponse:
        path = self._builder.log_path(log_id, "cookies")
        return self._get(
            path,
            self._builder.cookie_params(page, domains, hide_expired),
            CookiesResponse,
        )

    def files(self, log_id: str, *, page: int = 1) -> FilesResponse:
        path = self._builder.log_path(log_id, "files")
        return self._get(path, {"page": str(_page(page))}, FilesResponse)

    def content(self, log_id: str, path: str) -> File:
        if not path:
            raise InvalidRequestError("path is required")
        url = self._builder.log_path(log_id, "content")
        return self._get(url, {"path": path}, File)

    def _get(self, path: str, params: Mapping[str, str], model: type[T]) -> T:
        response = self._http.get(
            f"{self._builder.base_url}{path}",
            params=params,
            headers=self._builder.headers,
        )
        raise_for_status(response)
        return model.model_validate_json(response.content)


class AsyncClient:
    """Asynchronous stealerlogs.com API client."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self._builder = _RequestBuilder(api_key, base_url)
        self._owns_http = http is None
        self._http = http or httpx.AsyncClient(
            base_url=self._builder.base_url,
            timeout=timeout,
        )

    @property
    def api_key(self) -> str:
        return self._builder.api_key

    @property
    def base_url(self) -> str:
        return self._builder.base_url

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def search(
        self,
        query: str,
        *,
        type: SearchType | str,
        regex: bool = False,
        files: bool = False,
    ) -> SearchResponse:
        params = self._builder.search_params(query, type, regex, files)
        return await self._get("/search", params, SearchResponse)

    async def credentials(self, log_id: str, *, page: int = 1) -> CredentialsResponse:
        path = self._builder.log_path(log_id, "credentials")
        return await self._get(path, {"page": str(_page(page))}, CredentialsResponse)

    async def cookies(
        self,
        log_id: str,
        *,
        page: int = 1,
        domains: Sequence[str] | None = None,
        hide_expired: bool = False,
    ) -> CookiesResponse:
        path = self._builder.log_path(log_id, "cookies")
        return await self._get(
            path,
            self._builder.cookie_params(page, domains, hide_expired),
            CookiesResponse,
        )

    async def files(self, log_id: str, *, page: int = 1) -> FilesResponse:
        path = self._builder.log_path(log_id, "files")
        return await self._get(path, {"page": str(_page(page))}, FilesResponse)

    async def content(self, log_id: str, path: str) -> File:
        if not path:
            raise InvalidRequestError("path is required")
        url = self._builder.log_path(log_id, "content")
        return await self._get(url, {"path": path}, File)

    async def _get(self, path: str, params: Mapping[str, str], model: type[T]) -> T:
        response = await self._http.get(
            f"{self._builder.base_url}{path}",
            params=params,
            headers=self._builder.headers,
        )
        raise_for_status(response)
        return model.model_validate_json(response.content)
