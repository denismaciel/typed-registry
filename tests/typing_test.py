from typing import assert_type

from typed_registry import ServiceRegistry, ServiceToken


class EventBus:
    pass


class Settings:
    pass


def typecheck_registry() -> None:
    registry = ServiceRegistry()
    event_bus_token = ServiceToken[EventBus]("event_bus")
    settings_token = ServiceToken[Settings]("settings")

    event_bus_token.register(registry, EventBus())
    settings_token.register(registry, Settings())

    assert_type(registry.get(event_bus_token), EventBus)
    assert_type(registry.get(settings_token), Settings)
