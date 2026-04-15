from collections.abc import Iterable
from difflib import SequenceMatcher
from time import time
from typing import override, Protocol, Self

from .persistence import PersistenceStrategy, NoOpPersistenceStrategy, Persistable, Serializable

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


class TextDecayStrategy(Protocol):

    def apply(self, text: "Text") -> list[Operation]:
        ...

    def update_callback(self, text : "Text") -> None:
        pass


class MaxNInsertionsStrategy(TextDecayStrategy):

    def __init__(self, n : int = 100):
        self.max_n : int = n

    @override
    def apply(self, text: "Text") -> list[Operation]:
        new_ops : list[Operation] = []
        n_ops = len([op for op in text.ops if isinstance(op, Insertion)])
        to_delete = max(0, n_ops - self.max_n)
        for op in text.ops:
            if to_delete <= 0 or not isinstance(op, Insertion):
                new_ops.append(op)
            else:
                to_delete -= 1
        return new_ops

    @override
    def update_callback(self, text : "Text") -> None:
        text.ops = self.apply(text)


class ConstantSpaceStrategy(TextDecayStrategy):
    def __init__(self, size : int):
        self.size  : int = size

    @override
    def apply(self, text  : "Text") -> list[Operation]:
        overflow = text.size - self.size
        new_ops : list[Operation] = []
        for op in text.ops:
            if overflow > 0:
                overflow -= op.size
            else:
                new_ops.append(op)
        return new_ops

    @override
    def update_callback(self, text : "Text") -> None:
        text.ops = self.apply(text)



class Insertion(Operation):

    def __init__(self, position : int, text : str, timestamp : float | None = None):
        self.position : int = position
        self.text : str = text
        super(Insertion, self).__init__(timestamp)


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


    @override
    def __repr__(self) -> str:
        return f"Insertion(position: {self.position}, text: '{self.text}', timestamp: {self.timestamp})"


class Deletion(Operation):

    def __init__(self, position : int, length : int, timestamp : float | None = None):
        self.position : int = position
        self.length : int = length
        super(Deletion, self).__init__(timestamp)

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

    @override
    def __repr__(self):
        return f"Deletion(position: {self.position}, length: {self.length}, timestamp: {self.timestamp})"


class Text(Persistable[SerializableOp]):

    DEFAULT_DECAY_STRATEGY : TextDecayStrategy = MaxNInsertionsStrategy()
    DEFAULT_PERSISTENCE_STRATEGY : PersistenceStrategy[SerializableOp] = NoOpPersistenceStrategy()

    def __init__(self,
        initial_value : str | None = None,
        decay_strategy : TextDecayStrategy | None = None,
        persistence_strategy : PersistenceStrategy[SerializableOp] | None = None
    ):
        if decay_strategy is None:
            decay_strategy = Text.DEFAULT_DECAY_STRATEGY
        self.decay_strategy : TextDecayStrategy  = decay_strategy

        if persistence_strategy is None:
            persistence_strategy = Text.DEFAULT_PERSISTENCE_STRATEGY
        self.persistence_strategy : PersistenceStrategy[SerializableOp] = persistence_strategy

        self.ops : list[Operation] = []

        if initial_value is not None:
            _ = self.update(initial_value)

    @property
    def value(self) -> str:
        current = ""
        for op in self.ops:
            current = op.apply(current)
        return current

    @property
    def n_ops(self) -> int:
        return len(self.ops)

    @property
    def first_timestamp(self) -> float | None:
        if len(self.ops) > 0:
            return self.ops[0].timestamp

    @property
    def last_timestamp(self) -> float | None:
        if len(self.ops) > 0:
            return self.ops[-1].timestamp
    @property
    def size(self)-> int:
        return sum(op.size for op in self.ops)

    @property
    @override
    def serializable_items(self) -> Iterable[Serializable[SerializableOp]]:
        return self.ops

    def decay(self) -> Self:
        self.ops = self.decay_strategy.apply(self)
        return self

    def update(self, new_value : str) -> Self:
        matcher : SequenceMatcher[str] = SequenceMatcher(None, self.value, new_value, autojunk=False)
        offset : int  = 0  # tracks how prior insertions/deletions shift positions
        ops : list[Operation] = []
        for (tag, i1, i2, j1, j2) in matcher.get_opcodes():
            if tag == 'equal':
                pass
            elif tag == 'insert':
                ops.append(Insertion(i1 + offset, new_value[j1:j2]))
                offset += (j2 - j1)
            elif tag == 'delete':
                ops.append(Deletion(i1 + offset, i2 - i1))
                offset -= (i2 - i1)
            elif tag == 'replace':
                ops.append(Deletion(i1 + offset, i2 - i1))
                ops.append(Insertion(i1 + offset, new_value[j1:j2]))
                offset += (j2 - j1) - (i2 - i1)
        self.ops.extend(ops)
        self.decay_strategy.update_callback(self)
        self.persistence_strategy.update_callback(self)
        return self

    def trace_ops(self) -> None:
        for op in self.ops:
            print(op)

    @override
    def __repr__(self):
        return f"Text(value: '{self.value}', first_timestamp: {self.first_timestamp}, last_timestamp: {self.last_timestamp}, n_ops: {self.n_ops})"
