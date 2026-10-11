# Algorithms

## Problem model

The application solves a constrained Traveling Salesman Problem over geographic points. The objective is the sum of Haversine distances along the visit sequence. This is tour ordering, not road-network shortest-path search.

The default remains distance minimization. Users can instead select fastest-route scoring or priority-weighted arrival time. Fastest routing uses an OSRM duration matrix when loaded, otherwise a clearly labelled constant-speed assumption. Priority-weighted arrival minimizes the sum of each destination's arrival time multiplied by a priority weight (priority 1 is highest); service duration delays later arrivals. All algorithms compare candidates with the same selected objective while still reporting physical route distance separately.

## Nearest Neighbor

From the depot, choose the closest unvisited destination until none remain. The implementation counts every candidate distance comparison. Time complexity is `O(n²)` and memory use is `O(n)`. It is deterministic (including tie-breaking by index), fast, and useful as a baseline, but a locally shortest leg can create an expensive later leg. It does not guarantee an optimum.

## Brute Force

Enumerate every permitted ordering of intermediate destinations, attach the required start/end constraints, and keep the shortest. Equal-distance optimal routes are counted; deterministic lexicographic tie-breaking chooses the returned route. Time complexity is `O(n! · n)`. Exactness is guaranteed only because the permitted solution space was exhausted. The caller must respect the configurable destination limit; ROUTEFORGE never launches unrestricted factorial work.

## 2-opt

Start from a valid Nearest Neighbor route. For every movable pair of positions, reverse the intermediate segment, accept the best strictly improving candidate, and repeat. Depot and fixed-endpoint positions never move. With `k` passes, the straightforward implementation is approximately `O(k · n³)` here because each of `O(n²)` candidates is remeasured in `O(n)`; a delta-cost refinement could reduce that. The result cannot be worse than its initial route, but it is only locally optimal.

## Simulated Annealing

Start from a valid greedy route. Sample a segment reversal. Improving moves are always accepted; worsening moves are accepted with probability `exp(-Δ/T)`. Multiply temperature by the cooling rate after each proposal and retain the best route seen, not merely the final current route. Runtime is proportional to the configured iteration count and route measurement cost. A seed makes runs reproducible. The method can escape local optima but does not guarantee the global optimum.

## Operation counts

Work metrics deliberately keep their algorithm-specific names: distance comparisons, permutations evaluated, candidate reversals, and neighbor proposals. They are useful within an algorithm, but they are not equivalent units of computational cost across algorithms.
