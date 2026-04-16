from flask import Flask, redirect, render_template, request

from ..text import Operation, Text
from ..text.decay import ConstantSpaceStrategy
from ..persistence import CSVPersistenceStrategy

text = Text(
    decay_strategy=ConstantSpaceStrategy(size=1024),
    persistence_strategy=CSVPersistenceStrategy("./test.csv")
)

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html", text=text.value)


@app.post("/")
def update():
    _ = text.update(request.form["text"])
    return redirect("/")



