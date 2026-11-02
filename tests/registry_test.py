from typed_registry import MissingServiceError, ServiceRegistry, ServiceToken


class EventBus:
    pass


def test_registers_and_resolves_by_token_identity() -> None:
    first = ServiceToken[EventBus]("event_bus")
    same_name = ServiceToken[EventBus]("event_bus")
    registry = ServiceRegistry()
    event_bus = EventBus()

    first.register(registry, event_bus)

    assert registry.get(first) is event_bus
    try:
        registry.get(same_name)
    except MissingServiceError as error:
        assert error.service_name == "event_bus"
    else:
        raise AssertionError("distinct tokens with the same name must not alias")


def test_registration_can_replace_a_test_service() -> None:
    token = ServiceToken[EventBus]("event_bus")
    registry = ServiceRegistry()
    first = EventBus()
    replacement = EventBus()

    token.register(registry, first)
    token.register(registry, replacement)

    assert registry.get(token) is replacement
