// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_sync_2ff
// 2-Flop CDC Synchronizer with ASYNC_REG placement constraint

`ifndef GEO_SYNC_2FF_SV
`define GEO_SYNC_2FF_SV

`timescale 1ns/1ps

module geo_sync_2ff #(
    parameter int WIDTH = 1,
    parameter logic [WIDTH-1:0] RESET_VAL = '0
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [WIDTH-1:0] din,
    output logic [WIDTH-1:0] dout
);

    (* ASYNC_REG = "TRUE" *) logic [WIDTH-1:0] sync_stage1;
    (* ASYNC_REG = "TRUE" *) logic [WIDTH-1:0] sync_stage2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_stage1 <= RESET_VAL;
            sync_stage2 <= RESET_VAL;
        end else begin
            sync_stage1 <= din;
            sync_stage2 <= sync_stage1;
        end
    end

    assign dout = sync_stage2;

endmodule

`endif // GEO_SYNC_2FF_SV
