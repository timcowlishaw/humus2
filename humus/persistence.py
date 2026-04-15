import csv
from collections.abc import Iterable
from typing import override, Any, Protocol

class Serializable[S : Iterable[Any]](Protocol):
    @property
    def serializable(self) -> S:
        ...

class Persistable[S : Iterable[Any]](Protocol):
    @property
    def serializable_items(self) -> Iterable[Serializable[S]]:
        ...

class PersistenceStrategy[S : Iterable[Any]](Protocol):
    def update_callback(self, persistable : Persistable[S]) -> None:
        ...


class NoOpPersistenceStrategy[S : Iterable[Any]](PersistenceStrategy[S]):
    @override
    def update_callback(self, persistable : Persistable[S]) -> None:
        pass

class CSVPersistenceStrategy[S : Iterable[Any]](PersistenceStrategy[S]):
    def __init__(self, filename : str):
        self.filename : str = filename

    @override
    def update_callback(self, persistable : Persistable[S]) -> None:
        with open(self.filename, "w") as file:
            writer = csv.writer(file)
            for row in persistable.serializable_items:
                writer.writerow(row.serializable)
