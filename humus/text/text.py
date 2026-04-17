from __future__ import annotations

from collections.abc import Iterable
from difflib import SequenceMatcher
from typing import Callable, Self, cast, override

from ..persistence import (
    NoOpPersistenceStrategy,
    Persistable,
    PersistenceStrategy,
    Serialization,
)
from .decay import MaxNInsertionsStrategy, TextDecayStrategy
from .operations import Deletion, Insertion, Operation


class Text(Persistable[Operation]):

    DEFAULT_DECAY_STRATEGY: TextDecayStrategy = MaxNInsertionsStrategy()
    DEFAULT_PERSISTENCE_STRATEGY: PersistenceStrategy[Text] = NoOpPersistenceStrategy()

    def __init__(
        self,
        initial_value: str | None = None,
        ops: list[Operation] | None = None,
        decay_strategy: TextDecayStrategy | None = None,
        persistence_strategy: PersistenceStrategy[Text] | None = None,
    ):
        if decay_strategy is None:
            decay_strategy = Text.DEFAULT_DECAY_STRATEGY
        self.decay_strategy: TextDecayStrategy = decay_strategy

        if persistence_strategy is None:
            persistence_strategy = Text.DEFAULT_PERSISTENCE_STRATEGY
        self.persistence_strategy: PersistenceStrategy[Text] = persistence_strategy

        if ops is None:
            ops = []
        self.ops: list[Operation] = ops

        if initial_value is not None:
            _ = self.update(initial_value)

    @override
    @classmethod
    def from_persisted(
        cls,
        items: Iterable[Serialization],
        persistence_strategy: PersistenceStrategy[Text],
        **kwargs: object,
    ) -> Self:
        ops: list[Operation] = []
        decay_strategy = cast(TextDecayStrategy, kwargs["decay_strategy"])
        for item in items:
            ops.append(Operation.from_serialized(item))
        return cls(
            ops=ops,
            decay_strategy=decay_strategy,
            persistence_strategy=persistence_strategy,
        )

    @override
    def __repr__(self) -> str:
        return (
            f"Text(value: '{self.value}', "
            f"first_timestamp: {self.first_timestamp}, "
            f"last_timestamp: {self.last_timestamp}, "
            f"n_ops: {self.n_ops})"
        )

    @property
    def value(self) -> str:
        return self.apply_ops("", lambda op, current, previous: current)

    @property
    def n_ops(self) -> int:
        return len(self.ops)

    @property
    def first_timestamp(self) -> float | None:
        if len(self.ops) > 0:
            return self.ops[0].timestamp
        else:
            return None

    @property
    def last_timestamp(self) -> float | None:
        if len(self.ops) > 0:
            return self.ops[-1].timestamp
        else:
            return None

    @property
    def size(self) -> int:
        return sum(op.size for op in self.ops)

    @property
    @override
    def serializable_items(self) -> Iterable[Operation]:
        return self.ops

    def apply_ops[T](self, initial: T, callback: Callable[[Operation, str, T], T]) -> T:
        current = initial
        current_text = ""
        for op in self.ops:
            current_text = op.apply(current_text)
            current = callback(op, current_text, current)
        return current

    def decay(self) -> Self:
        self.ops = self.decay_strategy.apply(self)
        return self

    def update(self, new_value: str) -> Self:
        matcher: SequenceMatcher[str] = SequenceMatcher(
            None, self.value, new_value, autojunk=False
        )
        offset: int = 0  # tracks how prior insertions/deletions shift positions
        ops: list[Operation] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                pass
            elif tag == "insert":
                ops.append(Insertion(i1 + offset, new_value[j1:j2]))
                offset += j2 - j1
            elif tag == "delete":
                ops.append(Deletion(i1 + offset, i2 - i1))
                offset -= i2 - i1
            elif tag == "replace":
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
