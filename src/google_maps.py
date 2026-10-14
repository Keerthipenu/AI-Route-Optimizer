from __future__ import annotations

import html
import json
from typing import Mapping, Sequence
from urllib.parse import urlencode

from .integrations import RoadRoute
from .models import AlgorithmResult, Location


def google_maps_html(
    result: AlgorithmResult,
    locations: Sequence[Location],
    api_key: str,
    road_route: RoadRoute | None = None,
    vehicles: Sequence[Mapping[str, object]] | None = None,
    height: int = 520,
) -> str:
    """Build an isolated Google Maps view for Streamlit's HTML component."""
    key = api_key.strip()
    if not key:
        raise ValueError("A Google Maps API key is required.")

    route_locations = [locations[index] for index in result.route]
    path = (
        [{"lat": latitude, "lng": longitude} for latitude, longitude in road_route.coordinates]
        if road_route
        else [{"lat": item.latitude, "lng": item.longitude} for item in route_locations]
    )

    markers = []
    seen: set[int] = set()
    for sequence, location_index in enumerate(result.route):
        if location_index in seen:
            continue
        seen.add(location_index)
        location = locations[location_index]
        is_depot = sequence == 0
        markers.append(
            {
                "lat": location.latitude,
                "lng": location.longitude,
                "label": "D" if is_depot else str(sequence),
                "title": location.name,
                "details": (
                    f"<strong>{html.escape(location.name)}</strong><br>"
                    f"{html.escape(location.location_id)} · {'Depot' if is_depot else f'Stop {sequence}'}"
                ),
                "depot": is_depot,
            }
        )

    vehicle_markers = []
    for vehicle in vehicles or []:
        vehicle_id = str(vehicle.get("vehicle_id", "Vehicle"))
        status = str(vehicle.get("reported_status", "Status unavailable"))
        vehicle_markers.append(
            {
                "lat": float(vehicle["latitude"]),
                "lng": float(vehicle["longitude"]),
                "label": "V",
                "title": vehicle_id,
                "details": f"<strong>{html.escape(vehicle_id)}</strong><br>{html.escape(status)}",
            }
        )

    payload = json.dumps(
        {"path": path, "markers": markers, "vehicles": vehicle_markers},
        ensure_ascii=True,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    script_url = "https://maps.googleapis.com/maps/api/js?" + urlencode(
        {
            "key": key,
            "loading": "async",
            "callback": "initMap",
            "v": "weekly",
            "libraries": "marker",
            "auth_referrer_policy": "origin",
        }
    )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    html, body, #map {{ height: 100%; margin: 0; background: #171a17; }}
    #map {{ min-height: {int(height)}px; border-radius: 10px; }}
    #error {{ display:none; box-sizing:border-box; min-height:{int(height)}px; padding:24px;
      color:#e9ece4; background:#171a17; border:1px solid #3a4037; font:14px system-ui; }}
  </style>
</head>
<body>
  <div id="map" aria-label="Optimized delivery route on Google Maps"></div>
  <div id="error" role="alert">Google Maps could not load. Check the API key, Maps JavaScript API access, billing, network connection, and browser referrer restrictions.</div>
  <script>
    const data = {payload};
    window.gm_authFailure = showError;
    function showError() {{
      document.getElementById("map").style.display = "none";
      document.getElementById("error").style.display = "block";
    }}
    async function initMap() {{
      try {{
        const {{ Map, InfoWindow }} = await google.maps.importLibrary("maps");
        const {{ AdvancedMarkerElement, PinElement }} = await google.maps.importLibrary("marker");
        const map = new Map(document.getElementById("map"), {{
          center: data.path[0], zoom: 12, mapId: "DEMO_MAP_ID",
          streetViewControl: false, mapTypeControl: true, fullscreenControl: true
        }});
        const bounds = new google.maps.LatLngBounds();
        data.path.forEach(point => bounds.extend(point));
        new google.maps.Polyline({{
          path: data.path, map, geodesic: {str(road_route is None).lower()},
          strokeColor: "#78A800", strokeOpacity: 0.95, strokeWeight: 5
        }});
        const info = new InfoWindow();
        data.markers.forEach(item => {{
          const pin = new PinElement({{
            glyphText: item.label,
            background: item.depot ? "#20251f" : "#c7f464",
            borderColor: "#20251f", glyphColor: item.depot ? "#c7f464" : "#20251f",
            scale: item.depot ? 1.25 : 1.05
          }});
          const marker = new AdvancedMarkerElement({{ map, position: item, title: item.title, content: pin }});
          marker.addListener("click", () => {{ info.setContent(item.details); info.open({{map, anchor: marker}}); }});
        }});
        data.vehicles.forEach(item => {{
          bounds.extend(item);
          const pin = new PinElement({{ glyphText: item.label, background: "#f39a55", borderColor: "#5c2b12", glyphColor: "#20251f", scale: 1.15 }});
          const marker = new AdvancedMarkerElement({{ map, position: item, title: item.title, content: pin }});
          marker.addListener("click", () => {{ info.setContent(item.details); info.open({{map, anchor: marker}}); }});
        }});
        if (!bounds.isEmpty()) map.fitBounds(bounds, 48);
      }} catch (error) {{ console.error(error); showError(); }}
    }}
  </script>
  <script async src="{html.escape(script_url, quote=True)}" onerror="showError()"></script>
</body>
</html>"""
