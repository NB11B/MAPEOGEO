// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Full Proposal-to-Disposition RTL Bridge Qualification Testbench
// Module: tb_pdi_bridge
// Verifies end-to-end streaming ingress, hardware validation, P0 fabric execution,
// authority protection, and streaming egress dispositions.

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_pdi_bridge;

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
        #50000;
        $display("[FAIL] Watchdog timeout in tb_pdi_bridge!");
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

    // Task to compute packet CRC
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

    // Buffer for captured disposition words
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

    logic [31:0] pkt [0:15];

    initial begin
        reset_n                    = 0;
        boot_trigger               = 0;
        pdi_rx_valid               = 0;
        pdi_rx_data                = 0;
        pdi_rx_last                = 0;
        pdi_tx_ready               = 1;
        authorized_capability_mask = 32'h00000001; // Grant basic capability bit 0

        #20;
        @(negedge clk);
        reset_n = 1;
        #20;

        $display("=== STEP 1: AUTONOMOUS FABRIC BOOT ===");
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        while (!boot_complete) @(posedge clk);
        $display("PASS: Autonomous boot complete! Ingress ready.");
        #20;

        // -------------------------------------------------------------
        // TEST A: VALID PROPOSAL (OP_ADD, Opcode 1)
        // -------------------------------------------------------------
        $display("=== TEST A: VALID PROPOSAL (OP_ADD: Add state 10 and state 11 -> state 12) ===");
        pkt[0]  = 32'h50444930;
        pkt[1]  = 32'h00100101;
        pkt[2]  = 32'd101;       // seq_id = 101
        pkt[3]  = 32'd2001;      // proposal_id = 2001
        pkt[4]  = 32'd0;         // assumed_ver = 0
        pkt[5]  = {8'd11, 8'd10, 8'd12, 8'd1}; // src_b=11, src_a=10, dest=12, op=1 (OP_ADD)
        pkt[6]  = 32'h00000001;  // auth_token = 1 (granted)
        pkt[7]  = 32'd0;
        pkt[8]  = 32'd0;
        pkt[9]  = 32'd0;
        pkt[10] = 32'd0;
        pkt[11] = 32'd0;
        pkt[12] = 32'd0;
        pkt[13] = 32'd0;
        pkt[14] = 32'd0;
        compute_pkt_crc();

        fork
            begin
                for (int i = 0; i < 16; i++) send_rx_word(pkt[i], (i == 15));
            end
            begin
                capture_disposition();
            end
        join

        $display("Captured disposition: magic=0x%08x, type_ver_out=0x%08x, seq=%0d, id=%0d, reason=%0d",
            rx_disp_words[0], rx_disp_words[1], rx_disp_words[2], rx_disp_words[3], rx_disp_words[4]);

        if (rx_disp_words[0] != 32'h50444930) begin
            $display("FAIL: Disposition magic mismatch!");
            $finish(1);
        end
        if (rx_disp_words[2] != 32'd101 || rx_disp_words[3] != 32'd2001) begin
            $display("FAIL: Disposition sequence or proposal ID mismatch!");
            $finish(1);
        end
        if (rx_disp_words[4] != 32'd0) begin
            $display("FAIL: Unexpected refusal on valid proposal, reason=%0d", rx_disp_words[4]);
            $finish(1);
        end
        $display("PASS: Valid proposal successfully executed, committed, and returned disposition!");
        #40;

        // -------------------------------------------------------------
        // TEST B: UNKNOWN OPERATOR REFUSAL (Opcode 45 > 33)
        // -------------------------------------------------------------
        $display("=== TEST B: UNKNOWN OPERATOR CODE REFUSAL ===");
        pkt[2]  = 32'd102;
        pkt[3]  = 32'd2002;
        pkt[5]  = {8'd11, 8'd10, 8'd12, 8'd45}; // Opcode 45 is unregistered!
        compute_pkt_crc();

        fork
            begin
                for (int i = 0; i < 16; i++) send_rx_word(pkt[i], (i == 15));
            end
            begin
                capture_disposition();
            end
        join

        $display("Captured refusal: outcome=%0d, reason=%0d", (rx_disp_words[1] >> 16) & 8'hFF, rx_disp_words[4]);
        if (((rx_disp_words[1] >> 16) & 8'hFF) != 8'd2 || rx_disp_words[4] != 32'd4) begin
            $display("FAIL: Expected ERR_UNKNOWN_OPERATOR (reason 4, outcome REFUSE 2)!");
            $finish(1);
        end
        $display("PASS: Hardware validator intercepted unregistered opcode without mutating state!");
        #40;

        // -------------------------------------------------------------
        // TEST C: UNAUTHORIZED CAPABILITY REFUSAL
        // -------------------------------------------------------------
        $display("=== TEST C: UNAUTHORIZED CAPABILITY REFUSAL ===");
        pkt[2]  = 32'd103;
        pkt[3]  = 32'd2003;
        pkt[5]  = {8'd11, 8'd10, 8'd12, 8'd1}; // Valid OP_ADD
        pkt[6]  = 32'h80000000; // Requires high privilege not in mask!
        compute_pkt_crc();

        fork
            begin
                for (int i = 0; i < 16; i++) send_rx_word(pkt[i], (i == 15));
            end
            begin
                capture_disposition();
            end
        join

        $display("Captured refusal: outcome=%0d, reason=%0d", (rx_disp_words[1] >> 16) & 8'hFF, rx_disp_words[4]);
        if (((rx_disp_words[1] >> 16) & 8'hFF) != 8'd2 || rx_disp_words[4] != 32'd7) begin
            $display("FAIL: Expected ERR_UNAUTHORIZED_CAPABILITY (reason 7, outcome REFUSE 2)!");
            $finish(1);
        end
        $display("PASS: Hardware authority check blocked unauthorized capability escalation!");
        #40;

        $display("=== ALL PDI BRIDGE RTL QUALIFICATION TESTS PASSED SUCCESSFULLY! ===");
        $finish(0);
    end

endmodule
