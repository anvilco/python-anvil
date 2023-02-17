## Dynamic query building with `gql`

This library makes use of [`graphql-python/gql`](https://github.com/graphql-python/gql) as its GraphQL client
implementation. This allows us to have a simpler interface when interacting with Anvil's GraphQL API. This also gives us
the ability to use gql's dynamic query
builder. [More info on their documentation page](https://gql.readthedocs.io/en/latest/advanced/dsl_module.html).

We have a few helper functions to help generate your first dynamic query. These are shown in the example below.
Keep in mind that your IDE will likely not be able to autocomplete any field lookups, so it may help to also
have [Anvil's GraphQL reference page](https://www.useanvil.com/docs/api/graphql/reference/) open as you create your
queries.

### Example usage

```python
from gql.dsl import DSLQuery, dsl_gql

from python_anvil.api import Anvil
from python_anvil.http import get_gql_ds

# These steps are similar to `gql's` docs on dynamic queries with Anvil helper functions.
# https://gql.readthedocs.io/en/latest/advanced/dsl_module.html

anvil = Anvil(api_key=MY_API_KEY)

# Use `ds` to create your queries
ds = get_gql_ds(anvil.gql_client)

# Create your query in one step
query = ds.Query.currentUser.select(
    ds.User.name,
    ds.User.email,
)

# Or, build your query with a chain or multiple steps until you're ready to use it.
query = ds.Query.currentUser.select(ds.User.name)
query.select(ds.User.email)
query.select(ds.User.firstName)
query.select(ds.User.lastName)

# Once your root query fields are defined, you can put them in an operation using DSLQuery, DSLMutation or DSLSubscription:
final_query = dsl_gql(DSLQuery(query))

res = anvil.query(final_query)
```
