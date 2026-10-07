# PDI-135M-v0.1 Repository Audit & Feasibility Assessment

**Status:** Completed Phase 0 Audit  
**Target Repository:** `MAPEOGEO`  
**Branch:** `experiment/pdi-135m-v0.1`  
**Base Model:** `HuggingFaceTB/SmolLM2-135M-Instruct` (rev `12fd25f77366fa6b3b4b768ec3050bf629380bac`)  
**Hardware Trust Boundary:** Probabilistic Untrusted (Host + Model) $\to$ Authoritative Deterministic (MAPEOGEO FPGA P0)  

---

## 1. Executive Summary

This repository audit establishes the empirical baseline, hardware contracts, and interface specifications required to integrate the existing **SmolLM2-135M** model with the **MAPEOGEO P0 FPGA Fabric** under the **Proposal-Disposition Interface (PDI-135M-v0.1)**.

### Core Architectural Invariant
$$\boxed{\text{Probabilistic Proposal } \neq \text{ Authoritative State Mutation}}$$
Neither the LLM inference engine nor the host-side parser possess execution authority. The FPGA fabric remains the sole deterministic arbiter of execution, certification, evidence generation, and authoritative memory mutation.

---

## 2. H3 Baseline Model & Training Audit

The earlier UoW H3 experiment established the foundation for structured operational output.

### 2.1 Model & Tokenizer Identity
- **Base Model:** `HuggingFaceTB/SmolLM2-135M-Instruct`
- **Model Revision:** `12fd25f77366fa6b3b4b768ec3050bf629380bac`
- **Tokenizer:** `HuggingFaceTB/SmolLM2-135M-Instruct` (matching revision, vocabulary size: `49,152`)
- **Weights Location:** Verified offline in local HuggingFace cache (`~/.cache/huggingface/hub/models--HuggingFaceTB--SmolLM2-135M-Instruct`)

### 2.2 Qualified H3 Adapter Baseline
- **H3 Adapter Path:** `C:\Users\nateb\OneDrive\Documents\UoW-v2\checkpoints\uow_h3_native_smollm2_135m_arm_nb`
- **Adapter Format:** PEFT LoRA
- **LoRA Configuration:**
  - Rank ($r$): `8`
  - Alpha ($\alpha$): `16`
  - Dropout: `0.05`
  - Target Modules: `["q_proj", "v_proj"]`
  - Bias: `"none"`
  - Task Type: `CAUSAL_LM`
- **Trainable Parameters:** `460,800` / `134,975,808` total ($0.3414\%$)
- **Adapter Weights File:** `adapter_model.safetensors` (`1,858,776` bytes)
- **Adapter SHA256:** `64d77db036472c86403a1d98490526fc5412d56e8c1640a47fd9eeed5f92ad6a` (verified exact match with manifest)

### 2.3 Prior H3 Experimental Results (Reference)
Evaluated on the 20 family-disjoint holdouts in `UoW-v2`:
- **Valid JSON Serialization:** $20/20$ ($100.0\%$)
- **Exact UoW Dispositions:** $16/20$ ($80.0\%$)
- **Unsafe YES Decisions:** $1/20$ ($5.0\%$)
- **Exact Lexical Bindings:** $1/20$ ($5.0\%$)

The $5\%$ unsafe decision rate proves why hardware authority isolation is non-negotiable.

---

## 3. Qualified P0 FPGA Fabric Audit

The MAPEOGEO P0 hardware implementation is located in `fabric_p0/rtl/`.

### 3.1 Primary Fabric Modules
- `fabric_p0/rtl/common/geo_defs.svh`: Central definitions (opcodes, structs, descriptors, telemetry)
- `fabric_p0/rtl/top/mapeogeo_p0_fabric.sv`: Top-level computational fabric
- `fabric_p0/rtl/work_fabric/geo_work_fabric.sv`: Multi-lane work cell scheduling and execution
- `fabric_p0/rtl/work_fabric/geo_work_cell.sv`: 12-state UoW lifecycle state machine
- `fabric_p0/rtl/authority/geo_authority_engine.sv`: Section 9 hardware authority verification engine
- `fabric_p0/rtl/evidence/geo_evidence_engine.sv`: Merkle/linear causal evidence accumulator
- `fabric_p0/rtl/memory/geo_state_memory.sv`: 256-word multivector memory with atomic 16-bit monotonic versions
- `fabric_p0/rtl/graph/geo_graph_memory.sv`: Hardware CSR graph memory with semantic query engine
- `fabric_p0/rtl/operators/geo_operator_unit.sv`: Fixed-point Q16.16 arithmetic, $\text{Cl}(2,0)$ multivector engine, matrix bridge $M_2(\mathbb{R})$, unary and bilinear ops

### 3.2 Authoritative Hardware UoW Descriptor (`uow_desc_t`)
The hardware candidate UoW descriptor is defined in `geo_defs.svh` with an exact packed width of **471 bits**:

| Field Name | Type / Width | Description |
| :--- | :--- | :--- |
| `uow_id` | `logic [31:0]` | Unique Unit-of-Work identifier |
| `opcode` | `geo_opcode_t` (6-bit) | Registered operator code (0–33) |
| `dest_addr` | `logic [7:0]` | Destination state address (0–255) |
| `src_a_addr` | `logic [7:0]` | Operand A state address |
| `src_b_addr` | `logic [7:0]` | Operand B state address |
| `dep_mask` | `logic [127:0]` | Concurrency dependency bitmask |
| `pre_state_hash` | `logic [31:0]` | Expected pre-state hash |
| `auth_token` | `logic [31:0]` | Required capability token |
| `imm_operand` | `cl20_mv_t` (128-bit) | 4 $\times$ 32-bit signed Q16.16: `s`, `e1`, `e2`, `e12` |
| `use_immediate` | `logic [0:0]` | 1 = use immediate for operand B |
| `dep_cond` | `dep_cond_type_t` (3-bit) | Dependency condition type (0–4) |
| `graph_query` | `graph_query_t` (34-bit) | Graph query: node(16), rel(8), type(8), radius(2) |
| `has_graph_mut` | `logic [0:0]` | Flag indicating graph mutation |
| `graph_mut_cmd` | `graph_mut_cmd_t` (2-bit) | NOP=0, ADD_EDGE=1, ADD_NODE=2, UPDATE_NODE=3 |
| `graph_mut_node` | `logic [15:0]` | Source graph node |
| `graph_mut_target` | `logic [15:0]` | Target graph node |
| `graph_mut_rel` | `logic [7:0]` | Relation identifier |
| `graph_mut_flags` | `logic [7:0]` | Graph edge/node flags |

### 3.3 Authoritative Hardware Outcome Types
Defined in `geo_defs.svh`:
- `OUTCOME_COMMIT` (`2'd0`): Certified, executed, committed to state memory and evidence log.
- `OUTCOME_REJECT` (`2'd1`): Syntactically valid but logically rejected (e.g. condition failed).
- `OUTCOME_REFUSE` (`2'd2`): Authoritatively refused (failed authority checks: stale version, invalid token, out of bounds).
- `OUTCOME_FAULT`  (`2'd3`): Arithmetic overflow or hardware exception.

### 3.4 Hardware Authority Checks
Implemented combinatorially in `geo_authority_engine.sv`:
1. `uow_id != 0`
2. `pre_state_hash == 0 || pre_state_hash == actual_pre_state_hash`
3. `deps_all_satisfied`
4. `(req_auth_token != 0) && ((req_auth_token & authorized_capability_mask) == req_auth_token)`
5. `!candidate_overflow`
6. `read_dest_version == current_dest_version` (Atomic CAS staleness protection)
7. `chk_invariants_pass`
8. `dest_addr < STATE_WORDS && (!has_graph_mut || (node < GRAPH_NODES && target < GRAPH_NODES))`

---

## 4. Integration Analysis & Interface Selection

### 4.1 Fabric Ingress/Egress Ports
In `mapeogeo_p0_fabric.sv`:
```systemverilog
// External Work Ingress (Multi-Lane)
input  logic [INGRESS_LANES-1:0]           ingress_valid,
output logic [INGRESS_LANES-1:0]           ingress_ready,
input  logic [INGRESS_LANES*471-1:0]       ingress_desc,

// External Result Egress (Multi-Lane)
output logic [EGRESS_LANES-1:0]            egress_valid,
input  logic [EGRESS_LANES-1:0]            egress_ready,
output logic [EGRESS_LANES*32-1:0]         egress_uow_id,
output logic [EGRESS_LANES*2-1:0]          egress_status,
output logic [EGRESS_LANES*128-1:0]        egress_result,
output logic [EGRESS_LANES*64-1:0]         egress_evidence_root,
```

### 4.2 Non-Invasive PDI Wrapper Strategy
The PDI layer implements an autonomous streaming wrapper around `mapeogeo_p0_fabric`:
1. **Logical Streaming Host Interface (32-bit):**
   - Host $\to$ FPGA: `pdi_rx_valid`, `pdi_rx_ready`, `pdi_rx_data[31:0]`, `pdi_rx_last`
   - FPGA $\to$ Host: `pdi_tx_valid`, `pdi_tx_ready`, `pdi_tx_data[31:0]`, `pdi_tx_last`
2. **Ingress Serialization/Validation:**
   - Assembles 32-bit binary words into candidate packets.
   - Verifies packet framing, magic word (`0x50444930` = `"PDI0"`), version, CRC32, and length bounds.
   - Validates opcode against registered table (`0..33`).
   - Reconstructs `uow_desc_t` (471 bits) and pulses `ingress_valid`.
3. **Egress Formatting:**
   - Intercepts fabric `egress_valid` and builds a structured binary disposition packet.
   - In case of pre-fabric rejection (e.g., malformed packet or unknown operator), directly emits a REFUSE/REJECT disposition with telemetry and error code.
4. **Execution Semantics:** Zero modifications to existing operator ALUs, state memory, or authority logic.

---

## 5. Potential Semantic Discrepancies & Protocol Alignments

| Proposal Specification (Section 3) | Actual RTL Implementation (`fabric_p0`) | Reconciliation Mechanism |
| :--- | :--- | :--- |
| `object_refs: [441, 442]` | State memory has `STATE_WORDS = 256` (8-bit address `0..255`). Graph memory has 16-bit node IDs (`0..65535`). | The PDI schema validator distinguishes between `state_ref` (bounded to 255) and `graph_node_ref` (bounded to 65535). Out-of-bounds references are rejected deterministically before packet dispatch. |
| `operator_id: 12` | RTL opcodes are 6-bit enum `geo_opcode_t` (values `0..33`). | An authoritative operator registry (`pdi_v0_operators.json`) is generated directly from `geo_defs.svh`. Any unmapped ID is rejected. |
| `parameters: [{"type": "u32", "value": 100}]` | Operands in RTL are Q16.16 signed fixed-point multivectors (`cl20_mv_t`: 4 components) or 8-bit memory addresses. | The host codec encodes parameter types (`u32`, `i32_q16_16`, `mv_cl20`, `addr8`) and populates `imm_operand` and `use_immediate`. |
| `assumed_state_version: 9938` | RTL tracks 16-bit monotonic version per memory word and checks `read_dest_version == current_dest_version`. | `assumed_state_version` is passed as pre-state version check; if mismatched, RTL issues `OUTCOME_REFUSE` (failed check 6). |
| Model confidence | Model confidence does not confer authorization. | Omitted from hardware packet entirely. |
| Authority token | Hardware check 4 requires `(auth_token & capability_mask) == auth_token`. | Host adapter assigns authorized capability token based on authenticated session grants; LLM is never allowed to fabricate or bypass authority tokens. |

---

## 6. Implementation Readiness & Isolation Boundary

1. **Branching:** Work is completely isolated on branch `experiment/pdi-135m-v0.1`.
2. **Untracked RTL Integrity:** No files in `fabric_p0/` are modified. All PDI artifacts live in `pdi/`.
3. **Simulation Restraint:** No simulation or RTL test runs will be initiated until explicit user signal.
4. **Dependencies Verified:** PyTorch 2.11.dev + CUDA 12.8 + PEFT 0.18.1 + Transformers 5.16.1 + Pytest are fully operational in the local Python environment.

Phase 0 Audit is **COMPLETE**.
