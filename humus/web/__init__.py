import hashlib
import html
from time import time
from typing import cast

from flask import Flask, Response, redirect, render_template, request
from flask.typing import ResponseReturnValue

from ..field import StableField
from ..file import File
from ..record import Record
from ..simple_text import SimpleText
from ..table import Table
from ..text import Text
from ..text.formatters import LabelledRangeFormatter

halflife = 300


def remove_record(record: Record) -> bool:
    if record["file"] is None:
        if record["text"] is None:
            return True
        if len(record["text"]) == 0:
            return True


table = Table(  # noqa
    name="notes",
    fields=[  # TODO Tim what's the typing problem here?
        ("text", SimpleText),
        ("file", File),
        ("x", StableField[int]),
        ("y", StableField[int]),
        ("z", StableField[int]),
        ("w", StableField[int]),
        ("h", StableField[int]),
        ("created", StableField[float]),
    ],
    destruction_strategy=remove_record,
)
table.load()

app = Flask(__name__)


def age_class(timestamp: float) -> str:
    now = time()
    age = now - float(timestamp)
    if age > 2 / 3 * halflife:
        return "old old-3"
    elif age > 1 / 3 * halflife:
        return "old old-2"
    else:
        return "old old-1"


age_formatter = LabelledRangeFormatter(
    lambda text, label: f'<span class="{label}">{html.escape(text)}</span>',
    lambda op: age_class(op.timestamp),
)


@app.template_filter()
def format_simple_text_with_age_styles(record: Record) -> str:
    text = record["text"]
    timestamp = record["created"]
    if text and timestamp:
        label = age_class(timestamp)
        return f'<span class="{label}">{html.escape(text)}</span>'
    else:
        return ""


@app.template_filter()
def format_text_with_age_styles(record: Record) -> str:
    return age_formatter.format(cast(Text, record.fields["text"]))


@app.template_filter()
def file_version(record: Record) -> str:
    data = record["file"]
    return hashlib.md5(cast(bytes, data)).hexdigest()[:8] if data else ""


@app.get("/")
def index() -> ResponseReturnValue:
    table.periodic_decay()
    return render_template("index.html", records=table.all())


@app.get("/<id>/file")
def get_file(id) -> ResponseReturnValue:
    data = table[id]["file"]
    return Response(cast(bytes, data), mimetype="image/jpeg")


@app.post("/<id>")
def update(id) -> ResponseReturnValue:
    for key in request.form:
        table[id][key] = request.form[key]
    for key, upload in request.files.items():
        table[id][key] = upload.read()
    return redirect("/")
