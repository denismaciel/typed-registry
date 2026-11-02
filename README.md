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
uv add typed-registry
# or
pip install typed-registry
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
uv sync
uv run pytest
uv run mypy
uv run ty check src tests
```

## License

[MIT](LICENSE)
