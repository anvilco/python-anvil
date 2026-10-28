"""The parts of dev/generate_types.py that post-process the generator's output."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load_generator():
    path = Path(__file__).parent.parent / "dev" / "generate_types.py"
    spec = importlib.util.spec_from_file_location("generate_types", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_types"] = module
    spec.loader.exec_module(module)
    return module


def describe_use_plain_str():
    def it_rewrites_a_one_line_import():
        gen = load_generator()
        source = "from pydantic import AwareDatetime, ConfigDict, EmailStr, Field\n\nemail: EmailStr | None\nwhen: AwareDatetime\n"
        out = gen._use_plain_str(source, ["EmailStr", "AwareDatetime"])
        assert (
            out
            == "from pydantic import ConfigDict, Field\n\nemail: str | None\nwhen: str\n"
        )

    def it_rewrites_a_wrapped_import():
        gen = load_generator()
        source = (
            "from pydantic import (\n    AnyUrl,\n    AwareDatetime,\n    ConfigDict,\n"
            "    EmailStr,\n    Field,\n)\n\nemail: EmailStr\n"
        )
        out = gen._use_plain_str(source, ["EmailStr", "AwareDatetime"])
        assert (
            out
            == "from pydantic import (\n    AnyUrl,\n    ConfigDict,\n    Field,\n)\n\nemail: str\n"
        )
        assert "import" in out and " str," not in out

    def it_keeps_acronym_plurals_whole_in_snake_case():
        gen = load_generator()
        assert gen._snake_case("mergePDFs") == "merge_pdfs"
        assert gen._snake_case("webhookURL") == "webhook_url"
        assert gen._snake_case("signURLForUser") == "sign_url_for_user"
