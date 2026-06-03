"""Event production interface.

Defines a Kafka-compatible producer abstraction used to publish scoring
and lifecycle events to a streaming bus for downstream consumers (e.g.
marketing automation, real-time dashboards). The repository ships only a
mock, in-memory implementation; a real deployment would back this with a
``kafka-python`` / ``confluent-kafka`` producer without changing callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EventProducer(ABC):
    """Abstract event producer with a Kafka-style interface."""

    @abstractmethod
    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """Publish a single event.

        Args:
            topic: Target topic name.
            value: Event payload (JSON-serializable).
            key: Optional partition key (e.g. user_id) for ordering.
        """
        ...

    @abstractmethod
    def flush(self) -> None:
        """Block until all buffered events have been delivered."""
        ...


class MockEventProducer(EventProducer):
    """In-memory event producer for development and tests.

    Captures published events in a list instead of sending them to a
    broker, which makes the event-emitting code path testable without
    external infrastructure.
    """

    def __init__(self) -> None:
        """Initialize an empty in-memory event buffer."""
        self.events: List[Dict[str, Any]] = []

    def send(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError
