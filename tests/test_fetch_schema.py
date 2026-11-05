"""The parts of dev/fetch_schema.py that write the specs."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def load_fetch_schema():
    path = Path(__file__).parent.parent / "dev" / "fetch_schema.py"
    spec = importlib.util.spec_from_file_location("fetch_schema", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["fetch_schema"] = module
    spec.loader.exec_module(module)
    return module


def test_write_specs_records_the_version_they_came_from(tmp_path, monkeypatch):
    fetch_schema = load_fetch_schema()
    monkeypatch.setattr(fetch_schema, "SCHEMA_PATH", tmp_path / "anvil_schema.graphql")
    monkeypatch.setattr(fetch_schema, "OPENAPI_PATH", tmp_path / "openapi.json")
    monkeypatch.setattr(fetch_schema, "SOURCE_PATH", tmp_path / "source.json")

    fetch_schema.write_specs(
        "type Query { a: Int }\n", '{"openapi": "3.0.0"}\n', "1.2.3"
    )

    assert (tmp_path / "anvil_schema.graphql").read_text() == "type Query { a: Int }\n"
    assert (tmp_path / "openapi.json").read_text() == '{"openapi": "3.0.0"}\n'
    assert json.loads((tmp_path / "source.json").read_text()) == {
        "package": "@anvilco/types",
        "version": "1.2.3",
    }
    assert (tmp_path / "source.json").read_text().endswith("}\n")


def test_the_checked_in_source_names_the_package():
    source = json.loads(
        (Path(__file__).parent.parent / "schema" / "source.json").read_text()
    )

    assert source["package"] == "@anvilco/types"
    assert source["version"].count(".") == 2
