def generate_mutation() -> str:
    return """
  mutation GenerateEtchSignURL (
    $signerEid: String!,
    $clientUserId: String!,
  ) {
    generateEtchSignURL (
      signerEid: $signerEid,
      clientUserId: $clientUserId
    )
  }
"""
