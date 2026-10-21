"""The errors the client raises, and how API error responses become them.

REST and GraphQL error responses come in several shapes. They are all
normalized into a list of dicts that each have a `message`, a `name`, or both,
and which keep whatever else the API said, like a validation error's `fields`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    import requests


class AnvilError(Exception):
    """Base class for every error this library raises on purpose."""


class AnvilRequestError(AnvilError):
    """The API responded, but with an error.

    :ivar errors: The normalized errors. Each has a `message`, a `name`, or
        both. GraphQL errors also have `path` and `locations`; REST validation
        errors have `fields`, each with a `message` and `property`.
    :ivar status_code: The HTTP status code. GraphQL errors usually come
        with a 200.
    :ivar headers: The response headers, e.g. for the rate limit headers.
    :ivar data: Any data the API returned alongside the errors. A GraphQL
        response can be partially successful.
    :ivar response: The `requests.Response`, if the error came from one.
    """

    def __init__(
        self,
        errors: list[dict[str, Any]],
        *,
        status_code: int,
        headers: Mapping[str, str] | None = None,
        data: Any = None,
        response: requests.Response | None = None,
    ):
        self.errors = errors
        self.status_code = status_code
        self.headers: Mapping[str, str] = headers or {}
        self.data = data
        self.response = response
        super().__init__(f"{status_code}: {'; '.join(format_error(e) for e in errors)}")

    @property
    def message(self) -> str:
        """The first error's message."""
        return format_error(self.errors[0]) if self.errors else "Unknown Error"


def format_error(error: Mapping[str, Any]) -> str:
    """One line describing a normalized error, including any field details."""
    parts = [str(part) for part in (error.get("name"), error.get("message")) if part]
    description = ": ".join(parts) if parts else "Unknown Error"

    fields = error.get("fields")
    if isinstance(fields, list) and fields:
        details = ", ".join(
            f"{field.get('property')}: {field.get('message')}"
            if field.get("property")
            else str(field.get("message"))
            for field in fields
            if isinstance(field, Mapping)
        )
        if details:
            description = f"{description} ({details})"

    return description


def looks_like_json_error(json: Any) -> bool:
    """Whether a JSON response body is an error, whatever its status code."""
    return isinstance(json, Mapping) and bool(
        json.get("errors") or json.get("message") or json.get("name")
    )


def normalize_json_errors(
    json: Any, status_text: str = "Unknown Error"
) -> list[dict[str, Any]]:
    """Normalize a JSON error response into a list of errors."""
    if isinstance(json, Mapping):
        # Normal, GraphQL way
        errors = json.get("errors")
        if isinstance(errors, list) and errors:
            return [
                dict(error) if isinstance(error, Mapping) else {"message": str(error)}
                for error in errors
            ]

        # Alternative way from some REST calls:
        # {
        #   "name": "AssertionError",
        #   "message": "PDF did not generate properly from given HTML!"
        # }
        #
        # OR
        #
        # {
        #   "name": "ValidationError",
        #   "fields":[{ "message": "Required", "property": "data" }]
        # }
        if json.get("message") or json.get("name"):
            return [dict(json)]

    # Hmm, ok. Default way
    status_text = status_text or "Unknown Error"
    return [{"name": status_text, "message": status_text}]


def normalize_exception(
    error: BaseException | None, status_text: str = "Unknown Error"
) -> list[dict[str, Any]]:
    """Normalize an exception, like a JSON parsing error, into a list of errors."""
    if error is not None:
        return [{"name": type(error).__name__, "message": str(error)}]

    status_text = status_text or "Unknown Error"
    return [{"name": status_text, "message": status_text}]
