from itertools import groupby
from typing import Callable

from .operations import Deletion, Insertion, Operation
from .text import Text


class LabelledRangeFormatter:
    def __init__(self, template : Callable[[str, str], str], labeller : Callable[[Operation], str]):
        self.template : Callable[[str, str], str] = template
        self.labeller : Callable[[Operation], str] = labeller

    def format(self, text : Text)  -> str:
        initial : tuple[list[str], str] = ([], "")
        result : tuple[list[str], str] = text.apply_ops(initial, self._apply_callback)
        (ages, current) = result
        parts: list[str] = []
        for label, group in groupby(zip(current, ages), key=lambda x: x[1]):
            group_text = "".join(char for char, _ in group)
            parts.append(self.template(group_text, label))

        return "".join(parts)

    def _apply_callback(self, op : Operation, current: str,  accumulator : tuple[list[str], str]) -> tuple[list[str], str]:
        (ages, _previous) = accumulator
        if isinstance(op, Insertion):
            ages = (
                ages[:op.position]
                + [self.labeller(op)] * len(op.text)
                + ages[op.position:]
            )
        elif isinstance(op, Deletion):
            ages = (
                ages[:op.position]
                + ages[op.position + op.length:]
            )
        return (ages, current)
