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


@app.template_filter()
def format_text_with_age_styles(record: Record) -> str:
    return age_formatter.format(cast(Text, record.fields["text"]))


@app.get("/")
def index() -> ResponseReturnValue:
    return render_template("index.html", records=table.all())


@app.post("/<id>")
def update(id) -> ResponseReturnValue:
    for key in request.form:
        table[id][key] = request.form[key]
    return redirect("/")
