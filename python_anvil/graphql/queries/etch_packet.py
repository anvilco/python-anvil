from python_anvil.graphql.selection import selection


DEFAULT_RESPONSE_QUERY = """{
  id
  eid
  name
  status
  isTest
  numberRemainingSigners
  webhookURL
  detailsURL
  completedAt
  archivedAt
  createdAt
  updatedAt
  documentGroup {
    eid
    status
    files
    signers {
      id
      eid
      aliasId
      routingOrder
      name
      email
      status
      signActionType
    }
  }
}"""


def generate_query(response_query: str | None = None) -> str:
    response_query = selection(response_query)
    return f"""
  query EtchPacket (
    $eid: String!,
  ) {{
    etchPacket (
      eid: $eid,
    ) {response_query or DEFAULT_RESPONSE_QUERY}
  }}
"""
