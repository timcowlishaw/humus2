from __future__ import annotations

import csv
import os
from difflib import SequenceMatcher
from random import choice, random, randrange
from string import printable
from time import time
from typing import Callable, Protocol, Self, override

from ..field import Field
from ..persistence import DATA_DIR
from ..record import Record
from .operations import Deletion, Insertion, Operation


class TextDecayStrategy(Protocol):

    def apply(self, text: Text) -> list[Operation]: ...

    def update_callback(self, text: Text) -> None:
        pass

    def periodic_decay(self, text: Text) -> None:
        pass


class MaxNInsertionsStrategy(TextDecayStrategy):

    def __init__(self) -> None:
        self.max_n: int = int(os.environ.get("HUMUS_TEXT_MAX_INSERTIONS", 100))

    @override
    def apply(self, text: Text) -> list[Operation]:
        new_ops: list[Operation] = []
        n_ops = len([op for op in text.ops if isinstance(op, Insertion)])
        to_delete = max(0, n_ops - self.max_n)
        for op in text.ops:
            if to_delete <= 0 or not isinstance(op, Insertion):
                new_ops.append(op)
            else:
                to_delete -= 1
        return new_ops

    @override
    def update_callback(self, text: Text) -> None:
        text.ops = self.apply(text)


class ConstantSpaceStrategy(TextDecayStrategy):
    def __init__(self) -> None:
        self.size: int = int(os.environ.get("HUMUS_TEXT_CONSTANT_SPACE_LIMIT", 1024))

    @override
    def apply(self, text: Text) -> list[Operation]:
        overflow = text.size - self.size
        new_ops: list[Operation] = []
        for op in text.ops:
            if overflow > 0:
                overflow -= op.size
            else:
                new_ops.append(op)
        return new_ops

    @override
    def update_callback(self, text: Text) -> None:
        text.ops = self.apply(text)


class RandomlyExponentialStrategy(TextDecayStrategy):

    def __init__(self) -> None:
        self.halflife: float = float(
            os.environ.get("HUMUS_TEXT_RANDOM_EXPONENTIAL_HALFLIFE", 300)
        )

    @override
    def apply(self, text: Text, now: float | None = None) -> list[Operation]:
        if now is None:
            now = time()
        new_ops: list[Operation] = []
        for op in text.ops:
            age = now - op.timestamp
            decay_prob = 1 - 2 ** (-age / self.halflife)
            if random() >= decay_prob:
                new_ops.append(op)
        return new_ops

    @override
    def update_callback(self, text: Text) -> None:
        text.ops = self.apply(text)

    @override
    def periodic_decay(self, text: Text) -> None:
        noise_prob = float(
            os.environ.get("HUMUS_TEXT_RANDOM_EXPONENTIAL_NOISE_PROB", "0.2")
        )
        if random() <= noise_prob:
            value = text.value
            ix = randrange(len(value))
            replace = choice(printable)
            value = value[0:ix] + replace + value[ix + 1 :]
            text.update(value)


DECAY_STRATEGIES: dict[str, Callable[[], TextDecayStrategy]] = {
    "max_n": MaxNInsertionsStrategy,
    "constant_space": ConstantSpaceStrategy,
    "random_exponential": RandomlyExponentialStrategy,
}


class Text(Field[str]):

    def __init__(
        self,
        record: Record,
        key: str,
    ) -> None:
        super(Text, self).__init__(record, key)
        self.decay_strategy: TextDecayStrategy = DECAY_STRATEGIES[
            os.environ.get("HUMUS_TEXT_DECAY_STRATEGY", "random_exponential")
        ]()

        self.ops: list[Operation] = []

    @property
    def filename(self) -> str:
        return (
            f"{DATA_DIR}/{self.record.table.name}/{self.record.id}/text_{self.key}.csv"
        )

    @override
    def load(self) -> None:
        ops: list[Operation] = []
        try:
            with open(self.filename) as file:
                reader = csv.reader(file)
                for row in reader:
                    ops.append(Operation.from_serialized(tuple(row)))
        except FileNotFoundError:
            pass
        self.ops = ops

    @override
    def save(self) -> None:
        os.makedirs(self.record.dirname, exist_ok=True)
        with open(self.filename, "w") as file:
            writer = csv.writer(file)
            for op in self.ops:
                writer.writerow(op.serialization)

    @override
    def __repr__(self) -> str:
        return (
            f"Text(value: '{self.value}', "
            f"first_timestamp: {self.first_timestamp}, "
            f"last_timestamp: {self.last_timestamp}, "
            f"n_ops: {self.n_ops})"
        )

    @property
    @override
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

    @override
    def update(self, value: str) -> None:
        matcher: SequenceMatcher[str] = SequenceMatcher(
            None, self.value, value, autojunk=False
        )
        offset: int = 0  # tracks how prior insertions/deletions shift positions
        ops: list[Operation] = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                pass
            elif tag == "insert":
                ops.append(Insertion(i1 + offset, value[j1:j2]))
                offset += j2 - j1
            elif tag == "delete":
                ops.append(Deletion(i1 + offset, i2 - i1))
                offset -= i2 - i1
            elif tag == "replace":
                ops.append(Deletion(i1 + offset, i2 - i1))
                ops.append(Insertion(i1 + offset, value[j1:j2]))
                offset += (j2 - j1) - (i2 - i1)
        self.ops.extend(ops)
        self.decay_strategy.update_callback(self)
        self.save()

    @override
    def periodic_decay(self) -> None:
        self.decay_strategy.periodic_decay(self)
        self.save()

    def trace_ops(self) -> None:
        for op in self.ops:
            print(op)
