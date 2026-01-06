## LUT Mapping Optimization using FlowMap

## Overview
This repository contains a **Python-based implementation of FPGA LUT technology mapping**
using the **FlowMap** and **FlowMap-r** algorithms for **delay optimization and depth-preserving
area recovery**.

The project demonstrates how combinational logic (modeled as a DAG) can be optimally
mapped onto **K-input LUTs**, with correctness validated through **Verilog simulation and
FPGA synthesis**.

> 📄 **All theoretical background, algorithm details, figures, and results are documented
in the project report. Please refer to the report for full explanations and analysis.**

---

## Repository Structure

### Python (Mapping Algorithms)
- `BuildMUX.py` – Generates a DAG for an N:1 multiplexer
- `flowmap.py` – Implements depth-optimal LUT mapping (FlowMap)
- `flowmap-r.py` – Implements depth-preserving area recovery (FlowMap-r)

### Verilog (Validation)
- `Direct_Result.v` – Unoptimized reference design
- `Optimized_MUX.v` – FlowMap-optimized LUT-mapped design
- `tb.v` – Testbench for functional verification

---

## How to Run

### 1. Run the mapping pipeline
```bash
python BuildMUX.py
python flowmap.py
python flowmap-r.py
