#!/usr/bin/env python3
"""Helps release the package. See "Publishing" in CONTRIBUTING.md.

    poetry run python dev/release.py prepare <version>
        Bumps pyproject.toml and CHANGELOG.md on a release branch and commits,
        ready for a PR to master.
    poetry run python dev/release.py tag
        Tags the current commit on master and pushes the tag, which runs the
        Publish workflow.

Both accept --dry-run to print what they would do without changing anything.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
PYPROJECT_PATH = ROOT / "pyproject.toml"
WORKFLOW_URL = "https://github.com/anvilco/python-anvil/actions/workflows/publish.yml"

# A PEP 440 release version, like 6.0.0, or a pre-release like 6.0.0a1, 6.0.0b2 or 6.0.0rc1
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+((a|b|rc)\d+)?$")
PYPROJECT_VERSION_RE = re.compile(r'^version = "(?P<version>[^"]+)"$', re.MULTILINE)

DRY_RUN = "--dry-run" in sys.argv
ARGS = [arg for arg in sys.argv[1:] if arg != "--dry-run"]


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def run(description: str, fn: Callable[[], object]) -> None:
    if DRY_RUN:
        print(f"[dry run] {description}")
    else:
        print(description)
        fn()


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def read_package_version() -> str:
    match = PYPROJECT_VERSION_RE.search(PYPROJECT_PATH.read_text())
    if not match:
        fail("Couldn't find the version in pyproject.toml")
    return match["version"]  # type: ignore[index]


def tag_exists(tag: str) -> str | None:
    if git("tag", "--list", tag):
        return "locally"
    if git("ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
        return "on origin"
    return None


def require_clean_working_tree() -> None:
    if git("status", "--porcelain"):
        fail("The working tree has uncommitted changes. Commit or stash them first.")


def is_prerelease(version: str) -> bool:
    return not version.replace(".", "").isdigit()


def prepare(args: list[str]) -> None:
    if not args:
        fail(
            "Usage: dev/release.py prepare <version>, e.g. dev/release.py prepare 6.0.0"
        )
    version = args[0].removeprefix("v")
    if not VERSION_RE.match(version):
        fail(f"{version} is not a release version, like 6.0.0 or 6.0.0rc1")

    tag = f"v{version}"
    current_version = read_package_version()
    if version == current_version:
        fail(f"pyproject.toml is already at {version}")
    existing = tag_exists(tag)
    if existing:
        fail(f"{tag} already exists {existing}")

    require_clean_working_tree()

    # Work on a release branch, so the change goes through a PR
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    release_branch = f"release/{tag}"
    if branch == "master":
        run(
            f"Creating branch {release_branch}",
            lambda: git("checkout", "-b", release_branch),
        )

    # pyproject.toml: a targeted replace, to keep the file's formatting
    pyproject = PYPROJECT_PATH.read_text()
    bumped = pyproject.replace(
        f'version = "{current_version}"', f'version = "{version}"', 1
    )
    if bumped == pyproject:
        fail(f'Couldn\'t find version = "{current_version}" in pyproject.toml')
    run(
        f"Bumping pyproject.toml from {current_version} to {version}",
        lambda: PYPROJECT_PATH.write_text(bumped),
    )

    # CHANGELOG.md: the Unreleased section becomes this version's. Pre-releases
    # leave it alone, so the final release gets all of the notes; their GitHub
    # release notes are generated from the commits instead.
    if is_prerelease(version):
        print(f"Leaving CHANGELOG.md as it is, since {tag} is a pre-release")
    else:
        changelog = CHANGELOG_PATH.read_text()
        unreleased = "## [Unreleased]\n"
        if unreleased not in changelog:
            fail('CHANGELOG.md has no "## [Unreleased]" section to release')
        updated = changelog.replace(
            unreleased, f"{unreleased}\n## [{tag}] - {date.today().isoformat()}\n", 1
        )
        run(
            f"Renaming the Unreleased section of CHANGELOG.md to {tag}",
            lambda: CHANGELOG_PATH.write_text(updated),
        )

    def commit() -> None:
        git("add", str(PYPROJECT_PATH), str(CHANGELOG_PATH))
        git("commit", "--quiet", "-m", f"Release {tag}")

    run(f'Committing "Release {tag}"', commit)

    check = (
        ""
        if is_prerelease(version)
        else f" Check the {tag} section of CHANGELOG.md reads well."
    )
    print(
        f"""
Next:
  1. Push this branch and open a PR to master.{check}
  2. After it merges: git checkout master && git pull && poetry run python dev/release.py tag
"""
    )


def tag() -> None:
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if branch != "master":
        fail(
            f"Tags must be on master, but this is {branch}. Run: git checkout master && git pull"
        )
    require_clean_working_tree()

    git("fetch", "--quiet", "origin", "master")
    head = git("rev-parse", "HEAD")
    if head != git("rev-parse", "origin/master"):
        fail("master is not the same as origin/master. Run: git pull")

    version = read_package_version()
    tag_name = f"v{version}"
    existing = tag_exists(tag_name)
    if existing:
        fail(
            f"{tag_name} already exists {existing}. Bump the version first: dev/release.py prepare <version>"
        )

    changelog = CHANGELOG_PATH.read_text()
    if f"## [{tag_name}]" not in changelog:
        if is_prerelease(version):
            print(
                f"CHANGELOG.md has no {tag_name} section, so the GitHub release notes will be generated from the commits"
            )
        else:
            fail(
                f'CHANGELOG.md has no "## [{tag_name}]" section. Run dev/release.py prepare {version} on a branch and merge it first.'
            )

    run(f"Tagging {head[:8]} as {tag_name}", lambda: git("tag", tag_name))
    run(f"Pushing {tag_name} to origin", lambda: git("push", "origin", tag_name))

    print(
        f"\nThe Publish workflow will publish {tag_name} to PyPI once a maintainer approves it: {WORKFLOW_URL}"
    )


def main() -> None:
    command = ARGS[0] if ARGS else None
    if command == "prepare":
        prepare(ARGS[1:])
    elif command == "tag":
        tag()
    else:
        fail("Usage: dev/release.py prepare <version> | dev/release.py tag")


if __name__ == "__main__":
    main()
