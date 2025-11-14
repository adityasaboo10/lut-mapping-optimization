r"""
flowmap_r_final.py

Depth‑optimal K‑LUT mapping (FlowMap) + depth‑preserving area recovery (FlowMap‑r / area‑flow)
----------------------------------------------------------------------------------------------
Fixes included:
  • Area‑recovery now iterates in *topological order* (not reversed), so
    fanin area_flow values are available when needed.
  • Explicit, safe call patterns in __main__.
  • Minor typing/printing cleanups.
"""
from __future__ import annotations
from collections import defaultdict, deque
from itertools import product
from typing import Dict, List, Set, Tuple, Optional

# =========================
# Graph / Utility routines
# =========================

def topo_sort(graph: Dict[str, List[str]]) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return a topological order for DAG: node -> [fanins], and fanouts map."""
    indeg = {n: len(graph[n]) for n in graph}
    fanouts: Dict[str, List[str]] = defaultdict(list)
    for v, fins in graph.items():
        for u in fins:
            fanouts[u].append(v)
    q = deque([n for n, d in indeg.items() if d == 0])
    order: List[str] = []
    while q:
        u = q.popleft()
        order.append(u)
        for w in fanouts[u]:
            indeg[w] -= 1
            if indeg[w] == 0:
                q.append(w)
    if len(order) != len(graph):
        raise ValueError("Graph is not a DAG")
    return order, fanouts


def primary_inputs(graph: Dict[str, List[str]]) -> Set[str]:
    return {n for n, fins in graph.items() if len(fins) == 0}


def detect_outputs(graph: Dict[str, List[str]]) -> List[str]:
    all_fins = {u for fins in graph.values() for u in fins}
    return [n for n in graph if n not in all_fins]


# =========================
# Cut handling
# =========================

def minimalize_cuts(cuts: List[Set[str]]) -> List[Set[str]]:
    """Keep only set‑minimal cuts (remove supersets & duplicates)."""
    fs = [frozenset(c) for c in cuts]
    keep: List[Set[str]] = []
    for i, c in enumerate(fs):
        dominated = False
        for j, d in enumerate(fs):
            if i == j:
                continue
            if d.issubset(c):
                if d != c or j < i:
                    dominated = True
                    break
        if not dominated:
            keep.append(set(c))
    out: List[Set[str]] = []
    seen: Set[frozenset] = set()
    for c in keep:
        f = frozenset(c)
        if f not in seen:
            out.append(c)
            seen.add(f)
    return out


def enumerate_minimal_kcuts(
    graph: Dict[str, List[str]],
    K: int,
    cut_limit: Optional[int] = None,
) -> Dict[str, List[Set[str]]]:
    """Enumerate set‑minimal K‑feasible cuts per node."""
    if K < 1:
        raise ValueError("K must be >= 1")
    topo, _ = topo_sort(graph)
    PIs = primary_inputs(graph)

    node_cuts: Dict[str, List[Set[str]]] = {}
    for v in topo:
        if v in PIs:
            node_cuts[v] = [{v}]
            continue
        fins = graph[v]
        cand: List[Set[str]] = []
        pools = [node_cuts[fi] for fi in fins]
        for combo in product(*pools):
            U = set().union(*combo)
            if len(U) <= K:
                cand.append(U)
        triv = set(fins)
        if len(triv) <= K:
            cand.append(triv)
        cand = minimalize_cuts(cand)
        if cut_limit is not None and len(cand) > cut_limit:
            cand.sort(key=lambda s: (len(s), tuple(sorted(s))))
            cand = cand[:cut_limit]
        node_cuts[v] = cand
    return node_cuts


# =========================
# FlowMap depth labels
# =========================

def flowmap_labels(
    graph: Dict[str, List[str]],
    K: int,
    node_cuts: Optional[Dict[str, List[Set[str]]]] = None,
) -> Tuple[Dict[str, int], Dict[str, List[Set[str]]], Dict[str, Dict[frozenset, int]]]:
    """Compute depth‑optimal labels per FlowMap recurrence."""
    if node_cuts is None:
        node_cuts = enumerate_minimal_kcuts(graph, K)
    topo, _ = topo_sort(graph)
    PIs = primary_inputs(graph)

    labels: Dict[str, int] = {}
    cut_depth: Dict[str, Dict[frozenset, int]] = {v: {} for v in graph}

    for v in topo:
        if v in PIs:
            labels[v] = 0
            cut_depth[v][frozenset({v})] = 0
            continue
        best_lbl: Optional[int] = None
        for C in node_cuts[v]:
            d = 1 + max(labels[u] for u in C) if C else 1
            cut_depth[v][frozenset(C)] = d
            if best_lbl is None or d < best_lbl:
                best_lbl = d
        if best_lbl is None:
            raise RuntimeError(f"No K‑feasible cuts for {v} with K={K}")
        labels[v] = best_lbl
    return labels, node_cuts, cut_depth


# =========================
# Area‑flow recovery (depth‑preserving)
# =========================

def compute_refcounts(graph: Dict[str, List[str]]) -> Dict[str, int]:
    """Approximate refcounts by structural fanouts; avoid zeros."""
    _, fanouts = topo_sort(graph)
    return {n: max(1, len(fanouts[n])) for n in graph}


def area_recovery(
    graph: Dict[str, List[str]],
    K: int,
    labels: Dict[str, int],
    node_cuts: Dict[str, List[Set[str]]],
    cut_depth: Dict[str, Dict[frozenset, int]],
) -> Tuple[Dict[str, Set[str]], Dict[str, float]]:
    """
    Depth‑preserving area minimization using area_flow DP.

    Chooses per node a cut with:
        depth_via_cut <= labels[v]   (do not increase depth)
        minimal area_flow

    area_flow(v) = 1 + sum_{u in C \\ PIs} area_flow(u) / refcount(u)
    """
    topo, _ = topo_sort(graph)
    PIs = primary_inputs(graph)
    refcnt = compute_refcounts(graph)

    area_flow: Dict[str, float] = {}
    best_cut_area: Dict[str, Set[str]] = {}

    # ✅ Use normal topological order so fanin costs exist when needed
    for v in topo:
        if v in PIs:
            area_flow[v] = 0.0
            best_cut_area[v] = {v}
            continue

        best_cost: Optional[float] = None
        best_cut: Optional[Set[str]] = None

        for C in node_cuts[v]:
            d = cut_depth[v][frozenset(C)]
            if d > labels[v]:
                continue  # depth‑preserving filter
            cost = 1.0
            for u in C:
                if u not in PIs:
                    cost += area_flow[u] / refcnt[u]
            if best_cost is None or cost < best_cost:
                best_cost, best_cut = cost, C

        if best_cut is None:
            # Fallback: among minimum‑depth cuts, pick by area proxy
            min_d = min(cut_depth[v].values())
            cands = [set(c) for c, dv in cut_depth[v].items() if dv == min_d]
            def proxy(C2: Set[str]) -> float:
                return 1.0 + sum(area_flow.get(u, 0.0) / max(1, refcnt.get(u, 1)) for u in C2 if u not in PIs)
            best_cut = min(cands, key=proxy)
            best_cost = proxy(best_cut)

        best_cut_area[v] = best_cut
        area_flow[v] = best_cost

    return best_cut_area, area_flow


# =========================
# LUT cover construction
# =========================

def build_cover(
    graph: Dict[str, List[str]],
    chosen_cut: Dict[str, Set[str]],
    labels: Dict[str, int],
    outputs: Optional[List[str]] = None,
) -> List[Dict[str, object]]:
    """Back‑trace from outputs to create a LUT cover following chosen cuts."""
    if outputs is None:
        outputs = detect_outputs(graph)
    PIs = primary_inputs(graph)
    covered: Set[str] = set()
    LUTs: List[Dict[str, object]] = []

    def place(v: str) -> None:
        if v in covered or v in PIs:
            return
        C = chosen_cut[v]
        LUTs.append({"output": v, "inputs": sorted(C), "level": labels[v]})
        covered.add(v)
        for u in C:
            if u not in PIs:
                place(u)

    for po in outputs:
        place(po)

    LUTs.sort(key=lambda x: (x["level"], x["output"]))
    return LUTs


# =========================
# End‑to‑end convenience
# =========================

def map_with_area_optimized_flow(
    graph: Dict[str, List[str]],
    K: int,
    outputs: Optional[List[str]] = None,
    cut_limit: Optional[int] = None,
    verbose: bool = True,
) -> Tuple[Dict[str, int], Dict[str, Set[str]], List[Dict[str, object]]]:
    """
    1) Enumerate minimal K‑cuts (optionally limited)
    2) FlowMap labels (depth‑optimal)
    3) Area‑flow recovery (depth‑preserving)
    4) Build LUT cover
    """
    node_cuts = enumerate_minimal_kcuts(graph, K, cut_limit=cut_limit)
    labels, node_cuts, cut_depth = flowmap_labels(graph, K, node_cuts=node_cuts)
    best_cut_area, area_flow = area_recovery(graph, K, labels, node_cuts, cut_depth)
    LUTs = build_cover(graph, best_cut_area, labels, outputs=outputs)

    if verbose:
        print("Labels (depth):")
        for n in sorted(labels, key=lambda x: (labels[x], x)):
            print(f"  {n}: L{labels[n]}")
        print("\nChosen cuts (area‑optimized, depth‑preserving):")
        for n in labels:
            if n in primary_inputs(graph):
                continue
            print(f"  {n}: {sorted(best_cut_area[n])}")
        print("\nLUT cover:")
        for lut in LUTs:
            print(f"  L{lut['level']}  {lut['output']} <= {lut['inputs']}")

    return labels, best_cut_area, LUTs


# =========================
# Demo / unit test
# =========================
if __name__ == "__main__":
    graph = {
        "a": [],
        "b": [],
        "c": [],
        "and1": ["a", "b"],
        "or1":  ["and1", "c"],
    }

    for K in [2, 3, 6]:
        print("\n" + "=" * 72)
        print(f"FlowMap‑r mapping with K = {K}")
        labels, chosen_cuts, LUTs = map_with_area_optimized_flow(
            graph=graph,
            K=K,
            outputs=None,
            cut_limit=None,
            verbose=True,
        )

    graph2 = {
        "a": [], "b": [], "c": [], "d": [],
        "and1": ["a", "b"],
        "and2": ["c", "d"],
        "xor1": ["and1", "and2"],
        "or1":  ["and1", "c"],
        "out":  ["xor1", "or1"],
    }
    print("\n" + "=" * 72)
    print("FlowMap‑r on reconvergent example (K=3)")
    labels, chosen_cuts, LUTs = map_with_area_optimized_flow(
        graph=graph2,
        K=3,
        outputs=None,
        cut_limit=None,
        verbose=True,
    )
