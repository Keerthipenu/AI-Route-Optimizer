from io import BytesIO

import pandas as pd
import pytest

from src.data_loader import load_csv
from src.validation import DataValidationError, frame_to_locations, validate_delivery_frame


def valid_frame():
    return pd.DataFrame({
        "location_id": ["D", "A"], "name": ["Depot", "Stop"],
        "latitude": [12.9, 12.91], "longitude": [77.6, 77.61],
    })


def test_valid_frame_gets_optional_columns():
    clean = validate_delivery_frame(valid_frame())
    assert list(clean.columns) == ["location_id", "name", "latitude", "longitude", "priority", "service_duration"]
    assert len(frame_to_locations(clean)) == 2


def test_empty_and_missing_columns_rejected():
    with pytest.raises(DataValidationError, match="empty"):
        validate_delivery_frame(pd.DataFrame())
    with pytest.raises(DataValidationError, match="Missing"):
        validate_delivery_frame(pd.DataFrame({"name": ["A"]}))


def test_duplicate_ids_rejected_but_coordinates_allowed():
    frame = valid_frame()
    frame.loc[1, "location_id"] = "D"
    with pytest.raises(DataValidationError, match="Duplicate"):
        validate_delivery_frame(frame)
    frame = valid_frame()
    frame.loc[1, ["latitude", "longitude"]] = frame.loc[0, ["latitude", "longitude"]]
    assert len(validate_delivery_frame(frame)) == 2


def test_invalid_csv_uploads():
    with pytest.raises(DataValidationError):
        load_csv(b"not,a,valid\nset,of,columns")
    with pytest.raises(DataValidationError):
        load_csv(BytesIO(b"\xff\xfe\x00"))
