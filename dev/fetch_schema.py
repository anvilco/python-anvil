#!/usr/bin/env python3
"""Refreshes the API specs the generated types come from.

Both come from the published @anvilco/types npm package
(https://www.npmjs.com/package/@anvilco/types):

- schema/anvil_schema.graphql, the Anvil GraphQL schema, which the package has
  always shipped.
- schema/openapi.json, the API's OpenAPI spec, which recent versions of the
  package ship. An older version doesn't have it, so it is fetched from
  production instead.

The package is regenerated from production after every deploy, and node-anvil
and dotnet-anvil generate their types from the same copy, so every client
describes the same API build. Neither file needs an API key. Then run
`dev/generate_types.py` (`make generate`) to regenerate python_anvil/types.

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
OPENAPI_IN_PACKAGE = "package/schema/openapi.json"
OPENAPI_URL = "https://app.useanvil.com/api/v1/openapi.json"

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
SCHEMA_PATH = SCHEMA_DIR / "anvil_schema.graphql"
OPENAPI_PATH = SCHEMA_DIR / "openapi.json"


def fetch_specs(version: str = "latest") -> tuple[str, str | None, str]:
    """The specs in the given version of @anvilco/types, and that version.

    The GraphQL schema SDL, and the OpenAPI spec or None when the version
    predates the spec shipping in the package.
    """
    metadata_url = f"{REGISTRY}/{PACKAGE.replace('/', '%2F')}"
    with urllib.request.urlopen(metadata_url, timeout=60) as response:
        metadata = json.load(response)

    if version == "latest":
        version = metadata["dist-tags"]["latest"]
    tarball_url = metadata["versions"][version]["dist"]["tarball"]

    with urllib.request.urlopen(tarball_url, timeout=60) as response:
        tarball = response.read()

    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        schema = _read_member(archive, SCHEMA_IN_PACKAGE)
        if schema is None:
            raise FileNotFoundError(
                f"{SCHEMA_IN_PACKAGE} is not in {PACKAGE}@{version}"
            )
        openapi = _read_member(archive, OPENAPI_IN_PACKAGE)
        return schema, openapi, version


def _read_member(archive: tarfile.TarFile, name: str) -> str | None:
    try:
        member = archive.extractfile(name)
    except KeyError:
        return None
    return None if member is None else member.read().decode("utf-8")


def fetch_openapi_spec_from_production() -> str:
    """The OpenAPI spec, pretty-printed with sorted keys so the diff is only real changes."""
    with urllib.request.urlopen(OPENAPI_URL, timeout=60) as response:
        spec = json.load(response)
    if "openapi" not in spec or "paths" not in spec:
        raise ValueError(f"{OPENAPI_URL} did not return an OpenAPI spec")
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "latest"

    schema, openapi, version = fetch_specs(version)
    openapi_source = f"{PACKAGE}@{version}"
    if openapi is None:
        openapi = fetch_openapi_spec_from_production()
        openapi_source = f"{OPENAPI_URL} ({PACKAGE}@{version} doesn't ship it)"

    SCHEMA_PATH.write_text(schema, encoding="utf-8")
    print(
        f"Wrote the GraphQL schema from {PACKAGE}@{version} to {_relative(SCHEMA_PATH)}"
    )
    OPENAPI_PATH.write_text(openapi, encoding="utf-8")
    print(f"Wrote the OpenAPI spec from {openapi_source} to {_relative(OPENAPI_PATH)}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    main()
