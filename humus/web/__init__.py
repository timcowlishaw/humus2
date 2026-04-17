import html
from time import time

from flask import Flask, redirect, render_template, request
from flask.typing import ResponseReturnValue

from ..persistence import CSVPersistenceStrategy, PersistenceStrategy
from ..text import Operation, Text
from ..text.decay import RandomlyExponentialStrategy
from ..text.formatters import LabelledRangeFormatter

decay_strategy = RandomlyExponentialStrategy(halflife=300)
persistence_strategy: PersistenceStrategy[Text] = CSVPersistenceStrategy(
    "./data/test.csv"
)
text = persistence_strategy.reconstruct(Text, decay_strategy=decay_strategy)

app = Flask(__name__)


@app.get("/")
def index() -> ResponseReturnValue:
    def age_class(op: Operation) -> str:
        now = time()
        age = now - op.timestamp
        if age > 200:
            return "old old-3"
        elif age > 100:
            return "old old-2"
        else:
            return "old old-1"

    age_formatter = LabelledRangeFormatter(
        lambda text, label: f'<span class="{label}">{html.escape(text)}</span>',
        age_class,
    )

    return render_template("index.html", text=age_formatter.format(text))


@app.post("/")
def update() -> ResponseReturnValue:
    _ = text.update(request.form["text"])
    return redirect("/")
