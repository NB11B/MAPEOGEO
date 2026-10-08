// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Testbench for Streaming Ingress Unit
// Module: tb_pdi_ingress

`timescale 1ns/1ps

`include "pdi_ingress.sv"

module tb_pdi_ingress;

    logic        clk;
    logic        reset_n;
    logic        pdi_rx_valid;
    logic        pdi_rx_ready;
    logic [31:0] pdi_rx_data;
    logic        pdi_rx_last;

    logic        pkt_assembled_valid;
    logic        pkt_consumed_ack;
    logic [511:0] pkt_raw_data;
    logic        pkt_framing_error;
    logic        pkt_crc_error;

    pdi_ingress #(
        .PACKET_WORDS(16)
    ) dut (
        .clk(clk),
        .reset_n(reset_n),
        .pdi_rx_valid(pdi_rx_valid),
        .pdi_rx_ready(pdi_rx_ready),
        .pdi_rx_data(pdi_rx_data),
        .pdi_rx_last(pdi_rx_last),
        .pkt_assembled_valid(pkt_assembled_valid),
        .pkt_consumed_ack(pkt_consumed_ack),
        .pkt_raw_data(pkt_raw_data),
        .pkt_framing_error(pkt_framing_error),
        .pkt_crc_error(pkt_crc_error)
    );

    // Clock generation: 100 MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Task to send a word
    task automatic send_word(input logic [31:0] w, input logic is_last);
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

    logic [31:0] test_words [0:15];
    logic [31:0] test_crc;

    // Simulation sequence
    initial begin
        reset_n          = 0;
        pdi_rx_valid     = 0;
        pdi_rx_data      = 0;
        pdi_rx_last      = 0;
        pkt_consumed_ack = 0;

        #20;
        reset_n = 1;
        #20;

        $display("=== TEST 1: STREAM VALID 16-WORD PACKET ===");
        test_words[0]  = 32'h50444930; // Magic "PDI0"
        test_words[1]  = 32'h00100101; // total_words=16, ver=1, type=1
        test_words[2]  = 32'd1;        // seq_id=1
        test_words[3]  = 32'd1000;     // proposal_id=1000
        test_words[4]  = 32'd50;       // assumed_ver=50
        test_words[5]  = 32'h02010001; // src_b=2, src_a=1, dest=0, op=1 (OP_ADD)
        test_words[6]  = 32'h00000001; // auth_token=1
        test_words[7]  = 32'd0;
        test_words[8]  = 32'd0;
        test_words[9]  = 32'd0;
        test_words[10] = 32'd0;
        test_words[11] = 32'd0;
        test_words[12] = 32'd0;
        test_words[13] = 32'd0;
        test_words[14] = 32'd0;

        // Compute expected CRC
        test_crc = 32'hFFFFFFFF;
        for (int i = 0; i < 15; i++) begin
            test_crc = dut.crc32_word(test_crc, test_words[i]);
        end
        test_words[15] = test_crc ^ 32'hFFFFFFFF;

        // Send all 16 words
        for (int i = 0; i < 16; i++) begin
            send_word(test_words[i], (i == 15));
        end

        // Wait for assembly
        @(posedge clk);
        while (!pkt_assembled_valid) @(posedge clk);

        if (pkt_framing_error) begin
            $display("FAIL: Unexpected framing error on valid packet");
            $finish(1);
        end
        if (pkt_crc_error) begin
            $display("FAIL: CRC mismatch on valid packet");
            $finish(1);
        end
        $display("PASS: Packet assembled with valid CRC!");

        // Acknowledge packet
        pkt_consumed_ack <= 1'b1;
        @(posedge clk);
        pkt_consumed_ack <= 1'b0;
        #20;

        $display("=== TEST 2: CORRUPTED CRC DETECTION ===");
        // Corrupt CRC
        test_words[15] = test_words[15] ^ 32'h00000001;
        for (int i = 0; i < 16; i++) begin
            send_word(test_words[i], (i == 15));
        end

        @(posedge clk);
        while (!pkt_assembled_valid) @(posedge clk);

        if (!pkt_crc_error) begin
            $display("FAIL: Corrupted CRC was not detected!");
            $finish(1);
        end
        $display("PASS: Corrupted CRC correctly detected and flagged!");

        pkt_consumed_ack <= 1'b1;
        @(posedge clk);
        pkt_consumed_ack <= 1'b0;
        #20;

        $display("=== ALL INGRESS TESTS PASSED SUCCESSFULLY ===");
        $finish(0);
    end

endmodule
