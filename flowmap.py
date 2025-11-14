# flowmap_debug_demo.py
from collections import defaultdict, deque
from itertools import product

# ---------------- Topological sort ----------------
def topo_sort(graph):
    # indegree = number of fanins
    indeg = {n: len(graph[n]) for n in graph}
    # build fanouts
    fanouts = defaultdict(list)
    for v, fins in graph.items():
        for u in fins:
            fanouts[u].append(v)

    q = deque([n for n, d in indeg.items() if d == 0])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for w in fanouts[u]:
            indeg[w] -= 1
            if indeg[w] == 0:
                q.append(w)

    if len(order) != len(graph):
        raise ValueError("Graph is not a DAG (cycle detected).")
    return order

# --------------- Cut utilities -------------------
def minimalize_cuts(cuts):
    """Keep only set-minimal cuts (remove supersets & dups)."""
    fs = [frozenset(c) for c in cuts]
    keep = []
    for i, c in enumerate(fs):
        dom = False
        for j, d in enumerate(fs):
            if i == j:
                continue
            if d.issubset(c):
                # if another cut is a subset (or equal), drop c
                if d != c or j < i:
                    dom = True
                    break
        if not dom:
            keep.append(set(c))
    # dedup preserving order
    out, seen = [], set()
    for c in keep:
        f = frozenset(c)
        if f not in seen:
            out.append(c)
            seen.add(f)
    return out

def primary_inputs(graph):
    return {n for n, fins in graph.items() if len(fins) == 0}

def detect_outputs(graph):
    all_fins = {u for fins in graph.values() for u in fins}
    return [n for n in graph if n not in all_fins]

# --------- FlowMap-style labeling + cover ----------
def flowmap_label_and_cover(graph, K, outputs=None, vendor_pack_shortcut=False, verbose=True):
    """
    graph: dict node -> list of fanins
    K: LUT input size (e.g., 6 for Xilinx 6-LUT)
    outputs: optional list of sink nodes; if None, auto-detect
    vendor_pack_shortcut: if True, any node whose distinct *primary inputs*
                          are <= K is labeled as 1 and gets a single LUT
    verbose: print per-node cut evaluation
    """
    if K < 1:
        raise ValueError("K must be >= 1")

    topo = topo_sort(graph)
    PIs = primary_inputs(graph)
    if outputs is None:
        outputs = detect_outputs(graph)

    # Helpers to compute distinct PIs feeding a node (for optional shortcut)
    fanin_cache = {}
    def pis_reaching(v):
        if v in fanin_cache:
            return fanin_cache[v]
        if v in PIs:
            fanin_cache[v] = {v}
            return fanin_cache[v]
        s = set()
        for u in graph[v]:
            s |= pis_reaching(u)
        fanin_cache[v] = s
        return s

    node_cuts = {}
    labels = {}
    chosen_cut = {}

    # Labeling phase
    for v in topo:
        if v in PIs:
            node_cuts[v] = [{v}]
            labels[v] = 0
            chosen_cut[v] = {v}
            if verbose:
                print(f"[{v}] PI -> label=0, cuts={{{{{v}}}}}")
            continue

        fins = graph[v]

        # Optional vendor-like packing: if all distinct PIs feeding v <= K,
        # treat v as computable in one LUT over those PIs.
        if vendor_pack_shortcut:
            pis = pis_reaching(v)
            if len(pis) <= K:
                node_cuts[v] = [set(pis)]  # single cut of direct PIs
                labels[v] = 1 + max(labels[u] for u in pis) if pis - PIs else 1
                chosen_cut[v] = set(pis)
                if verbose:
                    lbls = [labels[u] for u in pis]
                    print(f"[{v}] vendor_pack_shortcut: PIs={sorted(pis)} "
                          f"leaf_labels={lbls} -> label={labels[v]} (chosen={sorted(pis)})")
                continue

        # Build candidate cuts by combining fanin cuts (cartesian product)
        prod = product(*(node_cuts[fi] for fi in fins))
        candidate = []
        for combo in prod:
            U = set().union(*combo)
            if len(U) <= K:
                candidate.append(U)

        # Also consider the trivial cut (immediate fanins)
        triv = set(fins)
        if len(triv) <= K:
            candidate.append(triv)

        candidate = minimalize_cuts(candidate)

        # Evaluate labels via the FlowMap recurrence
        best_label, best_cut = None, None
        if verbose:
            print(f"[{v}] candidates:")
        for C in candidate:
            leaf_labels = [labels[u] for u in C]
            depth_via_C = 1 + max(leaf_labels) if leaf_labels else 1
            if verbose:
                print(f"   - cut={sorted(C)} leaf_labels={leaf_labels} "
                      f"max={max(leaf_labels) if leaf_labels else 0} => label={depth_via_C}")
            if best_label is None or depth_via_C < best_label:
                best_label, best_cut = depth_via_C, C

        if best_label is None:
            raise RuntimeError(f"No K-feasible cuts for node {v} with K={K}")

        node_cuts[v] = candidate
        labels[v] = best_label
        chosen_cut[v] = best_cut
        if verbose:
            print(f"   => CHOSEN cut={sorted(best_cut)} -> label({v})={best_label}")

    # Back-trace cover from outputs
    covered = set()
    LUTs = []
    def place(v):
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
    return labels, chosen_cut, LUTs

# ------------------- Demo -----------------------
if __name__ == "__main__":
    graph = {
        "a": [],
        "b": [],
        "c": [],
        "and1": ["a", "b"],   # and1 = a & b
        "or1":  ["and1", "c"] # or1  = and1 | c  (final)
    }

    for K in [2, 3, 6]:
        print("\n" + "="*60)
        print(f"Mapping with K = {K} (strict cut-based)")
        labels, chosen_cut, LUTs = flowmap_label_and_cover(graph, K, verbose=True, vendor_pack_shortcut=False)
        print("Labels:")
        for n in sorted(labels, key=lambda x: (labels[x], x)):
            print(f"  {n}: L{labels[n]}")
        print("LUT cover:")
        for lut in LUTs:
            print(f"  L{lut['level']}  {lut['output']} <= {lut['inputs']}")

    print("\n" + "="*60)
    print(f"Mapping with K = 6 (with vendor_pack_shortcut)")
    labels, chosen_cut, LUTs = flowmap_label_and_cover(graph, 6, verbose=True, vendor_pack_shortcut=True)
    print("Labels:")
    for n in sorted(labels, key=lambda x: (labels[x], x)):
        print(f"  {n}: L{labels[n]}")
    print("LUT cover:")
    for lut in LUTs:
        print(f"  L{lut['level']}  {lut['output']} <= {lut['inputs']}")
