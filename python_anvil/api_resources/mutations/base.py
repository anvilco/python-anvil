from __future__ import annotations

from typing import Any


class BaseQuery:
    """Base class for the classes that build a GraphQL mutation and its variables."""

    # The fields the mutation selects unless `response_query` is given
    default_response_query: str | None = None
    # The same, set on a subclass or instance the way it was before 6.0.0
    mutation_res_query: str | None = None

    def get_mutation(self, response_query: str | None = None) -> str:
        """The mutation to send, selecting `response_query` or the default fields."""
        raise NotImplementedError

    def response_fields(self, response_query: str | None = None) -> str | None:
        return response_query or self.mutation_res_query or self.default_response_query

    def create_payload(self) -> Any:
        """The model whose dump is the mutation's variables."""
        raise NotImplementedError
