from __future__ import annotations

from abc import ABC, abstractmethod
from time import time
from typing import override

from ..persistence import NotDeserializableError


class Operation(ABC):

    timestamp: float

    def __init__(self, timestamp: float | None = None):
        if timestamp is None:
            timestamp = time()
        self.timestamp = timestamp

    @classmethod
    def from_serialized(cls, serialization: tuple[str, ...]) -> Operation:
        (tag, timestamp, position, length, text) = serialization
        if tag == "i":
            return Insertion(int(position), text, float(timestamp))
        elif tag == "d":
            return Deletion(int(position), int(length), float(timestamp))
        else:
            raise NotDeserializableError

    @property
    @abstractmethod
    def size(self) -> int: ...

    @property
    @abstractmethod
    def serialization(self) -> tuple[str, ...]: ...

    @abstractmethod
    def apply(self, _previous: str) -> str: ...


class Insertion(Operation):

    def __init__(self, position: int, text: str, timestamp: float | None = None):
        self.position: int = position
        self.text: str = text
        super(Insertion, self).__init__(timestamp)

    @override
    def __repr__(self) -> str:
        return (
            f"Insertion(position: {self.position}, "
            f"text: '{self.text}',"
            f"timestamp: {self.timestamp})"
        )

    @property
    @override
    def size(self) -> int:
        return len(self.text)

    @property
    @override
    def serialization(self) -> tuple[str, ...]:
        return ("i", str(self.timestamp), str(self.position), "", self.text)

    @override
    def apply(self, previous: str) -> str:
        return previous[: self.position] + self.text + previous[self.position :]


class Deletion(Operation):

    def __init__(self, position: int, length: int, timestamp: float | None = None):
        self.position: int = position
        self.length: int = length
        super(Deletion, self).__init__(timestamp)

    @override
    def __repr__(self) -> str:
        return (
            f"Deletion(position: {self.position}, "
            f"length: {self.length}, "
            f"timestamp: {self.timestamp})"
        )

    @property
    @override
    def size(self) -> int:
        return 0

    @property
    @override
    def serialization(self) -> tuple[str, ...]:
        return ("d", str(self.timestamp), str(self.position), str(self.length), "")

    @override
    def apply(self, previous: str) -> str:
        return previous[: self.position] + previous[self.position + self.length :]
