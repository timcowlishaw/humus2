import os
from random import random, randrange
from typing import override

from .field import Field
from .persistence import DATA_DIR
from .record import Record


class File(Field[bytes]):

    _value: bytes | None

    def __init__(self, record: Record, key: str):
        super().__init__(record, key)
        self._value = None

    @property
    def filename(self) -> str:
        return f"{DATA_DIR}/{self.record.table.name}/{self.record.id}/file_{self.key}"

    @property
    @override
    def value(self) -> bytes | None:
        return self._value

    @override
    def update(self, value: bytes):
        self._value = value
        self.save()

    @override
    def load(self):
        try:
            with open(self.filename, "rb") as file:
                self._value = file.read()
        except FileNotFoundError:
            pass

    @override
    def save(self):
        if self.value is not None:
            os.makedirs(self.record.dirname, exist_ok=True)
            with open(self.filename, "wb") as file:
                _ = file.write(self.value)

    @override
    def periodic_decay(self) -> None:
        decay_prob = float(os.environ.get("HUMUS_FILE_DECAY_PROBABILITY", "0.2"))
        if random() <= decay_prob:
            self.load()
            if self.value is not None and len(self.value) > 0:
                data = bytearray(self.value)
                index = randrange(len(data))
                data[index] = randrange(255)
                self.update(bytes(data))
