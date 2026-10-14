import pytest

from src.google_maps import google_maps_html
from src.integrations import RoadRoute
from src.models import AlgorithmResult, Location


def route_result():
    return AlgorithmResult("Test", [0, 1, 0], 2.0, 0.01, 2)


def locations():
    return [
        Location("D", "Depot <HQ>", 12.9, 77.6),
        Location("A", "Stop A", 12.91, 77.61),
    ]


def test_google_maps_html_contains_route_and_escapes_labels():
    output = google_maps_html(route_result(), locations(), "browser-key")
    assert "maps.googleapis.com/maps/api/js" in output
    assert "browser-key" in output
    assert "Depot &lt;HQ&gt;" in output
    assert '"label":"D"' in output
    assert output.count('"title":"Depot <HQ>"') == 1


def test_google_maps_html_uses_road_geometry_and_vehicle_marker():
    road = RoadRoute([(12.9, 77.6), (12.905, 77.605), (12.91, 77.61)], 2.2, 6)
    output = google_maps_html(
        route_result(), locations(), "browser-key", road,
        [{"vehicle_id": "V1", "latitude": 12.905, "longitude": 77.605, "reported_status": "En route"}],
    )
    assert '"lat":12.905,"lng":77.605' in output
    assert '"title":"V1"' in output
    assert "geodesic: false" in output


def test_google_maps_html_requires_key():
    with pytest.raises(ValueError, match="key"):
        google_maps_html(route_result(), locations(), " ")
