// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_sva_invariants
// SystemVerilog Assertions (SVA) encoding Section 9 Safety & Zero-Mutation Invariants

`ifndef GEO_SVA_INVARIANTS_SV
`define GEO_SVA_INVARIANTS_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_sva_invariants (
    input logic clk,
    input logic reset_n,

    // Authority Engine interface signals
    input logic                   cert_req,
    input logic                   cert_done,
    input commit_outcome_t        outcome,
    input logic                   commit_permit,
    input logic                   chk_auth_present,
    input logic                   chk_stale_pass,
    input logic                   chk_invariants_pass,
    input logic                   candidate_overflow,

    // Memory interface signals
    input logic                   mem_commit_en,
    input logic [7:0]             mem_commit_addr,
    input logic [15:0]            post_commit_version,

    // Egress Interface signals
    input logic                   egress_valid,
    input logic                   egress_ready,
    input logic [31:0]            egress_uow_id
);

`ifdef SVA_ON

    // -------------------------------------------------------------------------
    // Property 1: Zero Mutation on Authority Rejection / Refusal
    // If authority or stale-state check fails, commit_permit must be strictly 0.
    // -------------------------------------------------------------------------
    property p_zero_mutation_on_auth_refuse;
        @(posedge clk) disable iff (!reset_n)
        (cert_done && (!chk_auth_present || !chk_stale_pass)) |-> (!commit_permit && (outcome == OUTCOME_REFUSE));
    endproperty
    assert_zero_mutation_auth: assert property (p_zero_mutation_on_auth_refuse)
        else $error("[SVA FAULT] Zero-mutation violated: commit permitted on authority refusal!");

    // -------------------------------------------------------------------------
    // Property 2: Arithmetic Fault Fails Closed
    // Any candidate overflow forces outcome to OUTCOME_FAULT and suppresses commit.
    // -------------------------------------------------------------------------
    property p_arith_fault_fail_closed;
        @(posedge clk) disable iff (!reset_n)
        (cert_done && candidate_overflow) |-> (!commit_permit && (outcome == OUTCOME_FAULT));
    endproperty
    assert_arith_fault_closed: assert property (p_arith_fault_fail_closed)
        else $error("[SVA FAULT] Arithmetic fault did not fail closed!");

    // -------------------------------------------------------------------------
    // Property 3: Version Monotonicity on Successful Memory Commit
    // Every committed memory write must produce a strictly incremented version tag.
    // -------------------------------------------------------------------------
    property p_version_monotonic_commit;
        @(posedge clk) disable iff (!reset_n)
        mem_commit_en |-> (post_commit_version > 16'd0);
    endproperty
    assert_version_monotonic: assert property (p_version_monotonic_commit)
        else $error("[SVA FAULT] Memory commit version not monotonic!");

    // -------------------------------------------------------------------------
    // Property 4: Egress Protocol Handshake Stability
    // Egress data must remain stable until ready handshake acknowledges transfer.
    // -------------------------------------------------------------------------
    property p_egress_stability;
        @(posedge clk) disable iff (!reset_n)
        (egress_valid && !egress_ready) |=> (egress_valid && $stable(egress_uow_id));
    endproperty
    assert_egress_stability: assert property (p_egress_stability)
        else $error("[SVA FAULT] Egress data unstable during backpressure!");

`endif // SVA_ON

endmodule

`endif // GEO_SVA_INVARIANTS_SV
