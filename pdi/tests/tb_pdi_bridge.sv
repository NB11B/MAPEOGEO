// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Full Proposal-to-Disposition RTL Bridge Testbench
// Module: tb_pdi_bridge

`timescale 1ns/1ps

`include "geo_defs.svh"
`include "pdi_uow_bridge.sv"

module tb_pdi_bridge;

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
        .WORK_CELL_COUNT(4),
        .OPERATOR_LANES(1),
        .MEMORY_BANKS(1),
        .AUTHORITY_ENGINES(1)
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

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        reset_n                    = 0;
        boot_trigger               = 0;
        pdi_rx_valid               = 0;
        pdi_rx_data                = 0;
        pdi_rx_last                = 0;
        pdi_tx_ready               = 1;
        authorized_capability_mask = 32'hFFFFFFFF;

        #20;
        reset_n = 1;
        #20;
        boot_trigger = 1;
        #10;
        boot_trigger = 0;

        $display("=== PDI BRIDGE TESTBENCH READY FOR EXECUTION ON USER SIGNAL ===");
        $finish;
    end

endmodule
