#!/usr/bin/env python3
"""Refreshes schema/anvil_schema.graphql from the published @anvilco/types package.

@anvilco/types (https://www.npmjs.com/package/@anvilco/types) ships the Anvil
GraphQL schema, regenerated from production after every deploy. node-anvil
validates its operations against that copy, and so does this client: using
the same source keeps the two clients in step, and needs no API key.

Usage:
    poetry run python dev/fetch_schema.py [version]

Defaults to the latest version. On any failure the existing file is untouched.
"""

from __future__ import annotations

import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path


PACKAGE = "@anvilco/types"
REGISTRY = "https://registry.npmjs.org"
SCHEMA_IN_PACKAGE = "package/schema/anvil-schema.graphql"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "schema" / "anvil_schema.graphql"


def fetch_schema(version: str = "latest") -> tuple[str, str]:
    """The schema SDL in the given version of @anvilco/types, and that version."""
    metadata_url = f"{REGISTRY}/{PACKAGE.replace('/', '%2F')}"
    with urllib.request.urlopen(metadata_url) as response:
        metadata = json.load(response)

    if version == "latest":
        version = metadata["dist-tags"]["latest"]
    tarball_url = metadata["versions"][version]["dist"]["tarball"]

    with urllib.request.urlopen(tarball_url) as response:
        tarball = response.read()

    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        member = archive.extractfile(SCHEMA_IN_PACKAGE)
        if member is None:
            raise FileNotFoundError(
                f"{SCHEMA_IN_PACKAGE} is not in {PACKAGE}@{version}"
            )
        return member.read().decode("utf-8"), version


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "latest"
    schema, version = fetch_schema(version)
    OUTPUT_PATH.write_text(schema)
    print(
        f"Wrote the schema from {PACKAGE}@{version} to {OUTPUT_PATH.relative_to(Path.cwd())}"
    )


if __name__ == "__main__":
    main()
