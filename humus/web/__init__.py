import html
from time import time
from typing import cast

from flask import Flask, redirect, render_template, request
from flask.typing import ResponseReturnValue

from ..field import StableField
from ..record import Record
from ..table import Table
from ..text import Operation, Text
from ..text.formatters import LabelledRangeFormatter

halflife = 300

table = Table(  # noqa
    name="notes",
    fields=[  # TODO Tim what's the typing problem here?
        ("text", Text),
        ("x", StableField[int]),
        ("y", StableField[int]),
    ],
)
table.load()

app = Flask(__name__)


@app.get("/")
def index() -> ResponseReturnValue:
    def age_class(op: Operation) -> str:
        now = time()
        age = now - op.timestamp
        if age > 2 / 3 * halflife:
            return "old old-3"
        elif age > 1 / 3 * halflife:
            return "old old-2"
        else:
            return "old old-1"

    age_formatter = LabelledRangeFormatter(
        lambda text, label: f'<span class="{label}">{html.escape(text)}</span>',
        age_class,
    )

    record = table["test"]
    return render_template(
        "index.html",
        text=age_formatter.format(cast(Text, record.fields["text"])),
        x=record.fields["x"].value or 50,
        y=record.fields["y"].value or 50,
    )


# TODO Tim, get the window moving around. Then deal with multiples
# , with like a DB class.
@app.post("/<id>")
def update(id) -> ResponseReturnValue:
    for key in request.form:
        table[id][key] = request.form[key]
    return redirect("/")
