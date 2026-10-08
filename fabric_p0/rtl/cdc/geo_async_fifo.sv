// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_async_fifo
// Parameterized Dual-Clock Asynchronous FIFO with Gray-Code Pointer Crossing

`ifndef GEO_ASYNC_FIFO_SV
`define GEO_ASYNC_FIFO_SV

`timescale 1ns/1ps

module geo_async_fifo #(
    parameter int DWIDTH     = 128,
    parameter int AWIDTH     = 4,
    parameter int SYNC_DEPTH = 2
) (
    // Write Domain
    input  logic              wclk,
    input  logic              wrst_n,
    input  logic              winc,
    input  logic [DWIDTH-1:0] wdata,
    output logic              wfull,
    output logic              walmost_full,

    // Read Domain
    input  logic              rclk,
    input  logic              rrst_n,
    input  logic              rinc,
    output logic [DWIDTH-1:0] rdata,
    output logic              rempty,
    output logic              ralmost_empty
);

    localparam int DEPTH = 1 << AWIDTH;

    // Dual-Port RAM storage
    logic [DWIDTH-1:0] mem [0:DEPTH-1];

    // Write domain pointers
    logic [AWIDTH:0] wptr_bin, wptr_bin_next;
    logic [AWIDTH:0] wptr_gray, wptr_gray_next;
    logic [AWIDTH:0] rptr_gray_sync;

    // Read domain pointers
    logic [AWIDTH:0] rptr_bin, rptr_bin_next;
    logic [AWIDTH:0] rptr_gray, rptr_gray_next;
    logic [AWIDTH:0] wptr_gray_sync;

    // Synchronizers
    geo_sync_2ff #(.WIDTH(AWIDTH+1)) u_sync_r2w (
        .clk(wclk),
        .rst_n(wrst_n),
        .din(rptr_gray),
        .dout(rptr_gray_sync)
    );

    geo_sync_2ff #(.WIDTH(AWIDTH+1)) u_sync_w2r (
        .clk(rclk),
        .rst_n(rrst_n),
        .din(wptr_gray),
        .dout(wptr_gray_sync)
    );

    // ------------------------------------------------------------------------
    // Write Domain Logic
    // ------------------------------------------------------------------------
    assign wptr_bin_next  = wptr_bin + (winc & ~wfull);
    assign wptr_gray_next = (wptr_bin_next >> 1) ^ wptr_bin_next;

    always_ff @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wptr_bin  <= '0;
            wptr_gray <= '0;
        end else begin
            wptr_bin  <= wptr_bin_next;
            wptr_gray <= wptr_gray_next;
        end
    end

    // Memory write
    always_ff @(posedge wclk) begin
        if (winc && !wfull) begin
            mem[wptr_bin[AWIDTH-1:0]] <= wdata;
        end
    end

    // Full detection: MSBs differ, MSB-1 differ, LSBs match
    wire wfull_val = (wptr_gray_next == {~rptr_gray_sync[AWIDTH:AWIDTH-1], rptr_gray_sync[AWIDTH-2:0]});

    always_ff @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wfull        <= 1'b0;
            walmost_full <= 1'b0;
        end else begin
            wfull        <= wfull_val;
            walmost_full <= (wptr_bin_next - rptr_bin) >= (DEPTH - 2);
        end
    end

    // ------------------------------------------------------------------------
    // Read Domain Logic
    // ------------------------------------------------------------------------
    assign rptr_bin_next  = rptr_bin + (rinc & ~rempty);
    assign rptr_gray_next = (rptr_bin_next >> 1) ^ rptr_bin_next;

    always_ff @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rptr_bin  <= '0;
            rptr_gray <= '0;
        end else begin
            rptr_bin  <= rptr_bin_next;
            rptr_gray <= rptr_gray_next;
        end
    end

    // Memory read
    assign rdata = mem[rptr_bin[AWIDTH-1:0]];

    // Empty detection: pointers strictly equal
    wire rempty_val = (rptr_gray_next == wptr_gray_sync);

    always_ff @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rempty        <= 1'b1;
            ralmost_empty <= 1'b1;
        end else begin
            rempty        <= rempty_val;
            ralmost_empty <= (wptr_bin - rptr_bin_next) <= 1;
        end
    end

endmodule

`endif // GEO_ASYNC_FIFO_SV
