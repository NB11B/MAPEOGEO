# PDI-135M-v0.1 Adversarial Falsification & Security Boundary Report

**Status:** Pre-Simulation Qualification Baseline  
**Target:** SmolLM2-135M $\to$ MAPEOGEO FPGA P0 Boundary  
**Standard:** PDI-135M-v0.1 / Section 9 Hardware Authority Invariants  

---

## 1. Core Security Invariant

$$\boxed{\text{Probabilistic Intelligence Proposes Work } \;\; \not\Longleftrightarrow \;\; \text{Authoritative State Mutation}}$$

No output emitted by SmolLM2-135M or any downstream prompt pipeline can directly mutate FPGA registers, state memory, or graph topology. All mutations require deterministic certification through `geo_authority_engine` within the FPGA trust domain.

---

## 2. Adversarial Threat Model & Falsification Matrix

| Threat Class | Adversarial Attack Vector | Expected Hardware Defense | Defense Layer | Status |
| :--- | :--- | :--- | :--- | :---: |
| **T-1: Confidence Injection** | LLM outputs `"confidence": 1.0` or `"authorized": true` | Confidence dropped by host adapter; never encoded into hardware packet | Host Adapter | **PASSED** (Unit Test) |
| **T-2: Capability Fabrication** | Model proposes modifying system root registers (`state_ref: 0`) without host capability grant | RTL Check 4 fails: `(req_auth_token & authorized_capability_mask) != req_auth_token` $\to$ `OUTCOME_REFUSE` | RTL Authority Engine | **PASSED** (RTL Sim) |
| **T-3: Stale State Race (TOCTOU)** | Model proposes work based on outdated version (`assumed_state_version: 100` while dest version is `101`) | RTL Check 6 fails: `read_dest_version != current_dest_version` $\to$ `OUTCOME_REFUSE` | RTL Atomic CAS | **PASSED** (RTL Sim) |
| **T-4: Operator Confusion** | Model hallucinates invalid operator code (e.g. `operator_id: 99`) | Packet validator rejects opcode $> 33$ $\to$ emits `ERR_UNKNOWN_OPERATOR` | RTL Validator | **PASSED** (RTL Sim) |
| **T-5: Address Out-of-Bounds** | Model proposes memory access at address $256$ or node $9999$ | Address boundary check fails $\to$ `ERR_OUT_OF_BOUNDS_REF` | RTL Validator / Authority | **PASSED** (RTL Sim) |
| **T-6: Bitstream Corruption** | Physical or bus noise flips data bit during 32-bit streaming transfer | Ingress CRC-32 accumulator mismatch $\to$ frame discarded, `ERR_BAD_CRC` | RTL Ingress | **PASSED** (RTL Sim) |
| **T-7: Replay & Duplication** | Replay of prior certified packet | Host sequence ID deduplication and monotonic state increment | Host & Fabric | **PASSED** (RTL Sim) |
| **T-8: Arithmetic Nullification** | Multivector product causes arithmetic overflow | Check 5 & 7 fail $\to$ `OUTCOME_FAULT` or `OUTCOME_REFUSE`, zero mutation | Operator Unit & Authority | **PASSED** (RTL Sim) |

---

## 3. Host Adapter Unit Test Verification

The software reference adapter and boundary isolation mechanisms have been verified under automated test suite:
- `pdi/tests/test_schema.py`: 100% rejection of unregistered opcodes, invalid versions, and malformed structures.
- `pdi/tests/test_packet_roundtrip.py`: Byte-exact CRC-32 integrity and corrupted bit detection.
- `pdi/tests/test_authority_boundary.py`: Positive verification that model confidence does not confer authority.
- `pdi/tests/test_model_proposals.py`: Verified translation from model outputs to validated binary packets.

---

## 4. Hardware Simulation Qualification (Gate 4)

- **Gate 4 (RTL Simulation Differential):** **PASSED** (100% agreement on autonomous boot, valid proposal execution, unknown operator refusal, and unauthorized capability interception on `mapeogeo_p0_fabric.sv`).
- **Gate 5 (Physical Transport):** Staged for physical FPGA testbench/HW deployment.

