from __future__ import annotations

import os

DATA_DIR = os.environ.get("HUMUS_DATA_DIR", "./data")


class NotDeserializableError(RuntimeError):
    pass
