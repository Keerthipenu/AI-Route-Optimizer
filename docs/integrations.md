# Live and Road-Network Integrations

ROUTEFORGE remains offline-first. External calls occur only after an explicit user action, have finite timeouts, produce visible provider labels, and fail back to the local workflow without corrupting route data.

## OSRM road routing

Select **Road network · OSRM** and press **Load / refresh road matrix**. ROUTEFORGE calls the OSRM table service for driving distance and duration matrices, then passes the returned distance matrix through the same tested algorithms. The selected route can also request OSRM GeoJSON geometry for a road-shaped plot.

The default endpoint is the public demonstration server and is suitable only for modest educational use. The server field is configurable so a self-hosted or contracted OSRM instance can be used. OSRM durations are routing-profile estimates, not guaranteed live traffic.

## OpenStreetMap Nominatim geocoding

The Delivery Data page offers explicit address search—never autocomplete or background bulk geocoding. The adapter:

- identifies ROUTEFORGE through its User-Agent;
- applies an application-wide one-request-per-second guard;
- caches identical searches;
- returns at most five matches;
- displays OpenStreetMap attribution and the public-service policy;
- warns users not to submit private or confidential addresses.

For production or high-volume use, configure a dedicated geocoder instead of the public service.

## TomTom live traffic

After optimizing a route, expand the live-traffic panel and provide a TomTom Routing API key. The key is held only in the Streamlit session and is never written to disk. An explicit refresh asks TomTom for the fastest car route through the optimized stop order and displays returned travel time, traffic delay, no-traffic time, distance, departure, and arrival values.

No traffic result is shown without a successful provider response. ROUTEFORGE does not infer or manufacture traffic.

## GPS telemetry

The Live Tracking page accepts:

- the committed, visibly labelled sample telemetry;
- an uploaded CSV;
- an HTTP/HTTPS endpoint returning CSV or a JSON array (or `{ "positions": [...] }`).

Required fields are `timestamp`, `vehicle_id`, `latitude`, and `longitude`; `status` is optional. Only the latest position per vehicle is displayed. Stop proximity uses a documented 250 metre radius and is not treated as proof of delivery completion.

Example:

```csv
timestamp,vehicle_id,latitude,longitude,status
2026-10-11T08:10:00Z,VAN-01,12.9218,77.6371,in_transit
```

For continuous production tracking, expose a secured fleet endpoint and use authentication at a reverse proxy or provider layer. Do not put secrets inside uploaded CSV files.
