import os
from random import choice, random, randrange
from string import printable
from typing import override

from .field import Field
from .persistence import DATA_DIR
from .record import Record


class SimpleText(Field[str]):

    _value: str | None

    def __init__(self, record: Record, key: str):
        super().__init__(record, key)
        self._value = None

    @property
    def filename(self) -> str:
        return f"{self.record.dirname}/simpletext_{self.key}.txt"

    @property
    @override
    def value(self) -> str | None:
        return self._value

    @override
    def update(self, value: str):
        self._value = value
        self.save()

    @override
    def load(self):
        try:
            with open(self.filename) as file:
                self._value = file.read()
        except FileNotFoundError:
            pass

    @override
    def save(self):
        if self.value is not None:
            os.makedirs(self.record.dirname, exist_ok=True)
            with open(self.filename, "w") as file:
                _ = file.write(self.value)

    @override
    def periodic_decay(self) -> None:
        decay_prob = float(os.environ.get("HUMUS_SIMPLE_TEXT_DECAY_PROBABILITY", "0.2"))
        if random() <= decay_prob:
            self.load()
            if self.value is not None and len(self.value) > 0:
                index = randrange(len(self.value))
                replacement = choice(
                    ["", "", "", choice(printable)]
                )  # 1/4 chance of a replacement, 3/4 of a deletion.
                self.update(self.value[0:index] + replacement + self.value[index + 1 :])
