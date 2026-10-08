// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_reset_sync
// Asynchronous Assert, Synchronous Deassert Reset Synchronizer (RDC)

`ifndef GEO_RESET_SYNC_SV
`define GEO_RESET_SYNC_SV

`timescale 1ns/1ps

module geo_reset_sync (
    input  logic clk,
    input  logic async_rst_n,
    output logic sync_rst_n
);

    (* ASYNC_REG = "TRUE" *) logic rst_stage1;
    (* ASYNC_REG = "TRUE" *) logic rst_stage2;

    always_ff @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n) begin
            rst_stage1 <= 1'b0;
            rst_stage2 <= 1'b0;
        end else begin
            rst_stage1 <= 1'b1;
            rst_stage2 <= rst_stage1;
        end
    end

    assign sync_rst_n = rst_stage2;

endmodule

`endif // GEO_RESET_SYNC_SV
