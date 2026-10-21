"""The client's GraphQL operations: the queries and mutations it sends.

These match node-anvil's `src/graphql/` exactly, variable names and default
response fields included. Pass your own response query to select other
fields, or your own whole operation.
"""

from python_anvil.graphql import mutations, queries


__all__ = ["mutations", "queries"]
