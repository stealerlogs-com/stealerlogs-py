from __future__ import annotations

import os

import pytest

from stealerlogs import Client, InvalidAPIKeyError

API_KEY = os.environ.get("STEALERLOGS_API_KEY")
pytestmark = pytest.mark.skipif(not API_KEY, reason="STEALERLOGS_API_KEY is not set")


def test_empty_search() -> None:
    with Client(API_KEY) as sl:  # type: ignore[arg-type]
        response = sl.search(
            "zzzzzznotfound12345@example.invalid",
            type="email",
        )
        assert response.hits == []


def test_log_endpoints() -> None:
    with Client(API_KEY) as sl:  # type: ignore[arg-type]
        log_id = "3qzOQmky1-6kd1eum5QC"
        creds = sl.credentials(log_id, page=1)
        assert creds.kind == "credentials"
        assert creds.page == 1
        assert creds.items

        cookies = sl.cookies(log_id, page=1, domains=[".youtube.com"], hide_expired=True)
        assert cookies.kind == "cookies"
        assert cookies.domains

        files = sl.files(log_id, page=1)
        assert files.kind == "files"
        if files.items:
            content = sl.content(log_id, files.items[0].path)
            assert content.path == files.items[0].path


def test_me() -> None:
    with Client(API_KEY) as sl:  # type: ignore[arg-type]
        account = sl.me()
        assert account.plan
        assert account.plan_name
        assert account.expires_at
        assert account.days_left >= 0
        assert account.limits.searches_per_day >= 0
        assert account.limits.searches_used >= 0
        assert account.limits.searches_remaining >= 0
        assert account.limits.resets_at


def test_invalid_key() -> None:
    with Client("sl_invalid") as sl:
        with pytest.raises(InvalidAPIKeyError):
            sl.search("a@b.c", type="email")
