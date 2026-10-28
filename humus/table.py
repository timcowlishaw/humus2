import os
from typing import Callable

from .field import Field, FieldValue
from .persistence import DATA_DIR
from .record import Record


class Table:
    def __init__(
        self,
        name: str,
        fields: list[tuple[str, type[Field[FieldValue]]]],
        destruction_strategy: Callable[[Record], bool] | None = None,
    ):
        self.name: str = name
        self.fields: list[tuple[str, type[Field[FieldValue]]]] = fields
        self.destruction_strategy: Callable[[Record], bool] | None = (
            destruction_strategy
        )

    def load(self) -> None:
        pass

    def __setitem__(self, id: str, values: dict[str, FieldValue]) -> None:
        record = Record(id=id, table=self, fields=self.fields)
        record.load()
        record.update(values)
        record.save()

    def __getitem__(self, id: str) -> Record:
        record = Record(id=id, table=self, fields=self.fields)
        record.load()
        return record

    def periodic_decay(self) -> None:
        for record in self.all():
            record.periodic_decay()

    def all(self) -> list[Record]:
        records: list[Record] = []
        for filename in os.listdir(f"{DATA_DIR}/{self.name}"):
            record = Record(id=filename, table=self, fields=self.fields)
            record.load()
            records.append(record)
        return records
