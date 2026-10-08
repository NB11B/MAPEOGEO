// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_synth_authority (Gate RTL-9 Post-Synthesis Equivalence)

`timescale 1ns/1ps
`include "geo_defs.svh"

module tb_synth_authority;

    logic        clk;
    logic        reset_n;
    logic        cert_req;
    logic [31:0] candidate_uow_id;
    logic [7:0]  candidate_dest_addr;
    cl20_mv_t    candidate_result;
    logic        candidate_overflow;
    logic [31:0] req_pre_state_hash;
    logic [31:0] req_auth_token;
    logic        deps_all_satisfied;
    logic        candidate_has_graph_mut;
    graph_mut_cmd_t candidate_graph_cmd;
    logic [15:0] candidate_graph_node;
    logic [15:0] candidate_graph_target;
    logic [7:0]  candidate_graph_rel;
    logic [7:0]  candidate_graph_flags;

    logic [31:0] actual_pre_state_hash;
    logic [15:0] read_dest_version;
    logic [15:0] current_dest_version;
    logic [31:0] authorized_capability_mask;

    logic            cert_done;
    commit_outcome_t outcome;
    logic            commit_permit;
    logic [7:0]      commit_addr;
    cl20_mv_t        commit_data;
    logic            commit_graph_en;
    graph_mut_cmd_t  commit_graph_cmd;
    logic [15:0]     commit_graph_node;
    logic [15:0]     commit_graph_target;
    logic [7:0]      commit_graph_rel;
    logic [7:0]      commit_graph_flags;
    logic [31:0]     cert_id;
    logic [31:0]     certified_uow_id;
    logic [7:0]      failed_checks;

    always #5 clk = ~clk;

    geo_authority_engine dut (
        .clk(clk),
        .reset_n(reset_n),
        .cert_req(cert_req),
        .candidate_uow_id(candidate_uow_id),
        .candidate_dest_addr(candidate_dest_addr),
        .candidate_result(candidate_result),
        .candidate_overflow(candidate_overflow),
        .req_pre_state_hash(req_pre_state_hash),
        .req_auth_token(req_auth_token),
        .deps_all_satisfied(deps_all_satisfied),
        .candidate_has_graph_mut(candidate_has_graph_mut),
        .candidate_graph_cmd(candidate_graph_cmd),
        .candidate_graph_node(candidate_graph_node),
        .candidate_graph_target(candidate_graph_target),
        .candidate_graph_rel(candidate_graph_rel),
        .candidate_graph_flags(candidate_graph_flags),
        .actual_pre_state_hash(actual_pre_state_hash),
        .read_dest_version(read_dest_version),
        .current_dest_version(current_dest_version),
        .authorized_capability_mask(authorized_capability_mask),
        .cert_done(cert_done),
        .outcome(outcome),
        .commit_permit(commit_permit),
        .commit_addr(commit_addr),
        .commit_data(commit_data),
        .commit_graph_en(commit_graph_en),
        .commit_graph_cmd(commit_graph_cmd),
        .commit_graph_node(commit_graph_node),
        .commit_graph_target(commit_graph_target),
        .commit_graph_rel(commit_graph_rel),
        .commit_graph_flags(commit_graph_flags),
        .cert_id(cert_id),
        .certified_uow_id(certified_uow_id),
        .failed_check_mask(failed_checks)
    );

    initial begin
        clk = 0;
        reset_n = 0;
        cert_req = 0;
        candidate_uow_id = 0;
        candidate_dest_addr = 0;
        candidate_result = '0;
        candidate_overflow = 0;
        req_pre_state_hash = 0;
        req_auth_token = 0;
        deps_all_satisfied = 0;
        candidate_has_graph_mut = 0;
        candidate_graph_cmd = GRAPH_MUT_NOP;
        candidate_graph_node = 0;
        candidate_graph_target = 0;
        candidate_graph_rel = 0;
        candidate_graph_flags = 0;
        actual_pre_state_hash = 0;
        read_dest_version = 0;
        current_dest_version = 0;
        authorized_capability_mask = 32'hFFFFFFFF;

        #20 reset_n = 1;
        #10;

        // Vector 1: Valid Normal Commit
        @(posedge clk);
        cert_req = 1;
        candidate_uow_id = 32'h00010001;
        candidate_dest_addr = 8'd42;
        candidate_result.s = 32'h00010000;
        candidate_result.e1 = 32'h00020000;
        candidate_result.e2 = 32'h00030000;
        candidate_result.e12 = 32'h00040000;
        candidate_overflow = 0;
        req_pre_state_hash = 32'h00000005; // version 5
        read_dest_version = 16'd5;
        current_dest_version = 16'd5;
        deps_all_satisfied = 1;
        req_auth_token = 32'hA5A55A5A;
        @(posedge clk);
        #1;
        assert(cert_done == 1'b1) else $fatal(1, "V1: cert_done not asserted");
        assert(outcome == OUTCOME_COMMIT) else $fatal(1, "V1: Expected COMMIT, got %0d", outcome);
        assert(commit_permit == 1'b1) else $fatal(1, "V1: Expected commit_permit 1");
        assert(commit_addr == 8'd42) else $fatal(1, "V1: Address mismatch");
        assert(commit_data.s == 32'h00010000) else $fatal(1, "V1: Data mismatch");
        cert_req = 0;

        // Vector 2: Stale CAS Version (Dest version mismatch) -> REFUSE
        @(posedge clk);
        cert_req = 1;
        candidate_uow_id = 32'h00010002;
        read_dest_version = 16'd5;
        current_dest_version = 16'd6; // Stale!
        @(posedge clk);
        #1;
        assert(cert_done == 1'b1) else $fatal(1, "V2: cert_done not asserted");
        assert(outcome == OUTCOME_REFUSE) else $fatal(1, "V2: Expected REFUSE on stale version");
        assert(commit_permit == 1'b0) else $fatal(1, "V2: Permitted stale commit!");
        cert_req = 0;

        // Vector 3: Arithmetic Overflow -> FAULT
        @(posedge clk);
        cert_req = 1;
        candidate_uow_id = 32'h00010003;
        current_dest_version = 16'd5;
        candidate_overflow = 1; // Overflow!
        @(posedge clk);
        #1;
        assert(cert_done == 1'b1) else $fatal(1, "V3: cert_done not asserted");
        assert(outcome == OUTCOME_FAULT) else $fatal(1, "V3: Expected FAULT on overflow");
        assert(commit_permit == 1'b0) else $fatal(1, "V3: Permitted overflow commit!");
        cert_req = 0;

        // Vector 4: Unauthorized Capability Token -> REFUSE
        @(posedge clk);
        cert_req = 1;
        candidate_uow_id = 32'h00010004;
        candidate_overflow = 0;
        req_auth_token = 32'h0; // Invalid token!
        @(posedge clk);
        #1;
        assert(cert_done == 1'b1) else $fatal(1, "V4: cert_done not asserted");
        assert(outcome == OUTCOME_REFUSE) else $fatal(1, "V4: Expected REFUSE on invalid token");
        assert(commit_permit == 1'b0) else $fatal(1, "V4: Permitted unauthorized commit!");
        cert_req = 0;

        // Vector 5: Unsatisfied Dependency -> REJECT
        @(posedge clk);
        cert_req = 1;
        candidate_uow_id = 32'h00010005;
        req_auth_token = 32'hA5A55A5A;
        read_dest_version = 16'd5;
        current_dest_version = 16'd5;
        deps_all_satisfied = 0; // Unsatisfied!
        @(posedge clk);
        #1;
        assert(cert_done == 1'b1) else $fatal(1, "V5: cert_done not asserted");
        assert(outcome == OUTCOME_REJECT) else $fatal(1, "V5: Expected REJECT on unsatisfied deps");
        assert(commit_permit == 1'b0) else $fatal(1, "V5: Permitted unsatisfied deps commit!");
        cert_req = 0;

        $display("PASS POST_SYNTHESIS_AUTHORITY_EQUIVALENCE");
        $finish;
    end

endmodule
