"""
    Build a k:1 multiplexer using AND/OR gates.
    Returns:
        graph: node -> fanins
        outputs: list with final output node name
        gate_type: node -> gate type ("AND", "OR", "NOT", "PI")
"""

from typing import Dict, List, Tuple
import math

def build_mux(k: int) -> Tuple[Dict[str, List[str]], List[str], Dict[str, str]]:

    graph: Dict[str, List[str]] = {}
    gate_type: Dict[str, str] = {}

    # ----------------------------------------------------------
    # 1) Declare primary inputs: Data lines D0..D(k-1)

    for i in range(k):
        name = f"D{i}"  # to create inputs named D0,D1, etc using f string
        graph[name] = []  # primary input meaning no fanins
        gate_type[name] = "PI"  # thus PI

    # 2) Declare select lines S0..S(log2(k)-1)
    # ----------------------------------------------------------
    sel_bits = math.ceil(math.log2(k))  # compute select lines needed based on k
    for i in range(sel_bits):
        name = f"S{i}"
        graph[name] = []  # primary input
        gate_type[name] = "PI"

    # use counters for proper naming
    not_count = 1
    and_count = 1

    # ----------------------------------------------------------
    # 3) Build selection paths
    #
    # For each i in [0..k-1]:
    #    Convert i to binary (length = sel_bits).
    #    For each bit:
    #        if bit == '1' -> use S[j]
    #        if bit == '0' -> use NOT(S[j])
    #
    #    Then AND together all these select signals with D[i]
    # ----------------------------------------------------------
    and_nodes = []

    for i in range(k):
        binary = format(
            i, f"0{sel_bits}b"
        )  # to generate Select signal equals i (ie for choosing input D(i))

        # Build list of input signals for the AND gate
        and_inputs = []

        for j, bit in enumerate(
            binary
        ):  # this block handels how the select line should be bit by bit based on i
            if bit == "1":
                # use S[j] directly no need for not since needed bit is 1
                and_inputs.append(f"S{j}")
            else:
                # we need NOT(S[j]), as needed bit is 0
                not_name = f"not{not_count}"
                # only create once
                if not_name not in graph:
                    graph[not_name] = [f"S{j}"]  # this creates the NOT gate
                    gate_type[not_name] = "NOT"
                    not_count += 1
                and_inputs.append(not_name)

        # Add the data input Di and thus successfully completing the AND path here by adding Di
        and_inputs.append(f"D{i}")

        # Create the AND gate node for this path
        and_node = f"and{and_count}"   # example when i=2 becomes and2 = AND(...)
        graph[and_node] = and_inputs
        gate_type[and_node] = "AND"
        and_nodes.append(and_node)
        and_count += 1

    # ----------------------------------------------------------
    # 4) OR all AND paths to produce the final output
    #    MODIFIED: Decompose into 2-input OR tree to fit small K
    # ----------------------------------------------------------
    
    current_layer = and_nodes
    or_gate_count = 1
    
    # Iteratively pair up nodes until only one root remains
    while len(current_layer) > 1:
        next_layer = []
        for i in range(0, len(current_layer), 2):
            chunk = current_layer[i : i + 2]
            if len(chunk) == 1:
                # Odd one out, pass it to the next layer
                next_layer.append(chunk[0])
            else:
                # Create a 2-input OR gate
                or_name = f"or{or_gate_count}"
                graph[or_name] = chunk
                gate_type[or_name] = "OR"
                next_layer.append(or_name)
                or_gate_count += 1
        current_layer = next_layer

    # The last remaining node is the final output
    out = current_layer[0] if current_layer else "error" # Handle k=0 if needed, though unlikely

    return graph, [out], gate_type


# ----------------------------------------------------------
# MAIN BLOCK (runs ONLY when file is executed directly)
# ----------------------------------------------------------
if __name__ == "__main__":
    # Generate 4:1 MUX (this will now create a tree of OR gates)
    graph, outputs, gate_type = build_mux(4)

    # Print the graph dictionary items formatted for direct copy-pasting
    for node, fanins in graph.items():
        # Convert list to string and replace single quotes with double quotes for JSON-like style
        formatted_list = str(fanins).replace("'", '"')
        print(f'    "{node}": {formatted_list},')
