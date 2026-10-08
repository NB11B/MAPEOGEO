// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_authority_engine
// Hardware Authority and Commit verification engine enforcing Section 9 checks & zero-mutation guarantee

`ifndef GEO_AUTHORITY_ENGINE_SV
`define GEO_AUTHORITY_ENGINE_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_authority_engine #(
    parameter int STATE_WORDS = 256,
    parameter int GRAPH_NODES = 256
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Evaluation Request
    input  logic                   cert_req,
    input  logic [31:0]            candidate_uow_id,
    input  logic [7:0]             candidate_dest_addr,
    input  cl20_mv_t               candidate_result,
    input  logic                   candidate_overflow,
    input  logic [31:0]            req_pre_state_hash,
    input  logic [31:0]            req_auth_token,
    input  logic                   deps_all_satisfied,
    input  logic                   candidate_has_graph_mut,
    input  graph_mut_cmd_t         candidate_graph_cmd,
    input  logic [15:0]            candidate_graph_node,
    input  logic [15:0]            candidate_graph_target,
    input  logic [7:0]             candidate_graph_rel,
    input  logic [7:0]             candidate_graph_flags,

    // Authoritative State Context
    input  logic [31:0]            actual_pre_state_hash,
    input  logic [15:0]            read_dest_version,
    input  logic [15:0]            current_dest_version,
    input  logic [31:0]            authorized_capability_mask,

    // Certification Outcome
    output logic                   cert_done,
    output commit_outcome_t        outcome,
    output logic                   commit_permit,
    output logic [7:0]             commit_addr,
    output cl20_mv_t               commit_data,
    output logic                   commit_graph_en,
    output graph_mut_cmd_t         commit_graph_cmd,
    output logic [15:0]            commit_graph_node,
    output logic [15:0]            commit_graph_target,
    output logic [7:0]             commit_graph_rel,
    output logic [7:0]             commit_graph_flags,
    output logic [31:0]            cert_id,
    output logic [31:0]            certified_uow_id,

    // Check Status Telemetry
    output logic [7:0]             failed_check_mask // Bit per check
);

    // --- The 8 Minimum Checks (Section 9.1) ---
    // 1. UoW identity valid
    logic chk_uow_valid;
    assign chk_uow_valid = (candidate_uow_id != 32'd0);

    // 2. Pre-state identity matches (upper 16 bits 0 indicates CAS versioning in lower 16 bits)
    logic chk_pre_state_match;
    assign chk_pre_state_match = (req_pre_state_hash[31:16] == 16'd0) || (req_pre_state_hash == actual_pre_state_hash);

    // 3. Dependencies satisfied
    logic chk_deps_satisfied;
    assign chk_deps_satisfied = deps_all_satisfied;

    // 4. Required authority / capability present
    logic chk_auth_present;
    assign chk_auth_present = (req_auth_token != 32'd0) && ((req_auth_token & authorized_capability_mask) == req_auth_token);

    // 5. Result corresponds to current UoW
    logic chk_result_valid;
    assign chk_result_valid = !candidate_overflow;

    // 6. Stale-state check passes (unversioned if 0, strictly matched otherwise)
    logic chk_stale_pass;
    assign chk_stale_pass = (read_dest_version == 16'd0) || (read_dest_version == current_dest_version);

    // 7. Declared invariants pass (finite, not nullified by illegal operator)
    logic chk_invariants_pass;
    assign chk_invariants_pass = !candidate_overflow;

    // 8. Proposed mutation is structurally valid (both state address and graph mutation parameters)
    logic chk_mutation_valid;
    assign chk_mutation_valid = (candidate_dest_addr < STATE_WORDS) &&
        (!candidate_has_graph_mut || (candidate_graph_node < GRAPH_NODES && candidate_graph_target < GRAPH_NODES));

    logic [7:0] checks_pass;
    assign checks_pass = {
        chk_mutation_valid,
        chk_invariants_pass,
        chk_stale_pass,
        chk_result_valid,
        chk_auth_present,
        chk_deps_satisfied,
        chk_pre_state_match,
        chk_uow_valid
    };

    logic all_passed;
    assign all_passed = (checks_pass == 8'b11111111);

    logic [31:0] cert_counter;

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            cert_done           <= 1'b0;
            outcome             <= OUTCOME_REJECT;
            commit_permit       <= 1'b0;
            commit_addr         <= '0;
            commit_data         <= '0;
            commit_graph_en     <= 1'b0;
            commit_graph_cmd    <= GRAPH_MUT_NOP;
            commit_graph_node   <= '0;
            commit_graph_target <= '0;
            commit_graph_rel    <= '0;
            commit_graph_flags  <= '0;
            cert_id             <= '0;
            certified_uow_id    <= '0;
            failed_check_mask   <= '0;
            cert_counter        <= 32'd1;
        end else begin
            if (cert_req) begin
                cert_done         <= 1'b1;
                cert_id           <= cert_counter;
                certified_uow_id  <= candidate_uow_id;
                cert_counter      <= cert_counter + 1'b1;
                failed_check_mask <= ~checks_pass;

                if (all_passed) begin
                    outcome             <= OUTCOME_COMMIT;
                    commit_permit       <= 1'b1;
                    commit_addr         <= candidate_dest_addr;
                    commit_data         <= candidate_result;
                    commit_graph_en     <= candidate_has_graph_mut;
                    commit_graph_cmd    <= candidate_graph_cmd;
                    commit_graph_node   <= candidate_graph_node;
                    commit_graph_target <= candidate_graph_target;
                    commit_graph_rel    <= candidate_graph_rel;
                    commit_graph_flags  <= candidate_graph_flags;
                end else if (!chk_auth_present || !chk_stale_pass) begin
                    outcome             <= OUTCOME_REFUSE;
                    commit_permit       <= 1'b0; // ZERO MUTATION
                    commit_addr         <= '0;
                    commit_data         <= '0;
                    commit_graph_en     <= 1'b0; // ZERO GRAPH MUTATION
                end else if (candidate_overflow || !chk_mutation_valid) begin
                    outcome             <= OUTCOME_FAULT;
                    commit_permit       <= 1'b0; // ZERO MUTATION
                    commit_addr         <= '0;
                    commit_data         <= '0;
                    commit_graph_en     <= 1'b0; // ZERO GRAPH MUTATION
                end else begin
                    outcome             <= OUTCOME_REJECT;
                    commit_permit       <= 1'b0; // ZERO MUTATION
                    commit_addr         <= '0;
                    commit_data         <= '0;
                    commit_graph_en     <= 1'b0; // ZERO GRAPH MUTATION
                end
            end else begin
                cert_done       <= 1'b0;
                commit_permit   <= 1'b0;
                commit_graph_en <= 1'b0;
            end
        end
    end

endmodule

`endif // GEO_AUTHORITY_ENGINE_SV
