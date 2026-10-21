from __future__ import annotations

from typing import Any


class BaseQuery:
    """Base class for the classes that build a GraphQL mutation and its variables."""

    def get_mutation(self, response_query: str | None = None) -> str:
        """The mutation to send, selecting `response_query` or the default fields."""
        raise NotImplementedError

    def create_payload(self) -> Any:
        """The model whose dump is the mutation's variables."""
        raise NotImplementedError
