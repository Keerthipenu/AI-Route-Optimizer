from __future__ import annotations

from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO, TextIO

import pandas as pd

from .validation import DataValidationError, validate_delivery_frame

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SAMPLE_FILES = {
    "Small · Bengaluru (6 stops)": "sample_small.csv",
    "Medium · Bengaluru (12 stops)": "sample_medium.csv",
    "Large · Bengaluru (24 stops)": "sample_large.csv",
}


def load_sample(name: str) -> pd.DataFrame:
    if name not in SAMPLE_FILES:
        raise DataValidationError(f"Unknown sample dataset: {name}")
    return validate_delivery_frame(pd.read_csv(DATA_DIR / SAMPLE_FILES[name]))


def load_csv(source: str | bytes | Path | BinaryIO | TextIO) -> pd.DataFrame:
    try:
        if isinstance(source, bytes):
            source = BytesIO(source)
        elif isinstance(source, str) and ("\n" in source or "," in source):
            source = StringIO(source)
        frame = pd.read_csv(source)
    except Exception as exc:
        raise DataValidationError(f"The CSV could not be read: {exc}") from exc
    return validate_delivery_frame(frame)
