from __future__ import annotations

import csv
from collections.abc import Iterable
from typing import Any, Protocol, Self, TypeVar, override

type Serialization = tuple[str, ...]


class Serializable(Protocol):
    @property
    def serializable(self) -> Serialization: ...

    @classmethod
    def from_serialized(cls, serialization: Serialization) -> Self: ...


S = TypeVar("S", bound=Serializable, covariant=True)


class Persistable[S](Protocol):
    @property
    def serializable_items(self) -> Iterable[S]: ...

    @classmethod
    def from_persisted(
        cls,
        items: Iterable[Serialization],
        persistence_strategy: PersistenceStrategy[Self],
        **kwargs: object,
    ) -> Self: ...


class PersistenceStrategy[P: Persistable[Any]](Protocol):
    # We can't actually enforce Persitable[S] here as you can't
    # include a TypeVar in a constraint, and Persistable[Serializable]
    # isn't covariant, so leads to errors, so we have to use Any
    def update_callback(self, persistable: P) -> None: ...

    def reconstruct(self, cls: type[P], **kwargs: object) -> P: ...


class NotDeserializableError(RuntimeError):
    pass


class NoOpPersistenceStrategy[P: Persistable[Serializable]](PersistenceStrategy[P]):
    @override
    def update_callback(self, persistable: P) -> None:
        pass

    @override
    def reconstruct(self, cls: type[P], **kwargs: object) -> P:
        raise NotDeserializableError


class CSVPersistenceStrategy[P: Persistable[Serializable]](PersistenceStrategy[P]):
    def __init__(self, filename: str):
        self.filename: str = filename

    @override
    def update_callback(self, persistable: P) -> None:
        with open(self.filename, "w") as file:
            writer = csv.writer(file)
            for row in persistable.serializable_items:
                writer.writerow(row.serializable)

    @override
    def reconstruct(self, cls: type[P], **kwargs: object) -> P:
        with open(self.filename) as file:
            reader = csv.reader(file)
            items: list[Serialization] = []
            for row in reader:
                items.append(tuple(row))
            return cls.from_persisted(items, self, **kwargs)
