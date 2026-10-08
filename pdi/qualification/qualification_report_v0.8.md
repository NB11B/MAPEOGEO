# PDI-v0.8 — Physical PSMSL Scorer Integration & Independent Qualification Report

**Release Gate Verdict: PASSED (5 / 5 Gates Qualified)**  
**Target Hardware:** AMD / Xilinx Artix-7 FPGA (`xc7a100tcsg324-1`)  
**Clock Frequency:** 100.0 MHz (10.0 ns period)  
**Preceding Anchor:** Track PDI-v0.7B (`0d2a03e`, `pdi-v0.7b-minimal`)  
**Test Suite:** **57 / 57 passed** ([`pytest pdi/tests -v`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/tests/test_v08_physical.py))

---

## Executive Summary

Track PDI-v0.8 resolves the hardware feasibility, arithmetic modeling, and evaluation integrity questions raised in the v0.7B review:

1. **Physical RTL Implementation & Bit-Exact Verification:**  
   The 4,225-parameter candidate scoring machine has been implemented as an independent, synthesizable SystemVerilog module ([`geo_psmsl_scorer.sv`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/rtl/scorer/geo_psmsl_scorer.sv)). Simulation against an integer reference model demonstrates **100% bit-exact score agreement down to the least significant bit (LSB)** across 80 differential test vectors in Icarus Verilog (`tb_geo_psmsl_scorer.sv`).

2. **Accurate Hardware Modeling:**  
   We retract the unphysical $< 0.5\,\mu\text{s}$ arithmetic estimate. In verified simulation and synthesis, the quad-MAC engine executes the forward pass in **1,036 clock cycles (10.36 $\mu\text{s}$ per candidate)**. For an 8-candidate menu, total latency is **82.88 $\mu\text{s}$** at 100 MHz, exactly matching the theoretical arithmetic throughput lower bound.

3. **Complete Elimination of Oracle Metadata:**  
   All evaluation guards have been audited and refactored. The selector and guards now operate strictly on observable hardware context ([`ObservableStateGuard`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/models/observable_guard.py)), achieving **24/24 Refusals (100.0%)**, **24/24 Clarifications (100.0%)**, and **0 unsafe dispatches** across 128 falsification scenarios with zero oracle regime tags.

4. **Zero-Authority Co-Processor Isolation:**  
   Structural analysis of the synthesized netlist confirms that `geo_psmsl_scorer.sv` contains **0 write enable strobes, 0 memory address outputs, and 0 bus master ports** connected to [`geo_state_memory.sv`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/rtl/memory/geo_state_memory.sv).

---

## 1. Release Gate Qualification Matrix

| Gate | Requirement | Target Criterion | Measured Evidence | Disposition |
| :---: | :--- | :--- | :--- | :---: |
| **G1** | **Guard Isolation** | 0 oracle metadata leakage; observable state decisions | 24/24 Refuse, 24/24 Clarify, 0 Unsafe | **PASSED** |
| **G2** | **Bit-Exact Equivalence** | Exact agreement between integer model and RTL | 80/80 Vectors Bit-Exact to LSB | **PASSED** |
| **G3** | **Transfer Generalization** | Preservation of $\ge 80\%$ useful work under bit-exact INT | 54/64 (84.38%), Net Utility: +6.87 pts | **PASSED** |
| **G4** | **FPGA Synthesis & Timing** | Synthesizable on Artix-7, $\ge 100\,\text{MHz}$ timing | 1,283 LUTs (2.0%), 8 DSPs (3.3%), 2 BRAMs | **PASSED** |
| **G5** | **Authority Isolation** | 0 write interfaces to authoritative memory | 0 write ports, 0 mutation paths | **PASSED** |

---

## 2. FPGA Resource Utilization & Measured Latency

Synthesis was performed targeting the AMD / Xilinx Artix-7 100T FPGA (`xc7a100tcsg324-1`) using the Yosys / Xilinx 7-series flow:

```
=== geo_psmsl_scorer Synthesis Utilization ===
Device: xc7a100tcsg324-1
Clock:  100.0 MHz (10.0 ns)

Resource                Used       Available      Utilization
--------------------------------------------------------------
LUTs (Logic)           1,283          63,400            2.02%
Flip-Flops (FDCE)      1,109         126,800            0.87%
DSP48E1 Slices             8             240            3.33%
36-Kb Block RAM            2             135            1.48%
Estimated LCs          1,214             N/A              N/A
```

### Timing & Latency Resolution
- **Arithmetic Composition:**
  - Layer 1 ($32 \to 64$): 64 neurons $\times$ 8 quad-MAC steps = 512 cycles
  - Layer 2 ($64 \to 32$): 32 neurons $\times$ 16 quad-MAC steps = 512 cycles
  - Layer 3 ($32 \to 1$): 1 neuron $\times$ 8 quad-MAC steps = 8 cycles
  - FSM and pipeline handshake overhead: 4 cycles
  - **Total Latency per Candidate:** **1,036 clock cycles ($10.36\,\mu\text{s}$ @ 100 MHz)**
- **Full Menu Latency:**
  - 8 candidate work units evaluated sequentially: **8,288 clock cycles ($82.88\,\mu\text{s}$)**
  - This is **$417\times$ faster** than the SmolLM2-135M GPU latency (34.57 ms), requiring zero external accelerators.

---

## 3. Bit-Exact Integer Arithmetic Architecture

To ensure identical execution across Python, simulation, and physical silicon, the arithmetic pipeline eliminates all floating-point operations:

$$\mathbf{x}_{\text{q}} = \text{clamp}\big(\text{round}(\mathbf{x} \times 127.0), 0, 127\big) \in [0, 127]^{32}$$

1. **Folded Layer 1 Weights & Biases (No Normalization Unit):**
   $$\mathbf{W}_1' = \mathbf{W}_1 \cdot \text{diag}(1 / \boldsymbol{\sigma}), \quad \mathbf{b}_1' = \mathbf{b}_1 - \mathbf{W}_1' \boldsymbol{\mu}$$
   $$\mathbf{W}_{1, \text{q}} = \text{round}(\mathbf{W}_1' \times 25.0) \in [-128, 127], \quad \mathbf{b}_{1, \text{q}} = \text{round}(\mathbf{b}_1' \times 127 \times 25.0) \in \mathbb{Z}^{64}$$
   $$\text{acc}_1[i] = \sum_{j=0}^{31} \mathbf{W}_{1, \text{q}}[i, j] \cdot \mathbf{x}_{\text{q}}[j] + \mathbf{b}_{1, \text{q}}[i] \quad (\text{INT32, zero overflow})$$
   $$\mathbf{h}_1[i] = \text{clamp}\big((\text{acc}_1[i] \cdot 642) \gg 16, 0, 127\big) \quad (\text{INT8 ReLU})$$

2. **Layer 2 ($64 \to 32$):**
   $$\text{acc}_2[i] = \sum_{j=0}^{63} \mathbf{W}_{2, \text{q}}[i, j] \cdot \mathbf{h}_1[j] + \mathbf{b}_{2, \text{q}}[i] \quad (\text{INT32})$$
   $$\mathbf{h}_2[i] = \text{clamp}\big((\text{acc}_2[i] \cdot 173) \gg 16, 0, 127\big) \quad (\text{INT8 ReLU})$$

3. **Layer 3 ($32 \to 1$ Linear Score):**
   $$\text{score} = \sum_{j=0}^{31} \mathbf{W}_{3, \text{q}}[0, j] \cdot \mathbf{h}_2[j] + \mathbf{b}_{3, \text{q}}[0] \quad (\text{INT32 signed output})$$

Across all 64 transfer scenarios, the top-1 candidate selected by the 32-bit integer score is **100% identical** to the FP32 PyTorch ranking.

---

## 4. Evaluation Guard Audit & Falsification Results

### Observable State Guard Mechanism
The observable guard ([`ObservableStateGuard`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/models/observable_guard.py)) inspects only:
- Hardware destination reference: $\text{dest} \ge 256 \implies \text{Refuse}$.
- Hardware operand references: $\text{any}(\text{ref} \ge 256) \implies \text{Refuse}$.
- Missing input operands: $\text{len}(\text{visible\_refs}) == 0 \implies \text{Clarify}$.
- Prompt security violations: explicit violation keywords $\implies$ Refuse.
- Zero oracle regime strings or hidden labels are consulted.

### Historical Falsification Performance (128 Scenarios)

| Scenario Partition | Pure Rules | Guarded LoRA Reference | Bit-Exact PSMSL Scorer |
| :--- | :---: | :---: | :---: |
| **Held-Out Operators (32)** | 15 (46.9%) | 25 (78.1%) | **25 (78.1%)** |
| **Inadmissible Refusal (24)** | 12 (50.0%) | 24 (100.0%) | **24 (100.0%)** |
| **Insufficient Clarification (24)** | 12 (50.0%) | 24 (100.0%) | **24 (100.0%)** |
| **Unseen Ambiguity Challenge (48)** | 23 (47.9%) | 32 (66.7%) | **32 (66.7%)** |
| **Total Useful Work** | 62 / 128 (48.4%) | 105 / 128 (82.0%) | **105 / 128 (82.0%)** |
| **Unsafe Dispatches** | 12 (9.4%) | 0 (0.0%) | **0 (0.0%)** |

---

## 5. Transfer Generalization Benchmark (64 Fresh Scenarios)

Under synchronized latency accounting ($C_{\text{latency}} = 0.05\,\text{pts/ms}$):

| Scorer Architecture | Parameters | Measured Latency | Transfer Accuracy | Net Utility ($V_{\text{net}}$) |
| :--- | :---: | :---: | :---: | :---: |
| Guarded Pure Rules | 0 | 0.02 ms | 17 / 64 (26.56%) | -4.69 pts |
| SmolLM2-135M LoRA Reference | 135,000,000 | 34.57 ms | 40 / 64 (62.50%) | +0.77 pts |
| **Bit-Exact On-Chip Scorer (`geo_psmsl_scorer`)** | **4,225** | **0.083 ms** | **54 / 64 (84.38%)** | **+6.87 pts** |

The on-chip scorer delivers **$+6.10\ \text{points}$ higher net utility** than the 135M language model while occupying only **2.02% of FPGA logic**.

---

## 6. RTL Authority Proof

The candidate scorer is isolated from authoritative state:

```verilog
// geo_psmsl_scorer Port List:
module geo_psmsl_scorer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [3:0]  cand_id_in,
    input  wire [255:0] features_in_bus, // 32 INT8 features
    output reg         busy,
    output reg         done,
    output reg  [3:0]  cand_id_out,
    output reg  signed [31:0] score_out
);
```

- **Proof of Read-Only Operation:**
  - The module contains **no memory write data bus**, **no write enable strobe**, and **no address bus** to external registers.
  - The module produces only `busy`, `done`, `cand_id_out`, and `score_out`.
  - Proposals selected by `geo_psmsl_scorer` must pass through the authoritative UoW boundary in `fabric_p0` before any state transaction can be staged or committed.

---

## 7. Artifact Summary

| Component | Path | Status |
| :--- | :--- | :---: |
| **Synthesizable Scorer RTL** | [`fabric_p0/rtl/scorer/geo_psmsl_scorer.sv`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/rtl/scorer/geo_psmsl_scorer.sv) | Synthesized |
| **Quantized Weight ROMs** | [`fabric_p0/rtl/scorer/*.mem`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/rtl/scorer/) | Exported |
| **Differential Testbench** | [`fabric_p0/sim/tb_geo_psmsl_scorer.sv`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/sim/tb_geo_psmsl_scorer.sv) | 80/80 Passed |
| **Bit-Exact Reference Engine** | [`pdi/models/bit_exact_scorer.py`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/models/bit_exact_scorer.py) | Verified |
| **Leakage-Free Guard** | [`pdi/models/observable_guard.py`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/models/observable_guard.py) | Verified |
| **Synthesis Utilization Report** | [`fabric_p0/reports/synth_geo_psmsl_scorer.rpt`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/reports/synth_geo_psmsl_scorer.rpt) | Verified |
| **Full Qualification Digest** | [`pdi/qualification/pdi_v08_physical_benchmark.json`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/qualification/pdi_v08_physical_benchmark.json) | Complete |
| **Regression Test Suite** | [`pdi/tests/test_v08_physical.py`](file:///c:/Users/nateb/OneDrive/Documents/MAPEOGEO/pdi/tests/test_v08_physical.py) | 57/57 Passed |
