import json
from typing import Self, cast

from .field import Field, FieldValue
from .persistence import DATA_DIR


class Record:
    def __init__(self, id: str, fields: list[tuple[str, type[Field[FieldValue]]]]):
        self.id: str = id
        self.fields: dict[str, Field[FieldValue]] = {}
        self.persisted_values: dict[str, FieldValue | None] = {}
        for name, cls in fields:
            self.fields[name] = cls(self, name)

    def load(self) -> None:
        self.load_persisted_values()
        for field in self.fields.values():
            field.load()

    def save(self) -> None:
        for field in self.fields.values():
            field.save()

    def get(self) -> dict[str, FieldValue | None]:
        return {key: field.value for (key, field) in self.fields.items()}

    def update(self, values: dict[str, FieldValue]) -> Self:
        for key, value in values.items():
            self.fields[key] = self.fields[key].update(value)
        return self

    def periodic_decay(self) -> None:
        for key in self.fields:
            self.fields[key].periodic_decay()

    def __getitem__(self, key: str) -> FieldValue | None:
        if field := self.fields.get(key):
            return field.value
        else:
            return None

    def __setitem__(self, key: str, value: FieldValue) -> None:
        _ = self.fields[key].update(value)

    @property
    def filename(self) -> str:
        return f"{DATA_DIR}/{self.id}/values.json"

    def load_persisted_values(self) -> None:
        with open(self.filename) as file:
            self.persisted_values = cast(dict[str, FieldValue | None], json.load(file))

    def save_persisted_values(self) -> None:
        with open(self.filename) as file:
            json.dump(self.persisted_values, file)

    def update_persisted_values(self, key: str, value: FieldValue | None) -> None:
        self.persisted_values[key] = value
        self.save_persisted_values()
