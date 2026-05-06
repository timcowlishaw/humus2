# pyright: reportImportCycles=none

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, cast, override

if TYPE_CHECKING:
    from .record import Record


type FieldValue = str | int | float | bool


class Field[V: FieldValue](ABC):

    record: Record
    key: str

    def __init__(self, record: Record, key: str):
        self.record = record
        self.key = key

    @property
    @abstractmethod
    def value(self) -> V | None: ...

    @abstractmethod
    def update(self, value: V) -> Self: ...

    @abstractmethod
    def load(self) -> None: ...

    def save(self) -> None:
        self.record.update_persisted_values(self.key, self.value)

    def periodic_decay(self) -> None:
        pass


class StableField[V: FieldValue](Field[V]):

    def __init__(self, record: Record, key: str):
        super(StableField, self).__init__(record, key)
        self._value: V | None = None

    @override
    def update(self, value: V) -> Self:
        self._value = value
        return self

    @property
    @override
    def value(self) -> V | None:
        return self._value

    @override
    def load(self) -> None:
        self._value = cast(V | None, self.record.persisted_values.get(self.key))
