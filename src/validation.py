from __future__ import annotations

import pandas as pd

from .distance import validate_coordinate
from .models import Location

REQUIRED_COLUMNS = ("location_id", "name", "latitude", "longitude")
OPTIONAL_COLUMNS = ("priority", "service_duration")


class DataValidationError(ValueError):
    """A user-facing delivery data validation error."""


def validate_delivery_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise DataValidationError("The delivery dataset is empty.")
    clean = frame.copy()
    clean.columns = [str(column).strip().lower() for column in clean.columns]
    missing = [column for column in REQUIRED_COLUMNS if column not in clean.columns]
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(missing)}.")
    if clean[list(REQUIRED_COLUMNS)].isnull().any().any():
        raise DataValidationError("Required values cannot be blank.")
    clean["location_id"] = clean["location_id"].astype(str).str.strip()
    clean["name"] = clean["name"].astype(str).str.strip()
    if (clean["location_id"] == "").any() or (clean["name"] == "").any():
        raise DataValidationError("Location IDs and names cannot be blank.")
    if clean["location_id"].duplicated().any():
        duplicates = sorted(clean.loc[clean["location_id"].duplicated(False), "location_id"].unique())
        raise DataValidationError(f"Duplicate location IDs: {', '.join(duplicates)}.")
    for column in ("latitude", "longitude"):
        try:
            clean[column] = pd.to_numeric(clean[column], errors="raise")
        except (TypeError, ValueError) as exc:
            raise DataValidationError(f"Column '{column}' must contain numbers.") from exc
    for row_number, row in clean.iterrows():
        try:
            validate_coordinate(float(row["latitude"]), float(row["longitude"]))
        except ValueError as exc:
            raise DataValidationError(f"Row {row_number + 2}: {exc}") from exc
    for column in OPTIONAL_COLUMNS:
        if column not in clean:
            clean[column] = None
        else:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
            if (clean[column].dropna() < 0).any():
                raise DataValidationError(f"Column '{column}' cannot contain negative values.")
    return clean[[*REQUIRED_COLUMNS, *OPTIONAL_COLUMNS]].reset_index(drop=True)


def frame_to_locations(frame: pd.DataFrame) -> list[Location]:
    clean = validate_delivery_frame(frame)
    locations: list[Location] = []
    for row in clean.itertuples(index=False):
        locations.append(Location(
            location_id=row.location_id,
            name=row.name,
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            priority=None if pd.isna(row.priority) else int(row.priority),
            service_duration=None if pd.isna(row.service_duration) else float(row.service_duration),
        ))
    return locations
