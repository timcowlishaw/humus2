from time import time
from typing import override, Protocol

from ..persistence import Serializable


type SerializableOp = tuple[str, float, int, int | None, str | None]

class Operation(Serializable[SerializableOp], Protocol):

    timestamp : float

    def __init__(self, timestamp : float | None = None):
        if timestamp is None:
            timestamp = time()
        self.timestamp = timestamp

    @property
    def size(self) -> int:
        ...

    def apply(self, _previous : str) -> str:
        ...

class Insertion(Operation):

    def __init__(self, position : int, text : str, timestamp : float | None = None):
        self.position : int = position
        self.text : str = text
        super(Insertion, self).__init__(timestamp)

    @override
    def __repr__(self) -> str:
        return f"Insertion(position: {self.position}, text: '{self.text}', timestamp: {self.timestamp})"

    @property
    @override
    def size(self) -> int:
        return len(self.text)

    @property
    @override
    def serializable(self) -> SerializableOp:
        return ("i", self.timestamp, self.position, None, self.text)

    @override
    def apply(self, previous : str) -> str:
        return previous[:self.position] + self.text + previous[self.position:]


class Deletion(Operation):

    def __init__(self, position : int, length : int, timestamp : float | None = None):
        self.position : int = position
        self.length : int = length
        super(Deletion, self).__init__(timestamp)

    @override
    def __repr__(self):
        return f"Deletion(position: {self.position}, length: {self.length}, timestamp: {self.timestamp})"

    @property
    @override
    def size(self) -> int:
        return 0

    @property
    @override
    def serializable(self) -> SerializableOp:
        return ("d", self.timestamp, self.position, self.length, None)

    @override
    def apply(self, previous : str) -> str:
        return previous[:self.position] + previous[self.position+self.length:]

