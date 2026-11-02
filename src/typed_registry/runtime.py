"""Typed runtime service composition primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast


class MissingServiceError(LookupError):
    def __init__(self, service_name: str) -> None:
        super().__init__(f"service is not registered: {service_name}")
        self.service_name = service_name


@dataclass(frozen=True, slots=True, eq=False)
class ServiceToken[T]:
    name: str

    def register(self, registry: ServiceRegistry, service: T) -> None:
        registry._store(self, service)


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[object, object] = {}

    def _store(self, token: object, service: object) -> None:
        self._services[token] = service

    def get[T](self, token: ServiceToken[T]) -> T:
        try:
            service = self._services[token]
        except KeyError:
            raise MissingServiceError(token.name) from None
        return cast(T, service)
