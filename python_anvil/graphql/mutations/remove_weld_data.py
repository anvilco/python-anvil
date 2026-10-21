def generate_mutation() -> str:
    return """
  mutation RemoveWeldData (
    $eid: String!,
  ) {
    removeWeldData (
      eid: $eid,
    )
  }"""
