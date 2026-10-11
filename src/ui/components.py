from __future__ import annotations

from html import escape

from ..export_utils import route_to_frame
from ..models import AlgorithmResult, Location


def brand(st) -> None:
    st.markdown(
        '<div class="rf-brand"><div class="rf-mark">R</div><div>'
        '<div class="rf-wordmark">ROUTEFORGE</div>'
        '<div class="rf-submark">EXPLAINABLE OPTIMIZATION</div></div></div>',
        unsafe_allow_html=True,
    )


def hero(st, kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="rf-hero"><div class="rf-kicker">{escape(kicker)}</div>'
        f'<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def route_timeline(st, result: AlgorithmResult, locations: list[Location], matrix) -> None:
    frame = route_to_frame(result, locations, matrix)
    st.markdown('<div class="rf-panel"><div class="rf-section">Route timeline</div>', unsafe_allow_html=True)
    for row in frame.itertuples(index=False):
        role = "DEPOT" if row.stop_number == 0 else ("RETURN" if row.location_id == frame.iloc[0]["location_id"] else "DESTINATION")
        st.markdown(
            '<div class="rf-stop">'
            f'<div class="rf-stop-num">{int(row.stop_number):02d}</div>'
            f'<div><div class="rf-stop-name">{escape(str(row.name))}</div>'
            f'<div class="rf-stop-meta">{role} · cumulative {row.cumulative_distance_km:.2f} km</div></div>'
            f'<div class="rf-stop-distance">+{row.leg_distance_km:.2f} km</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


def explanation(result: AlgorithmResult) -> str:
    if result.algorithm == "Nearest Neighbor":
        return "At each stop, the algorithm selected the nearest unvisited destination. This is fast and explainable, but a locally short leg can force an expensive final leg, so global optimality is not guaranteed."
    if result.algorithm == "2-opt":
        swaps = result.metadata.get("accepted_swaps", 0)
        gain = result.metadata.get("improvement_km", 0.0)
        objective = result.metadata.get("objective", "distance_km")
        if objective == "distance_km":
            change = f"removing {gain:.2f} km"
        else:
            change = f"improving the selected {str(objective).replace('_', ' ')} score"
        return f"2-opt began with the greedy route and accepted {swaps} improving segment reversal(s), {change}. It stopped when no tested reversal improved the selected objective; this is a local, not global, optimum."
    if result.algorithm == "Simulated Annealing":
        accepted = result.metadata.get("accepted_moves", 0)
        return f"The annealer proposed neighboring routes and accepted {accepted} moves. Early high temperatures permit some worse moves to escape local optima; cooling gradually makes the search more selective. It does not guarantee a global optimum."
    return "Brute Force enumerated every permitted destination ordering within the configured safety limit. The shortest evaluated route is therefore exact for this constrained instance."
