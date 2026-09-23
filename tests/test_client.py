from __future__ import annotations

import asyncio

import httpx
import pytest

from stealerlogs import (
    APIError,
    AsyncClient,
    Client,
    InvalidAPIKeyError,
    InvalidRequestError,
    NotFoundError,
    SearchType,
)

ACCOUNT = {
    "plan": "access",
    "planName": "Access",
    "active": True,
    "expiresAt": "2026-10-22T18:00:00.000Z",
    "daysLeft": 29,
    "limits": {
        "searchesPerDay": 1000,
        "searchesUsed": 12,
        "searchesRemaining": 988,
        "resetsAt": "2026-09-24T00:00:00.000Z",
    },
}


def make_client(respond) -> tuple[Client, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return respond(request)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return Client("sl_test_key", http=http), seen


def test_me() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/me"
        assert request.url.query == b""
        assert request.headers["Authorization"] == "Bearer sl_test_key"
        return httpx.Response(200, json=ACCOUNT)

    sl, _ = make_client(respond)
    account = sl.me()
    assert account.plan == "access"
    assert account.plan_name == "Access"
    assert account.active is True
    assert account.expires_at == "2026-10-22T18:00:00.000Z"
    assert account.days_left == 29
    assert account.limits.searches_per_day == 1000
    assert account.limits.searches_used == 12
    assert account.limits.searches_remaining == 988
    assert account.limits.resets_at == "2026-09-24T00:00:00.000Z"


def test_search_sends_flags_and_parses_hits() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/search"
        assert request.headers["Authorization"] == "Bearer sl_test_key"
        assert request.url.params["q"] == "example@example.com"
        assert request.url.params["type"] == "email"
        assert request.url.params["regex"] == "1"
        assert request.url.params["files"] == "1"
        return httpx.Response(
            200,
            json={
                "hits": [
                    {
                        "id": "file_abc123",
                        "dataType": "stealerlog",
                        "origin": "https://accounts.google.com",
                        "login": "example@example.com",
                        "password": "Summer2024!",
                        "source": "@cloudlogs",
                        "timeIngested": "2026-09-18T14:22:03Z",
                        "timePosted": "2026-09-18T14:22:03Z",
                    }
                ]
            },
        )

    sl, _ = make_client(respond)
    resp = sl.search(
        "example@example.com",
        type=SearchType.EMAIL,
        regex=True,
        files=True,
    )
    assert len(resp.hits) == 1
    assert resp.hits[0].id == "file_abc123"
    assert resp.hits[0].data_type == "stealerlog"


def test_search_validation() -> None:
    with Client("key") as sl:
        with pytest.raises(InvalidRequestError, match="query is required"):
            sl.search("", type="email")
        with pytest.raises(InvalidRequestError, match="type is required"):
            sl.search("x", type="")


def test_credentials() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/logs/abc/credentials"
        assert request.url.params["page"] == "2"
        return httpx.Response(
            200,
            json={
                "kind": "credentials",
                "count": 318,
                "page": 2,
                "hasNext": True,
                "hasPrev": True,
                "items": [
                    {
                        "origin": "https://accounts.google.com",
                        "login": "user@gmail.com",
                        "password": "secret",
                        "file": "passwords.txt",
                        "category": "personal",
                        "tags": ["signin"],
                        "host": "accounts.google.com",
                        "reused": True,
                        "reuseCount": 3,
                    }
                ],
            },
        )

    sl, _ = make_client(respond)
    resp = sl.credentials("abc", page=2)
    assert resp.count == 318
    assert resp.has_next is True
    assert resp.has_prev is True
    assert resp.items[0].reuse_count == 3


def test_cookies() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/logs/abc/cookies"
        assert request.url.params["page"] == "1"
        assert request.url.params["domains"] == ".youtube.com,.google.com"
        assert request.url.params["hide_expired"] == "1"
        return httpx.Response(
            200,
            json={
                "kind": "cookies",
                "count": 4806,
                "page": 1,
                "hasNext": True,
                "hasPrev": False,
                "items": [
                    {
                        "domain": ".youtube.com",
                        "path": "/",
                        "name": "PREF",
                        "value": "1",
                        "expires": 1824273462,
                        "secure": True,
                        "expired": False,
                        "file": "Cookies/Chrome.txt",
                    }
                ],
                "domains": [".youtube.com", ".google.com"],
            },
        )

    sl, _ = make_client(respond)
    resp = sl.cookies(
        "abc",
        page=1,
        domains=[".youtube.com", ".google.com"],
        hide_expired=True,
    )
    assert resp.count == 4806
    assert len(resp.items) == 1
    assert len(resp.domains) == 2


def test_files_and_content() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/logs/abc/files":
            return httpx.Response(
                200,
                json={
                    "kind": "files",
                    "count": 1,
                    "page": 1,
                    "hasNext": False,
                    "hasPrev": False,
                    "items": [
                        {
                            "name": "Chrome.txt",
                            "path": "Autofill/Chrome.txt",
                            "size": None,
                            "type": "txt",
                            "hash": "",
                            "content": "",
                        }
                    ],
                },
            )
        assert request.url.path == "/api/logs/abc/content"
        assert request.url.params["path"] == "Autofill/Chrome.txt"
        return httpx.Response(
            200,
            json={
                "name": "Chrome.txt",
                "path": "Autofill/Chrome.txt",
                "size": 12,
                "type": "txt",
                "hash": "",
                "content": "name: value",
            },
        )

    sl, _ = make_client(respond)
    files = sl.files("abc")
    assert files.items[0].path == "Autofill/Chrome.txt"
    assert files.items[0].size is None

    content = sl.content("abc", "Autofill/Chrome.txt")
    assert content.content == "name: value"
    assert content.size == 12


def test_unauthorized() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "A valid API key is required."})

    sl, _ = make_client(respond)
    with pytest.raises(InvalidAPIKeyError):
        sl.search("a@b.c", type="email")


def test_missing_query() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "Missing q."})

    sl, _ = make_client(respond)
    with pytest.raises(APIError) as exc:
        sl.search("x", type="email")
    assert exc.value.status == 400
    assert str(exc.value) == "Missing q."


def test_not_found() -> None:
    def respond(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "Document not found."})

    sl, _ = make_client(respond)
    with pytest.raises(NotFoundError, match="Document not found."):
        sl.credentials("missing")


def test_async_search() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/search"
        return httpx.Response(200, json={"hits": []})

    http = httpx.AsyncClient(transport=httpx.MockTransport(respond))

    async def run() -> None:
        async with AsyncClient("sl_test_key", http=http) as sl:
            resp = await sl.search("example@example.com", type="email")
            assert resp.hits == []

    asyncio.run(run())


def test_async_me() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/me"
        return httpx.Response(200, json=ACCOUNT)

    http = httpx.AsyncClient(transport=httpx.MockTransport(respond))

    async def run() -> None:
        async with AsyncClient("sl_test_key", http=http) as sl:
            account = await sl.me()
            assert account.plan == "access"
            assert account.limits.searches_remaining == 988

    asyncio.run(run())
