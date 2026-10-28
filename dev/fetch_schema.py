#!/usr/bin/env python3
"""Refreshes the API specs the generated types come from.

- schema/anvil_schema.graphql, from the published @anvilco/types npm package
  (https://www.npmjs.com/package/@anvilco/types). It ships the Anvil GraphQL
  schema, regenerated from production after every deploy. node-anvil
  validates its operations against that copy, and so does this client:
  using the same source keeps the two clients in step.
- schema/openapi.json, the API's own OpenAPI spec, from production.

Neither needs an API key. Then run `dev/generate_types.py` (`make generate`)
to regenerate python_anvil/types from them.

Usage:
    poetry run python dev/fetch_schema.py [@anvilco/types version]

Defaults to the latest version. On any failure the existing files are untouched.
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
OPENAPI_URL = "https://app.useanvil.com/api/v1/openapi.json"

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
SCHEMA_PATH = SCHEMA_DIR / "anvil_schema.graphql"
OPENAPI_PATH = SCHEMA_DIR / "openapi.json"


def fetch_graphql_schema(version: str = "latest") -> tuple[str, str]:
    """The schema SDL in the given version of @anvilco/types, and that version."""
    metadata_url = f"{REGISTRY}/{PACKAGE.replace('/', '%2F')}"
    with urllib.request.urlopen(metadata_url, timeout=60) as response:
        metadata = json.load(response)

    if version == "latest":
        version = metadata["dist-tags"]["latest"]
    tarball_url = metadata["versions"][version]["dist"]["tarball"]

    with urllib.request.urlopen(tarball_url, timeout=60) as response:
        tarball = response.read()

    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        try:
            member = archive.extractfile(SCHEMA_IN_PACKAGE)
        except KeyError:
            member = None
        if member is None:
            raise FileNotFoundError(
                f"{SCHEMA_IN_PACKAGE} is not in {PACKAGE}@{version}"
            )
        return member.read().decode("utf-8"), version


def fetch_openapi_spec() -> str:
    """The OpenAPI spec, pretty-printed with sorted keys so the diff is only real changes."""
    with urllib.request.urlopen(OPENAPI_URL, timeout=60) as response:
        spec = json.load(response)
    if "openapi" not in spec or "paths" not in spec:
        raise ValueError(f"{OPENAPI_URL} did not return an OpenAPI spec")
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "latest"

    schema, version = fetch_graphql_schema(version)
    openapi = fetch_openapi_spec()

    SCHEMA_PATH.write_text(schema, encoding="utf-8")
    print(
        f"Wrote the GraphQL schema from {PACKAGE}@{version} to {_relative(SCHEMA_PATH)}"
    )
    OPENAPI_PATH.write_text(openapi, encoding="utf-8")
    print(f"Wrote the OpenAPI spec from {OPENAPI_URL} to {_relative(OPENAPI_PATH)}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
