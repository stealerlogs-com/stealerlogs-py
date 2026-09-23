from __future__ import annotations


class StealerlogsError(Exception):
    """Base error for the stealerlogs client."""


class InvalidRequestError(StealerlogsError, ValueError):
    """Raised when a request is missing required arguments."""


class InvalidAPIKeyError(StealerlogsError):
    """Raised when the API key is missing or rejected."""


class NotFoundError(StealerlogsError):
    """Raised when a log or file path does not exist."""


class RateLimitError(StealerlogsError):
    """Raised when the API returns HTTP 429."""

    def __init__(self, message: str = "rate limit reached") -> None:
        super().__init__(message)


class ServerError(StealerlogsError):
    """Raised when the API returns an unexpected server failure."""


class APIError(StealerlogsError):
    """Raised for other non-success API responses."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
