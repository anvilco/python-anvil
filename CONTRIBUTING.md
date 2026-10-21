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

`python_anvil/types` is generated from the API specs in `schema/`: `anvil_schema.graphql`, the GraphQL schema as published in the [`@anvilco/types`](https://www.npmjs.com/package/@anvilco/types) npm package (the same copy node-anvil validates against), and `openapi.json`, the API's OpenAPI spec. Neither needs an API key to fetch.

```sh
make update-schema  # refresh schema/ from @anvilco/types and production
make generate       # regenerate python_anvil/types from schema/
```

`make generate` runs offline, and CI fails if the generated files don't match `schema/`, so run it after changing anything in `schema/`. See `dev/generate_types.py` for how each file is generated. The hand-written payload models in `python_anvil/api_resources/payload.py` extend the generated ones, so a change there is usually a matter of adjusting an override.

The [Sync API Types workflow](.github/workflows/sync-api-types.yml) does both steps after each Anvil production deploy, and weekly as a backstop, and opens a PR when anything changed. It needs:

* A `CI_GITHUB_TOKEN` repository secret: a token that can push branches and open PRs, so the PR gets its CI checks (the workflow's own `GITHUB_TOKEN` can't trigger workflows). anvil-js uses the same secret name.
* `python-anvil` in the `--webhook-repos` list of Foundry's postsync step in anvil-infra, which sends the `anvil-production-deploy` dispatch. Until then, only the weekly run and manual runs happen.

## Publishing

Publishing to PyPI is done by the [Publish workflow](.github/workflows/publish.yml) when a version tag is pushed, in two steps: the workflow builds and checks the release, and a maintainer approves the publish job. Merging to `master` does not publish anything.

1. On a branch, bump the version and release the `[Unreleased]` section of `CHANGELOG.md`:
   ```sh
   poetry run python dev/release.py prepare 6.0.0
   ```
   This sets `version` in `pyproject.toml`, renames `[Unreleased]` to `[v6.0.0]` with today's date, and commits. If you're on `master`, it creates a `release/v6.0.0` branch first. Push the branch, open a PR, and merge it to `master`.
1. Tag that commit on `master` and push the tag:
   ```sh
   git checkout master && git pull
   poetry run python dev/release.py tag
   ```
   This checks that `master` is up to date with `origin/master`, that `v6.0.0` doesn't already exist, and that `CHANGELOG.md` has a `[v6.0.0]` section, then tags and pushes.
1. When the workflow's build job has finished, approve its publish job on the workflow run's page. The job then publishes to PyPI and creates the GitHub release.

Both commands accept `--dry-run`. For a pre-release, run `poetry run python dev/release.py prepare 6.0.0rc1`: it bumps the version but leaves `CHANGELOG.md` alone, so the notes stay under `[Unreleased]` for the final release. Versions follow [PEP 440](https://peps.python.org/pep-0440/), so pre-releases are `6.0.0a1`, `6.0.0b1` or `6.0.0rc1`, and tagged `v6.0.0rc1`.

The workflow then:

1. Checks the tag is on `master` and matches the `pyproject.toml` version.
1. Lints, tests and builds the commit that was tagged.
1. Waits for a maintainer to approve the `pypi` environment, then publishes the build to PyPI with [trusted publishing](https://docs.pypi.org/trusted-publishers/).
1. Creates a GitHub release, using that version's `CHANGELOG.md` section as the release notes. Pre-releases are marked as such on GitHub.

### Setup

The workflow uses PyPI trusted publishing, so there is no PyPI token to store in GitHub secrets. Before the first release:

1. A maintainer of the PyPI project adds a trusted publisher on pypi.org, under the project's **Publishing** settings:
   * Publisher: GitHub
   * Owner: `anvilco`
   * Repository name: `python-anvil`
   * Workflow name: `publish.yml`
   * Environment name: `pypi`
1. A repository admin creates a `pypi` [environment](https://github.com/anvilco/python-anvil/settings/environments) on GitHub with **Required reviewers** set to the maintainers who may approve a release, and with deployment branches and tags limited to tags matching `v*`. The required reviewers are what makes a publish wait for approval; without them, the job publishes as soon as the build passes.

No GitHub secrets are needed: the release is created with the workflow's own `GITHUB_TOKEN`.
