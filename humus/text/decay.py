# pyright: reportImportCycles=none

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, override

from .operations import Insertion, Operation

if TYPE_CHECKING:  # This gets around the need for a circular import
    from .text import Text


class TextDecayStrategy(Protocol):

    def apply(self, text: Text) -> list[Operation]: ...

    def update_callback(self, text: Text) -> None:
        pass


class MaxNInsertionsStrategy(TextDecayStrategy):

    def __init__(self, n: int = 100):
        self.max_n: int = n

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
    def __init__(self, size: int):
        self.size: int = size

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
