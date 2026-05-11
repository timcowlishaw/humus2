from .field import Field, FieldValue
from .record import Record


class Table:
    def __init__(self, name: str, fields: list[tuple[str, type[Field[FieldValue]]]]):
        self.name: str = name
        self.fields: list[tuple[str, type[Field[FieldValue]]]] = fields

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
