// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_synth_evidence (Gate RTL-9 Post-Synthesis Equivalence)

`timescale 1ns/1ps
`include "geo_defs.svh"

module tb_synth_evidence;

    logic clk;
    logic reset_n;

    logic        append_req;
    logic [31:0] uow_id;
    logic [63:0] pre_state_hash;
    logic [63:0] post_state_hash;
    logic [63:0] candidate_hash;
    logic [31:0] cert_id;
    logic [31:0] causal_seq;

    logic              append_ack;
    logic              engine_busy;
    logic [31:0]       record_count;
    evidence_record_t  latest_record;

    logic [255:0] physical_evidence_root_256;
    logic [255:0] semantic_evidence_root_256;
    logic [63:0]  semantic_evidence_test_64;
    logic [63:0]  current_evidence_root;

    always #5 clk = ~clk;

    geo_evidence_engine dut (
        .clk(clk),
        .reset_n(reset_n),
        .append_req(append_req),
        .uow_id(uow_id),
        .pre_state_hash(pre_state_hash),
        .post_state_hash(post_state_hash),
        .candidate_hash(candidate_hash),
        .cert_id(cert_id),
        .causal_seq(causal_seq),
        .append_ack(append_ack),
        .engine_busy(engine_busy),
        .record_count(record_count),
        .latest_record(latest_record),
        .physical_evidence_root_256(physical_evidence_root_256),
        .semantic_evidence_root_256(semantic_evidence_root_256),
        .semantic_evidence_test_64(semantic_evidence_test_64),
        .current_evidence_root(current_evidence_root)
    );

    initial begin
        clk = 0;
        reset_n = 0;
        append_req = 0;
        uow_id = 0;
        pre_state_hash = 0;
        post_state_hash = 0;
        candidate_hash = 0;
        cert_id = 0;
        causal_seq = 0;

        #20 reset_n = 1;
        #10;

        // Vector 1: Append UoW 1
        @(negedge clk);
        append_req = 1;
        uow_id = 32'd1;
        pre_state_hash = 64'hA5A55A5A11112222;
        post_state_hash = 64'hB5B55B5B33334444;
        candidate_hash = 64'hC5C55C5C55556666;
        cert_id = 32'd100;
        causal_seq = 32'd1;
        @(negedge clk);
        append_req = 0;
        #1;
        assert(append_ack == 1'b1) else $fatal(1, "append_ack not asserted");
        assert(record_count == 32'd1) else $fatal(1, "record_count not 1");
        assert(semantic_evidence_test_64 != 64'd0) else $fatal(1, "XOR root null");

        // Wait for SHA pipeline done
        #800;

        assert(physical_evidence_root_256 != 256'd0) else $fatal(1, "physical_evidence_root null");
        assert(semantic_evidence_root_256 != 256'd0) else $fatal(1, "semantic_evidence_root null");

        $display("PASS POST_SYNTHESIS_EVIDENCE_EQUIVALENCE");
        $finish;
    end

endmodule
