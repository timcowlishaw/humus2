# pyright: reportImportCycles=none

from __future__ import annotations

import json
import os
from shutil import rmtree
from typing import TYPE_CHECKING, Callable, cast

from .field import Field, FieldValue
from .persistence import DATA_DIR

if TYPE_CHECKING:
    from .table import Table


class Record:
    def __init__(
        self, id: str, table: Table, fields: list[tuple[str, type[Field[FieldValue]]]]
    ):
        self.id: str = id
        self.table: Table = table
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

    def update(self, values: dict[str, FieldValue]) -> None:
        for key, value in values.items():
            self.fields[key].update(value)

    def periodic_decay(self) -> None:
        for key in self.fields:
            self.fields[key].periodic_decay()
        if self.table.destruction_strategy:
            destroy = self.table.destruction_strategy(self)
            if destroy:
                self.destroy()

    def __getitem__(self, key: str) -> FieldValue | None:
        if field := self.fields.get(key):
            return field.value
        else:
            return None

    def __setitem__(self, key: str, value: FieldValue) -> None:
        self.fields[key].update(value)
        self.save()

    @property
    def filename(self) -> str:
        return f"{self.dirname}/values.json"

    @property
    def dirname(self) -> str:
        return f"{DATA_DIR}/{self.table.name}/{self.id}"

    def load_persisted_values(self) -> None:
        try:
            with open(self.filename) as file:
                self.persisted_values = cast(
                    dict[str, FieldValue | None], json.load(file)
                )
        except FileNotFoundError:
            pass

    def save_persisted_values(self) -> None:
        os.makedirs(self.dirname, exist_ok=True)
        with open(self.filename, "w") as file:
            json.dump(self.persisted_values, file)

    def update_persisted_values(self, key: str, value: FieldValue | None) -> None:
        self.persisted_values[key] = value
        self.save_persisted_values()

    def destroy(self):
        rmtree(self.dirname)
