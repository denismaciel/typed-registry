# typed-registry

[![CI](https://github.com/denismaciel/typed-registry/actions/workflows/ci.yml/badge.svg)](https://github.com/denismaciel/typed-registry/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A tiny, fully typed service registry for Python. It has no dependencies, about
35 lines of code, and needs no casts.

```python
event_bus = registry.get(Services.event_bus)  # your type checker knows: EventBus
```

## Why

Most service locators key services by string or by class and hand you back
`Any`, or make you write `cast(...)` at every call site. `typed-registry`
keys services by **typed tokens** instead. Each token carries the type of the
service it names, so:

- `registry.get(token)` returns the right type, inferred by MyPy, ty, and
  Zuban.
- `token.register(registry, value)` rejects a value of the wrong type at type
  check time.
- Two tokens with the same name never collide, because tokens compare by
  identity, not by name.

## Install

```sh
uv add typed-registry==0.1.1
```

Requires Python 3.14+.

## Usage

Declare a catalogue of tokens that your application owns:

```python
from typing import Final

from typed_registry import ServiceToken


class Services:
    event_bus: Final = ServiceToken[EventBus]("platform.event_bus")
    settings: Final = ServiceToken[Settings]("platform.settings")
```

Wire concrete services in your composition root:

```python
from typed_registry import ServiceRegistry

registry = ServiceRegistry()
Services.settings.register(registry, Settings.from_env())
Services.event_bus.register(registry, EventBus())
```

Resolve them where you build the rest of the application:

```python
event_bus = registry.get(Services.event_bus)  # EventBus
settings = registry.get(Services.settings)    # Settings
```

Mismatches are caught before your code runs:

```python
Services.event_bus.register(registry, Settings())
# error: Argument 2 to "register" of "ServiceToken" has incompatible type "Settings"; expected "EventBus"
```

Asking for a token that was never registered raises `MissingServiceError`,
which is a `LookupError` and exposes the token's `service_name`:

```python
from typed_registry import MissingServiceError

try:
    registry.get(Services.event_bus)
except MissingServiceError as error:
    print(error.service_name)  # "platform.event_bus"
```

## Testing

Registering a token again replaces its value, so tests can build the real
wiring and then swap in a fake for a single service. The replacement is still
type checked against the token:

```python
registry = build_registry()
Services.event_bus.register(registry, FakeEventBus())
```

## Design notes

`typed-registry` is meant for the **composition root**: the one place where an
application assembles its object graph. Keep the registry there. Domain code
should receive the narrow dependencies it needs as plain arguments, not reach
into the registry. That keeps the domain easy to test without any registry at
all, and avoids the usual downside of service locators, which is that
dependencies become hidden.

Some deliberate non-features:

- **No autowiring or reflection.** You construct services yourself, in order.
- **No scopes or lifecycles.** A registry holds values; create one per scope if
  you need to.
- **No global registry.** You create and pass `ServiceRegistry` instances
  explicitly.

## API

| Name | Description |
| --- | --- |
| `ServiceToken[T](name)` | Typed, identity-compared key. `name` is used only in error messages. |
| `ServiceToken.register(registry, service)` | Store `service: T`, replacing any previous value. |
| `ServiceRegistry.get(token) -> T` | Resolve a service, or raise `MissingServiceError`. |
| `MissingServiceError` | `LookupError` subclass with a `service_name` attribute. |

## Development

```sh
make dev            # uv sync --locked
make check          # mypy and ty
make test           # pytest
make build          # uv build --no-sources
make release-check  # build and test installed wheel + sdist
```

Use uv 0.12.4. Development dependencies are pinned in `uv.lock`; packaging uses
`uv_build==0.12.4`. CI runs the same commands on Python 3.14 and 3.15.

## Releases

Releases are published to PyPI and GitHub. To prepare a release, update `project.version` in
`pyproject.toml`, run `uv lock`, and run:

```sh
make dev check test
RELEASE_TAG=v0.1.1 make release-check  # use the new version
```

`release-check` rejects a mismatched tag before building. It builds with
`uv build --no-sources`, installs the wheel and sdist separately in temporary
virtual environments outside the checkout, and checks package metadata,
`py.typed`, and registry behavior. Verified wheel/sdist files, `SHA256SUMS`, and
a hashed `index.html` are written to `dist/release/` (replacing its prior contents).
Without `RELEASE_TAG`, the check uses the version from `pyproject.toml`.

Commit the version and lockfile, then push a matching `vVERSION` tag. The release
workflow runs CI on that exact commit, repeats distribution verification, and
creates a draft GitHub release with the verified assets before publishing it.
Versions use `X.Y.Z` or `X.Y.ZaN`, `X.Y.ZbN`, or `X.Y.ZrcN`. Alpha, beta, and
release-candidate tags publish as prereleases without changing the latest release.
Existing releases are never overwritten. If publication fails after creating the
draft, inspect that draft and its assets before manually finishing or deleting it.
A manual workflow dispatch builds and uploads Actions artifacts only; it never
publishes a release.

After GitHub publication, a separate `pypi` environment job publishes only the
verified wheel and sdist to PyPI using Trusted Publishing and attestations. That
job never checks out or executes project code and has no repository write access.
Both publishers require a `v*` tag push in the canonical repository; the tagged
commit must be reachable from the default branch fetched from origin. Manual
workflow dispatch cannot publish. Checkout credentials are not persisted, and
release/CI dependency caching is disabled.

Configure the PyPI Trusted Publisher for owner `denismaciel`, repository
`typed-registry`, workflow `release.yml`, and environment `pypi`. Restrict that
GitHub environment to release tags and protect the default branch and release
tags. No PyPI API token is needed. If PyPI publication fails after GitHub
publication, rerun only the failed PyPI job; do not replace the GitHub release or
reuse a published PyPI version.

Once release assets are published, use that release's versioned wheel index
(replace the example version with the published version):

```sh
uv add --no-index --find-links https://github.com/denismaciel/typed-registry/releases/download/v0.1.1/index.html typed-registry==0.1.1
```

## License

[MIT](LICENSE)
