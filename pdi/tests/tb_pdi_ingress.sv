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

    // Task to send a 16-word packet
    task automatic send_packet(input logic [31:0] words [0:15]);
        begin
            for (int i = 0; i < 16; i++) begin
                @(posedge clk);
                while (!pdi_rx_ready) @(posedge clk);
                pdi_rx_valid <= 1'b1;
                pdi_rx_data  <= words[i];
                pdi_rx_last  <= (i == 15);
            end
            @(posedge clk);
            pdi_rx_valid <= 1'b0;
            pdi_rx_last  <= 1'b0;
        end
    endtask

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

        $display("=== PDI INGRESS TESTBENCH READY ===");
        $finish;
    end

endmodule
