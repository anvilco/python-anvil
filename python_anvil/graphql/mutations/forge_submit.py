from python_anvil.graphql.selection import selection


DEFAULT_RESPONSE_QUERY = """{
  id
  eid
  status
  continueURL
  payloadValue
  currentStep
  completedAt
  createdAt
  updatedAt
  signer {
    name
    email
    status
    routingOrder
  }
  weldData {
    eid
    isTest
    isComplete
    agents
  }
}"""


def generate_mutation(response_query: str | None = None) -> str:
    response_query = selection(response_query)
    return f"""
  mutation ForgeSubmit(
    $forgeEid: String!,
    $weldDataEid: String,
    $submissionEid: String,
    $payload: JSON!,
    $enforcePayloadValidOnCreate: Boolean,
    $currentStep: Int,
    $complete: Boolean,
    $isTest: Boolean,
    $timezone: String,
    $webhookURL: String,
    $groupArrayId: String,
    $groupArrayIndex: Int
  ) {{
    forgeSubmit(
      forgeEid: $forgeEid,
      weldDataEid: $weldDataEid,
      submissionEid: $submissionEid,
      payload: $payload,
      enforcePayloadValidOnCreate: $enforcePayloadValidOnCreate,
      currentStep: $currentStep,
      complete: $complete,
      isTest: $isTest,
      timezone: $timezone,
      webhookURL: $webhookURL,
      groupArrayId: $groupArrayId,
      groupArrayIndex: $groupArrayIndex
    ) {response_query or DEFAULT_RESPONSE_QUERY}
  }}"""
