import html
from time import time

from flask import Flask, redirect, render_template, request

from ..text import Operation, Text
from ..text.decay import ConstantSpaceStrategy
from ..text.formatters import LabelledRangeFormatter
from ..persistence import CSVPersistenceStrategy

text = Text(
    decay_strategy=ConstantSpaceStrategy(size=1024),
    persistence_strategy=CSVPersistenceStrategy("./test.csv")
)

app = Flask(__name__)

@app.get("/")
def index():
    def age_class(op: Operation) -> str:
        now = time()
        age = now - op.timestamp
        if age > 60:
            return "old old-3"
        elif age > 10:
            return "old old-2"
        else:
            return "old old-1"

    age_formatter = LabelledRangeFormatter(
        lambda text, label: f'<span class="{label}">{html.escape(text)}</span>',
        age_class
    )

    return render_template("index.html", text=age_formatter.format(text))


@app.post("/")
def update():
    _ = text.update(request.form["text"])
    return redirect("/")



