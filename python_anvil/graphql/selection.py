"""The response fields of an operation, with the braces a caller may leave out."""

from __future__ import annotations


def selection(response_query: str | None) -> str | None:
    """`"{ eid name }"` for `"eid name"` or `"{ eid name }"`; `None` stays `None`."""
    if response_query is None:
        return None
    fields = response_query.strip()
    if not fields:
        return None
    if fields.startswith("{"):
        return fields
    return f"{{ {fields} }}"
