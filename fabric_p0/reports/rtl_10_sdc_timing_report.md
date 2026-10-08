# MAPEOGEO P0 Gate RTL-10 SDC Timing-Constraint Sign-Off Report

**Document ID:** `RTL10-QUAL-2026-10-08`  
**Status:** **QUALIFIED / SIGNED-OFF**  
**Target Codebase:** `fabric_p0/` (Integrated Production Hardware Codebase)  
**Regression Status:** **121 / 121 PASSED (100% Green)**  

---

## 1. Executive Summary

Gate **RTL-10** establishes complete physical timing constraint coverage and sign-off for the MAPEOGEO P0 6-domain asynchronous hardware substrate.

The core exit criterion of Gate RTL-10 is:

$$\boxed{\textbf{Every physical timing path is either constrained or explicitly justified; 0 unconstrained paths.}}$$

The SDC constraint package ([`mapeogeo_p0_clocks.sdc`](file:///C:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/constraints/mapeogeo_p0_clocks.sdc)) and machine-readable synchronizer registry ([`cdc_synchronizer_registry.json`](file:///C:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/constraints/cdc_synchronizer_registry.json)) rigorously define:
1. All 6 physical clock domains with setup/hold uncertainty margins.
2. Pairwise asynchronous clock domain grouping.
3. CDC FIFO Gray-pointer max delay (`-datapath_only`) and bus-skew bounds.
4. Asynchronous reset assertion false paths strictly bound to 2FF stage1 capture flops.
5. Primary input and output delay envelopes for all top-level IO ports.
6. Zero wildcard / unbudgeted false paths catching internal compute, memory, or authority logic.

All **121 tests** across Gates RTL-1 through RTL-10 pass with zero errors.

---

## 2. Physical Clock Specifications & Uncertainty Budgets

### Table 1: Primary Clock Specifications

| Clock Port | Target Frequency | Clock Period | Target Domain | Setup Uncertainty | Hold Uncertainty |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `clk_ingress` | $125.00\text{ MHz}$ | $8.000\text{ ns}$ | Ingress Buffers / Dispatch | $0.150\text{ ns}$ | $0.050\text{ ns}$ |
| `clk_auth` | $100.00\text{ MHz}$ | $10.000\text{ ns}$ | Hardware Authority Engines | $0.150\text{ ns}$ | $0.050\text{ ns}$ |
| `clk_op` | $166.67\text{ MHz}$ | $6.000\text{ ns}$ | Spatial Work Cells & $Cl(2,0)$ ALU | $0.150\text{ ns}$ | $0.050\text{ ns}$ |
| `clk_mem` | $200.00\text{ MHz}$ | $5.000\text{ ns}$ | 4-Bank State Memory Subsystem | $0.150\text{ ns}$ | $0.050\text{ ns}$ |
| `clk_ev` | $133.33\text{ MHz}$ | $7.500\text{ ns}$ | FIPS 180-4 Evidence Subsystem | $0.150\text{ ns}$ | $0.050\text{ ns}$ |
| `clk_egress` | $156.25\text{ MHz}$ | $6.400\text{ ns}$ | Result Aggregation / Egress | $0.150\text{ ns}$ | $0.050\text{ ns}$ |

---

## 3. Clock Domain Interaction & CDC Timing Matrix

### Table 2: $6 \times 6$ Clock Domain Interaction Matrix

| Source \ Dest | `clk_ingress` | `clk_auth` | `clk_op` | `clk_mem` | `clk_ev` | `clk_egress` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`clk_ingress`** | **TIMED** ($8.0\text{ns}$) | ASYNC_GROUP | **MAX_DELAY** ($6.0\text{ns}$) | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP |
| **`clk_auth`** | ASYNC_GROUP | **TIMED** ($10.0\text{ns}$) | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP |
| **`clk_op`** | **MAX_DELAY** ($8.0\text{ns}$) | ASYNC_GROUP | **TIMED** ($6.0\text{ns}$) | ASYNC_GROUP | ASYNC_GROUP | **MAX_DELAY** ($6.4\text{ns}$) |
| **`clk_mem`** | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP | **TIMED** ($5.0\text{ns}$) | ASYNC_GROUP | ASYNC_GROUP |
| **`clk_ev`** | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP | ASYNC_GROUP | **TIMED** ($7.5\text{ns}$) | ASYNC_GROUP |
| **`clk_egress`** | ASYNC_GROUP | ASYNC_GROUP | **MAX_DELAY** ($6.0\text{ns}$) | ASYNC_GROUP | ASYNC_GROUP | **TIMED** ($6.4\text{ns}$) |

- **Intra-Domain Synchronous Paths:** Fully timed at target domain clock frequencies.
- **Asynchronous CDC Crossings:** Ingress-to-Work and Work-to-Egress are protected by `geo_async_fifo` Gray-pointer synchronizers with `-datapath_only` max-delay constraints.
- **Isolated Asynchronous Domains:** Authority, Memory, and Evidence operate in independent clock groups without unprotected combinational cross-talk.

---

## 4. Machine-Readable CDC Synchronizer Registry

All 10 hardware synchronizers are cataloged in [`cdc_synchronizer_registry.json`](file:///C:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/constraints/cdc_synchronizer_registry.json):

### Table 3: Hardware Synchronizer Catalog

| Sync ID | Instance Pattern | Source Domain | Dest Domain | Signal Type | Timing Constraint / Exception |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SYNC-RDC-01` | `u_sync_rst_ing` | `rst_ingress_async_n` | `clk_ingress` | Reset Assertion | `set_false_path -to *u_sync_rst_ing*rst_stage1*` |
| `SYNC-RDC-02` | `u_sync_rst_auth`| `rst_auth_async_n` | `clk_auth` | Reset Assertion | `set_false_path -to *u_sync_rst_auth*rst_stage1*` |
| `SYNC-RDC-03` | `u_sync_rst_op` | `rst_op_async_n` | `clk_op` | Reset Assertion | `set_false_path -to *u_sync_rst_op*rst_stage1*` |
| `SYNC-RDC-04` | `u_sync_rst_mem` | `rst_mem_async_n` | `clk_mem` | Reset Assertion | `set_false_path -to *u_sync_rst_mem*rst_stage1*` |
| `SYNC-RDC-05` | `u_sync_rst_ev` | `rst_ev_async_n` | `clk_ev` | Reset Assertion | `set_false_path -to *u_sync_rst_ev*rst_stage1*` |
| `SYNC-RDC-06` | `u_sync_rst_eg` | `rst_egress_async_n` | `clk_egress` | Reset Assertion | `set_false_path -to *u_sync_rst_eg*rst_stage1*` |
| `SYNC-CDC-ING-W2R` | `gen_ingress_cdc[*].u_ing_cdc_fifo.u_sync_w2r` | `clk_ingress` | `clk_op` | Gray Write Ptr | `set_max_delay 6.000 -datapath_only; bus_skew 1.5ns` |
| `SYNC-CDC-ING-R2W` | `gen_ingress_cdc[*].u_ing_cdc_fifo.u_sync_r2w` | `clk_op` | `clk_ingress` | Gray Read Ptr | `set_max_delay 8.000 -datapath_only; bus_skew 1.5ns` |
| `SYNC-CDC-EG-W2R` | `gen_egress_cdc[*].u_eg_cdc_fifo.u_sync_w2r` | `clk_op` | `clk_egress` | Gray Write Ptr | `set_max_delay 6.400 -datapath_only; bus_skew 1.5ns` |
| `SYNC-CDC-EG-R2W` | `gen_egress_cdc[*].u_eg_cdc_fifo.u_sync_r2w` | `clk_egress` | `clk_op` | Gray Read Ptr | `set_max_delay 6.000 -datapath_only; bus_skew 1.5ns` |

---

## 5. Constraint Lint & Timing Path Audit Results

The automated SDC auditor ([`fabric_p0/scripts/audit_sdc_constraints.py`](file:///C:/Users/nateb/OneDrive/Documents/MAPEOGEO/fabric_p0/scripts/audit_sdc_constraints.py)) performed static structural checks against `mapeogeo_p0_cdc_fabric.sv` and `synth_mapeogeo_p0_cdc_fabric.v`:

1. **Clock Port Binding:** 6 of 6 declared RTL clock ports bound to valid SDC clocks (0 unbound).
2. **Clock Group Membership:** 6 of 6 clocks assigned to `set_clock_groups -asynchronous`.
3. **Primary IO Coverage:** 100% of top-level input/output ports have setup/hold delay bounds ($2.0\text{ns}$ max, $0.5\text{ns}$ min).
4. **False-Path Whitelist:** 0 false-path exceptions match internal datapath, ALU, memory bank, or authority cells.
5. **Gray Bus Skew:** Bus skew constraint ($1.5\text{ns}$) bounds multi-bit pointer dispersion below half-period limits.
6. **Unconstrained Timing Paths:** **0 unconstrained paths**.

---

## 6. Master Hardening Regression Summary

```text
==================================================================================================
MAPEOGEO P0 MASTER HARDENING REGRESSION: 121 / 121 PASSED (100% GREEN)
==================================================================================================
  - test_p0_fabric.py                     : 17 / 17 PASSED
  - test_p0_capacity.py                   : 61 / 61 PASSED
  - test_p08_timing_fault.py              : 17 / 17 PASSED
  - test_p0_rtl7i_integration.py          :  4 /  4 PASSED
  - test_p0_rtl8_evidence.py              :  4 /  4 PASSED
  - test_p0_rtl9_equivalence.py           : 10 / 10 PASSED
  - test_p0_rtl10_sdc_audit.py            :  8 /  8 PASSED
==================================================================================================
TOTAL: 121 PASSED, 0 FAILED, 0 SKIPPED (100% Green)
==================================================================================================
```

---

## 7. Sign-Off & Next Milestone

Gate **RTL-10** is formally **SIGNED OFF**.

The design is now ready for **Gate RTL-11 (Vendor FPGA Technology Mapping & Physical Realization)** across candidate FPGA families (Xilinx UltraScale+, Intel Agilex), collecting:
- Physical resource utilization: $\text{LUT}, \text{FF}, \text{DSP}, \text{BRAM}, \text{URAM}$
- Timing metrics: $F_{\max}, \text{WNS}, \text{TNS}, \text{routing congestion}$
- Effective physical throughput: $R_{\rm physical} = R_{\rm UoW/cycle} \cdot F_{\max}$
- Hardware scaling sweeps across $(2,2,4,2,2)$, $(4,4,8,4,4)$, and $(8,8,16,8,8)$ fabric geometries.
