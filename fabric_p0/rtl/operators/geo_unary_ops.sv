// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_unary_ops
// Unary multivector involutions and grade projections

`ifndef GEO_UNARY_OPS_SV
`define GEO_UNARY_OPS_SV

`timescale 1ns/1ps

module geo_unary_ops #(
    parameter int WIDTH = 32
) (
    input  logic signed [WIDTH-1:0] in_s,
    input  logic signed [WIDTH-1:0] in_e1,
    input  logic signed [WIDTH-1:0] in_e2,
    input  logic signed [WIDTH-1:0] in_e12,
    input  logic [2:0]              op_sel, // 0: REV, 1: GR_INV, 2: CLIFF_CONJ, 3: SCALAR_PROJ, 4: VEC_PROJ, 5: BIVEC_PROJ

    output logic signed [WIDTH-1:0] out_s,
    output logic signed [WIDTH-1:0] out_e1,
    output logic signed [WIDTH-1:0] out_e2,
    output logic signed [WIDTH-1:0] out_e12,
    output logic                    overflow
);

    localparam logic signed [WIDTH-1:0] INT_MIN = {1'b1, {(WIDTH-1){1'b0}}};

    // Checked negations
    logic neg_e1_ovf, neg_e2_ovf, neg_e12_ovf;
    logic signed [WIDTH-1:0] neg_e1, neg_e2, neg_e12;

    assign neg_e1_ovf  = (in_e1 == INT_MIN);
    assign neg_e2_ovf  = (in_e2 == INT_MIN);
    assign neg_e12_ovf = (in_e12 == INT_MIN);

    assign neg_e1  = neg_e1_ovf ? '0 : -in_e1;
    assign neg_e2  = neg_e2_ovf ? '0 : -in_e2;
    assign neg_e12 = neg_e12_ovf ? '0 : -in_e12;

    always_comb begin
        out_s    = '0;
        out_e1   = '0;
        out_e2   = '0;
        out_e12  = '0;
        overflow = 1'b0;

        case (op_sel)
            3'd0: begin // Reverse: (s, e1, e2, -e12)
                out_s    = in_s;
                out_e1   = in_e1;
                out_e2   = in_e2;
                out_e12  = neg_e12;
                overflow = neg_e12_ovf;
            end
            3'd1: begin // Grade Involution: (s, -e1, -e2, e12)
                out_s    = in_s;
                out_e1   = neg_e1;
                out_e2   = neg_e2;
                out_e12  = in_e12;
                overflow = neg_e1_ovf || neg_e2_ovf;
            end
            3'd2: begin // Clifford Conjugation: (s, -e1, -e2, -e12)
                out_s    = in_s;
                out_e1   = neg_e1;
                out_e2   = neg_e2;
                out_e12  = neg_e12;
                overflow = neg_e1_ovf || neg_e2_ovf || neg_e12_ovf;
            end
            3'd3: begin // Scalar Projection: (s, 0, 0, 0)
                out_s    = in_s;
                out_e1   = '0;
                out_e2   = '0;
                out_e12  = '0;
                overflow = 1'b0;
            end
            3'd4: begin // Vector Projection: (0, e1, e2, 0)
                out_s    = '0;
                out_e1   = in_e1;
                out_e2   = in_e2;
                out_e12  = '0;
                overflow = 1'b0;
            end
            3'd5: begin // Bivector Projection: (0, 0, 0, e12)
                out_s    = '0;
                out_e1   = '0;
                out_e2   = '0;
                out_e12  = in_e12;
                overflow = 1'b0;
            end
            default: begin
                overflow = 1'b1;
            end
        endcase

        if (overflow) begin
            out_s   = '0;
            out_e1  = '0;
            out_e2  = '0;
            out_e12 = '0;
        end
    end

endmodule

`endif // GEO_UNARY_OPS_SV
