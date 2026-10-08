// SPDX-License-Identifier: MIT
// PDI-135M-v0.3: RTL Differential Equivalence Testbench for K=8 Work Proposals
// Module: tb_pdi_k8_selected_work
// Exercises the R01-R15 test matrix across MAPEOGEO P0 fabric with pdi_uow_bridge.

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_pdi_k8_selected_work;

    parameter int WORK_CELL_COUNT = 4;
    parameter int STATE_WORDS     = 256;

    logic        clk;
    logic        reset_n;
    logic        boot_trigger;
    logic        boot_complete;
    logic        fabric_halted;

    logic        pdi_rx_valid;
    logic        pdi_rx_ready;
    logic [31:0] pdi_rx_data;
    logic        pdi_rx_last;

    logic        pdi_tx_valid;
    logic        pdi_tx_ready;
    logic [31:0] pdi_tx_data;
    logic        pdi_tx_last;

    logic [31:0] authorized_capability_mask;

    pdi_uow_bridge #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .OPERATOR_LANES(1),
        .MEMORY_BANKS(1),
        .AUTHORITY_ENGINES(1),
        .STATE_WORDS(STATE_WORDS),
        .GRAPH_NODES(256)
    ) dut (
        .clk(clk),
        .reset_n(reset_n),
        .boot_trigger(boot_trigger),
        .boot_complete(boot_complete),
        .fabric_halted(fabric_halted),
        .pdi_rx_valid(pdi_rx_valid),
        .pdi_rx_ready(pdi_rx_ready),
        .pdi_rx_data(pdi_rx_data),
        .pdi_rx_last(pdi_rx_last),
        .pdi_tx_valid(pdi_tx_valid),
        .pdi_tx_ready(pdi_tx_ready),
        .pdi_tx_data(pdi_tx_data),
        .pdi_tx_last(pdi_tx_last),
        .authorized_capability_mask(authorized_capability_mask)
    );

    // 100 MHz clock
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Watchdog
    initial begin
        #200000;
        $display("[FAIL] Watchdog timeout in tb_pdi_k8_selected_work!");
        $finish(1);
    end

    // Tasks for streaming words
    task automatic send_rx_word(input logic [31:0] w, input logic is_last);
        begin
            @(posedge clk);
            while (!pdi_rx_ready) @(posedge clk);
            pdi_rx_valid <= 1'b1;
            pdi_rx_data  <= w;
            pdi_rx_last  <= is_last;
            @(posedge clk);
            pdi_rx_valid <= 1'b0;
            pdi_rx_last  <= 1'b0;
        end
    endtask

    logic [31:0] pkt [0:15];
    logic [31:0] test_crc;

    task automatic compute_pkt_crc();
        begin
            test_crc = 32'hFFFFFFFF;
            for (int i = 0; i < 15; i++) begin
                test_crc = dut.u_ingress.crc32_word(test_crc, pkt[i]);
            end
            pkt[15] = test_crc ^ 32'hFFFFFFFF;
        end
    endtask

    logic [31:0] rx_disp_words [0:15];
    int disp_word_idx;

    task automatic capture_disposition();
        begin
            disp_word_idx = 0;
            while (disp_word_idx < 16) begin
                @(posedge clk);
                if (pdi_tx_valid && pdi_tx_ready) begin
                    rx_disp_words[disp_word_idx] = pdi_tx_data;
                    disp_word_idx++;
                end
            end
        end
    endtask

    // Dispatch a test vector and verify outcomes
    task automatic run_test_vector(
        input string test_id,
        input string name,
        input int seq_id,
        input int prop_id,
        input logic [7:0] opcode,
        input logic [7:0] dest,
        input logic [7:0] src_a,
        input logic [7:0] src_b,
        input logic [31:0] auth_token,
        input logic [31:0] assumed_ver,
        input logic [7:0] exp_outcome,
        input logic [31:0] exp_reason
    );
        int cycle_start;
        int cycle_end;
        int cycles_elapsed;
        logic [7:0] act_outcome;
        logic [31:0] act_reason;
        logic [31:0] ev_digest;

        begin
            pkt[0]  = 32'h50444930;
            pkt[1]  = 32'h00100101;
            pkt[2]  = seq_id;
            pkt[3]  = prop_id;
            pkt[4]  = assumed_ver;
            pkt[5]  = {src_b, src_a, dest, opcode};
            pkt[6]  = auth_token;
            if (test_id == "R14") begin
                pkt[7]  = 32'h00000002; // has_gmut = 1
                pkt[12] = 32'd500;      // g_node = 500 >= GRAPH_NODES(256)
            end else begin
                pkt[7]  = 32'd0;
                pkt[12] = 32'd0;
            end
            pkt[8]  = 32'd0;
            pkt[9]  = 32'd0;
            pkt[10] = 32'd0;
            pkt[11] = 32'd0;
            pkt[13] = 32'd0;
            pkt[14] = 32'd0;
            compute_pkt_crc();

            cycle_start = $time / 10;
            fork
                begin
                    for (int i = 0; i < 16; i++) send_rx_word(pkt[i], (i == 15));
                end
                begin
                    capture_disposition();
                end
            join
            cycle_end = $time / 10;
            cycles_elapsed = cycle_end - cycle_start;

            act_outcome = (rx_disp_words[1] >> 16) & 8'hFF;
            act_reason  = rx_disp_words[4];
            ev_digest   = rx_disp_words[7];

            $display("RESULT | %s | %s | exp_out=%0d act_out=%0d | exp_rsn=%0d act_rsn=%0d | cycles=%0d | ev=0x%08x",
                test_id, name, exp_outcome, act_outcome, exp_reason, act_reason, cycles_elapsed, ev_digest);

            if (act_outcome != exp_outcome || act_reason != exp_reason) begin
                $display("[FAIL] Vector %s mismatch!", test_id);
                $finish(1);
            end

            #20;
        end
    endtask

    initial begin
        reset_n                    = 0;
        boot_trigger               = 0;
        pdi_rx_valid               = 0;
        pdi_rx_data                = 0;
        pdi_rx_last                = 0;
        pdi_tx_ready               = 1;
        authorized_capability_mask = 32'h00000001; // Grant default capability

        #20;
        @(negedge clk);
        reset_n = 1;
        #20;

        $display("=== PDI-135M-v0.3: RTL Differential Equivalence (R01-R15 Matrix) ===");
        $display("=== STEP 0: BOOT AND INITIALIZATION ===");
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        while (!boot_complete) @(posedge clk);
        $display("PASS: Fabric boot completed. Starting R01-R15 test matrix...");
        #20;

        // R01: OP_ADD
        run_test_vector("R01", "OP_ADD", 101, 1001, 8'd1, 8'd12, 8'd10, 8'd11, 32'h1, 32'd0, 8'd0, 32'd0);

        // R02: OP_SUB
        run_test_vector("R02", "OP_SUB", 102, 1002, 8'd2, 8'd15, 8'd13, 8'd14, 32'h1, 32'd0, 8'd0, 32'd0);

        // R03: OP_MUL
        run_test_vector("R03", "OP_MUL", 103, 1003, 8'd3, 8'd22, 8'd20, 8'd21, 32'h1, 32'd0, 8'd0, 32'd0);

        // R04: OP_CL20_PRODUCT
        run_test_vector("R04", "OP_CL20_PRODUCT", 104, 1004, 8'd5, 8'd42, 8'd40, 8'd41, 32'h1, 32'd0, 8'd0, 32'd0);

        // R05: OP_REVERSE
        run_test_vector("R05", "OP_REVERSE", 105, 1005, 8'd6, 8'd52, 8'd50, 8'd0, 32'h1, 32'd0, 8'd0, 32'd0);

        // R06: OP_GRADE_INVOLUTION
        run_test_vector("R06", "OP_GRADE_INVOLUTION", 106, 1006, 8'd7, 8'd62, 8'd60, 8'd0, 32'h1, 32'd0, 8'd0, 32'd0);

        // R07: OP_CLIFFORD_CONJUGATE
        run_test_vector("R07", "OP_CLIFFORD_CONJUGATE", 107, 1007, 8'd8, 8'd72, 8'd70, 8'd0, 32'h1, 32'd0, 8'd0, 32'd0);

        // R08: OP_VECTOR_DOT
        run_test_vector("R08", "OP_VECTOR_DOT", 108, 1008, 8'd9, 8'd82, 8'd80, 8'd81, 32'h1, 32'd0, 8'd0, 32'd0);

        // R09: OP_VECTOR_WEDGE
        run_test_vector("R09", "OP_VECTOR_WEDGE", 109, 1009, 8'd10, 8'd92, 8'd90, 8'd91, 32'h1, 32'd0, 8'd0, 32'd0);

        // R10: OP_COMPARE
        run_test_vector("R10", "OP_COMPARE", 110, 1010, 8'd4, 8'd0, 8'd32, 8'd33, 32'h1, 32'd0, 8'd0, 32'd0);

        // R11: Unknown Operator (Opcode 42) -> Refusal
        run_test_vector("R11", "ERR_UNKNOWN_OPERATOR", 111, 1011, 8'd42, 8'd12, 8'd10, 8'd11, 32'h1, 32'd0, 8'd2, 32'd4);

        // R12: Unauthorized Capability (0x80000000) -> Refusal
        run_test_vector("R12", "ERR_UNAUTHORIZED_CAPABILITY", 112, 1012, 8'd1, 8'd12, 8'd10, 8'd11, 32'h80000000, 32'd0, 8'd2, 32'd7);

        // R13: State Version Mismatch (Stale Version 2000 >= 1000) -> Refusal
        run_test_vector("R13", "ERR_STALE_STATE_VERSION", 113, 1013, 8'd1, 8'd12, 8'd10, 8'd11, 32'h1, 32'd2000, 8'd2, 32'd6);

        // R14: Out of Bounds Graph Reference (Node 500 >= GRAPH_NODES=256) -> Refusal
        run_test_vector("R14", "ERR_OUT_OF_BOUNDS", 114, 1014, 8'd1, 8'd12, 8'd10, 8'd11, 32'h1, 32'd0, 8'd2, 32'd5);

        // R15: NOP / State Preservation (Opcode 0) -> Commit without mutation
        run_test_vector("R15", "OP_NOP", 115, 1015, 8'd0, 8'd0, 8'd0, 8'd0, 32'h1, 32'd0, 8'd0, 32'd0);

        $display("=== ALL R01-R15 TEST VECTORS PASSED IDENTICALLY IN RTL! ===");
        $finish(0);
    end

endmodule
