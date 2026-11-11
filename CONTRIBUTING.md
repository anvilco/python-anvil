# Contributing

How to work on the client and publish it. For using the client, see the [README](README.md).

## Development

The client supports Python 3.10 through 3.15, and `.python-version` pins the version to develop with. Any way of installing that Python works, e.g. [uv](https://docs.astral.sh/uv/) (`uv python install`) or [pyenv](https://github.com/pyenv/pyenv) (`pyenv install`). Dependencies are managed with [Poetry](https://python-poetry.org/docs/#installation) 2.

Install the package, the `cli` extra and the dev dependencies into `.venv`:

```sh
make install
```

Lint, type-check, and run the unit tests:

```sh
make lint
make test
```

`make format` formats the code and fixes what the linter can. [Ruff](https://docs.astral.sh/ruff/) does both the linting and the formatting, and [mypy](https://mypy-lang.org/) the type-checking; their settings are in `pyproject.toml`. There is also a [pre-commit](https://pre-commit.com/) config that runs ruff.

Run a single test file or test with pytest directly:

```sh
poetry run pytest tests/test_api.py -k fill_pdf
```

The tests in `tests/test_http.py` run the real client against a local HTTP server (`tests/server.py`), so the auth encoding, multipart bodies, rate limit timing and error handling are checked on the wire. `tests/test_graphql_operations.py` validates the client's queries and mutations against the API schema in `schema/`.

## Testing against a real environment

[`test-client.py`](test-client.py) runs every method against an Anvil environment and prints a `PASS`, `FAIL` or `SKIP` for each. Run it on a release before and after a change to see which behaviors changed. It uses staging by default, and needs an API key for that environment:

```sh
ANVIL_API_KEY=<your staging API key> make test-client
```

* `ANVIL_BASE_URL` - _optional_ Test another environment instead, e.g. `http://localhost:3000`.
* `ANVIL_PDF_TEMPLATE_ID` - _optional_ The PDF template to test `fill_pdf` with. Defaults to the first template in your organization that has example data.
* `ANVIL_FORGE_EID` - _optional_ The webform (Forge) in a Workflow to test `forge_submit` with. Defaults to the first one in your organization.

Everything it creates is test data. It creates a test Etch packet each run, and removes the Workflow submission it creates.

## The generated types

`python_anvil/types` is generated from the API specs in `schema/`: `anvil_schema.graphql`, the GraphQL schema, and `openapi.json`, the API's OpenAPI spec. Both come from the published [`@anvilco/types`](https://www.npmjs.com/package/@anvilco/types) npm package, which anvil-js regenerates from production after every deploy; node-anvil and dotnet-anvil generate their types from the same copy, so every client describes the same API build. Neither needs an API key to fetch. (A version of the package that predates the OpenAPI spec shipping in it falls back to fetching the spec from production.)

```sh
make update-schema  # refresh schema/ from the latest @anvilco/types
make generate       # regenerate python_anvil/types from schema/
```

`make generate` runs offline, and CI fails if the generated files don't match `schema/`, so run it after changing anything in `schema/`. See `dev/generate_types.py` for how each file is generated. The hand-written payload models in `python_anvil/api_resources/payload.py` extend the generated ones, so a change there is usually a matter of adjusting an override.

`schema/source.json` records which version of the package the specs came from.

The [Sync API Types workflow](.github/workflows/sync-api-types.yml) does both steps whenever anvil-js publishes a new `@anvilco/types` (its release workflow sends an `anvilco-types-published` dispatch here), and weekly as a backstop, and opens a PR when anything changed. The PR says whether that version was a major, minor or patch of `@anvilco/types` (see Versioning); on a major it marks its changelog note `BREAKING`, adds the `breaking` label, and asks the GitHub users in the optional `SYNC_BREAKING_REVIEWERS` repository variable for review. It needs a `CI_GITHUB_TOKEN` repository secret: a token that can push branches and open PRs, so the PR gets its CI checks (the workflow's own `GITHUB_TOKEN` can't trigger workflows). anvil-js and dotnet-anvil use the same secret name.

## Versioning

Versions follow [semver](https://semver.org). The generated `python_anvil.types` are public API, so they count: a release that removes or renames a type or field is a major, one that adds them is a minor.

They come from `@anvilco/types`, which takes its own bumps from the API's spec diffs ([its policy](https://github.com/anvilco/anvil-js/tree/main/packages/types#versioning): major for a removed or changed type, field or argument, minor for additions, patch for descriptions). So every sync sets a floor for the next release here: a sync of a `@anvilco/types` major is a `BREAKING:` entry in `CHANGELOG.md` and the next release is a major; a minor makes it at least a minor. The client's own changes can raise the bump, never lower it.

## Publishing

Releases are run from [anvilco/package-ops](https://github.com/anvilco/package-ops), the private repository that releases every Anvil package: Actions → **Release** → **Run workflow**, pick `anvilco/python-anvil` and the increment. Merging to `master` does not publish anything, and nothing in this repository publishes.

The run checks out `master`, runs `make lint` and `make test`, checks the release floor (the last tag matches `version` in `pyproject.toml`, `CHANGELOG.md` has notes under `[Unreleased]`, and the increment isn't below what the synced `@anvilco/types` demands; see Versioning), then bumps `pyproject.toml`, turns `[Unreleased]` into `[vX.Y.Z] - date`, commits `Release vX.Y.Z` to `master`, tags `vX.Y.Z`, creates the GitHub release with that changelog section as its notes, builds with `make build`, and publishes the build to PyPI with [trusted publishing](https://docs.pypi.org/trusted-publishers/). A dry run (the default) shows all of that and changes nothing; run one first.

A pre-release (`prerelease` set to `rc`, say) bumps the version but leaves `CHANGELOG.md` alone, so the notes stay under `[Unreleased]` for the final release. The tag is semver (`v6.1.0-rc.1`); Poetry normalizes the version in the built package to [PEP 440](https://peps.python.org/pep-0440/) (`6.1.0rc1`), which is what PyPI shows.

Who may run a real release, the PyPI trusted publisher, and the GitHub App that pushes the release commit are set up in package-ops; its README has the details and how to add a repository.
