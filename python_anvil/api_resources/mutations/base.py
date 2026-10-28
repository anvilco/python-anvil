class BaseQuery:
    """Base class for any GraphQL queries/mutations."""

    mutation: str | None = None
    mutation_res_query: str | None = None

    def get_mutation(self):
        if self.mutation and self.mutation_res_query:
            return self.mutation.format(query=self.mutation_res_query)
        return self.mutation

    def create_payload(self):
        if not self.mutation:
            raise ValueError(
                "`mutation` property must be set on the inheriting class level"
            )
        raise NotImplementedError()
