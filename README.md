## LUT Mapping Optimization using FlowMap
## Description
This project focuses on **FPGA LUT-based delay optimization** using **FlowMap** and **FlowMap-r** algorithms.  
It demonstrates how combinational logic (specifically **K:1 multiplexers**) can be represented as a **Directed Acyclic Graph (DAG)**, decomposed using **K-feasible cuts**, and mapped to **K-input LUTs** with **minimum depth** and improved **area efficiency**.

The project includes:
- Automatic DAG generation for MUX structures
- Depth-optimal LUT mapping using **FlowMap**
- Refinement using **FlowMap-r**
- Functional verification and LUT-count comparison using **Verilog + Vivado**

<br>

## Table of Contents
1. [Project_Files](#project_files)
2. [Concepts_Used](#concepts_used)
3. [Software_Requirements](#software_requirements)
4. [SETUP](#setup)
5. [Usage](#usage)
6. [Results](#results)
7. [Suggestions](#suggestions)

---

## Project_Files

### Python Code (Algorithmic Implementation)
- **`BuildMUX.py`**  
  Generates a DAG representation for a K:1 multiplexer.
- **`flowmap.py`**  
  Implements **FlowMap** for depth-optimal LUT mapping using K-feasible cuts.
- **`flowmap-r.py`**  
  Implements **FlowMap-r**, refining the FlowMap result for LUT count reduction.

### Verilog Code
(inside `Verilog_Code.zip`)
- **`Direct_Result.v`** – Unoptimized combinational design
- **`Optimized_MUX.v`** – Optimized LUT-mapped design
- **`tb.v`** – Testbench for functional verification

### Documentation
- **`Report.pdf`** – Detailed explanation of theory, algorithm, and results
- **`LUT_minimization_PPT.pdf`** – Presentation slides
- **`README.txt`** – Original short instructions (expanded here)

---

## Concepts_Used

- **FPGA LUT Architecture**
- **K-feasible cuts**
- **Directed Acyclic Graph (DAG) modeling**
- **FlowMap algorithm (depth optimal mapping)**
- **FlowMap-r (area refinement)**
- **Logic synthesis and LUT utilization analysis**

---

## Software_Requirements

### Required
- **Python 3.8+**
- **Xilinx Vivado** (for synthesis & LUT count comparison)

### Optional
- Any Verilog simulator (ModelSim / Icarus Verilog)
- Python libraries (if required by scripts):
  - `networkx`
  - `matplotlib`

---

## SETUP

### 1) Clone the repository
```bash
git clone https://github.com/adityasaboo10/lut-mapping-optimization.git
cd lut-mapping-optimization
