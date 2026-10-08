// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_matrix_bridge
// Deterministic bidirectional isomorphism between M_2(R) and Cl(2,0)
// Section 5.3: phi(AB) = phi(A) * phi(B)

`ifndef GEO_MATRIX_BRIDGE_SV
`define GEO_MATRIX_BRIDGE_SV

`timescale 1ns/1ps

module geo_matrix_bridge #(
    parameter int WIDTH = 32
) (
    // Matrix inputs A = [a, b; c, d]
    input  logic signed [WIDTH-1:0] mat_a,
    input  logic signed [WIDTH-1:0] mat_b,
    input  logic signed [WIDTH-1:0] mat_c,
    input  logic signed [WIDTH-1:0] mat_d,

    // Multivector inputs MV = s + x*e1 + y*e2 + z*e12
    input  logic signed [WIDTH-1:0] mv_s,
    input  logic signed [WIDTH-1:0] mv_e1,
    input  logic signed [WIDTH-1:0] mv_e2,
    input  logic signed [WIDTH-1:0] mv_e12,

    input  logic                    direction, // 0: Matrix -> Cl(2,0), 1: Cl(2,0) -> Matrix

    // Matrix outputs
    output logic signed [WIDTH-1:0] out_mat_a,
    output logic signed [WIDTH-1:0] out_mat_b,
    output logic signed [WIDTH-1:0] out_mat_c,
    output logic signed [WIDTH-1:0] out_mat_d,

    // Multivector outputs
    output logic signed [WIDTH-1:0] out_mv_s,
    output logic signed [WIDTH-1:0] out_mv_e1,
    output logic signed [WIDTH-1:0] out_mv_e2,
    output logic signed [WIDTH-1:0] out_mv_e12,

    output logic                    overflow
);

    // --- Forward Mapping: M_2(R) -> Cl(2,0) ---
    // s = (a + d) / 2
    // x = (a - d) / 2
    // y = (b + c) / 2
    // z = (b - c) / 2
    logic signed [WIDTH:0] ext_s, ext_x, ext_y, ext_z;
    assign ext_s = {mat_a[WIDTH-1], mat_a} + {mat_d[WIDTH-1], mat_d};
    assign ext_x = {mat_a[WIDTH-1], mat_a} - {mat_d[WIDTH-1], mat_d};
    assign ext_y = {mat_b[WIDTH-1], mat_b} + {mat_c[WIDTH-1], mat_c};
    assign ext_z = {mat_b[WIDTH-1], mat_b} - {mat_c[WIDTH-1], mat_c};

    // Forward division by 2 via arithmetic shift (no overflow possible)
    logic signed [WIDTH-1:0] fwd_s, fwd_x, fwd_y, fwd_z;
    assign fwd_s = ext_s[WIDTH:1];
    assign fwd_x = ext_x[WIDTH:1];
    assign fwd_y = ext_y[WIDTH:1];
    assign fwd_z = ext_z[WIDTH:1];

    // --- Inverse Mapping: Cl(2,0) -> M_2(R) ---
    // a = s + x
    // b = y + z
    // c = y - z
    // d = s - x
    logic signed [WIDTH:0] ext_inv_a, ext_inv_b, ext_inv_c, ext_inv_d;
    assign ext_inv_a = {mv_s[WIDTH-1], mv_s}   + {mv_e1[WIDTH-1], mv_e1};
    assign ext_inv_b = {mv_e2[WIDTH-1], mv_e2} + {mv_e12[WIDTH-1], mv_e12};
    assign ext_inv_c = {mv_e2[WIDTH-1], mv_e2} - {mv_e12[WIDTH-1], mv_e12};
    assign ext_inv_d = {mv_s[WIDTH-1], mv_s}   - {mv_e1[WIDTH-1], mv_e1};

    logic inv_ovf;
    assign inv_ovf = (ext_inv_a[WIDTH] != ext_inv_a[WIDTH-1]) ||
                     (ext_inv_b[WIDTH] != ext_inv_b[WIDTH-1]) ||
                     (ext_inv_c[WIDTH] != ext_inv_c[WIDTH-1]) ||
                     (ext_inv_d[WIDTH] != ext_inv_d[WIDTH-1]);

    logic signed [WIDTH-1:0] inv_a_trunc, inv_b_trunc, inv_c_trunc, inv_d_trunc;
    assign inv_a_trunc = ext_inv_a[WIDTH-1:0];
    assign inv_b_trunc = ext_inv_b[WIDTH-1:0];
    assign inv_c_trunc = ext_inv_c[WIDTH-1:0];
    assign inv_d_trunc = ext_inv_d[WIDTH-1:0];

    always @* begin
        out_mat_a  = '0;
        out_mat_b  = '0;
        out_mat_c  = '0;
        out_mat_d  = '0;
        out_mv_s   = '0;
        out_mv_e1  = '0;
        out_mv_e2  = '0;
        out_mv_e12 = '0;
        overflow   = 1'b0;

        if (direction == 1'b0) begin
            // Matrix -> Cl(2,0)
            out_mv_s   = fwd_s;
            out_mv_e1  = fwd_x;
            out_mv_e2  = fwd_y;
            out_mv_e12 = fwd_z;
            overflow   = 1'b0;
        end else begin
            // Cl(2,0) -> Matrix
            overflow   = inv_ovf;
            out_mat_a  = inv_ovf ? '0 : inv_a_trunc;
            out_mat_b  = inv_ovf ? '0 : inv_b_trunc;
            out_mat_c  = inv_ovf ? '0 : inv_c_trunc;
            out_mat_d  = inv_ovf ? '0 : inv_d_trunc;
        end
    end

endmodule

`endif // GEO_MATRIX_BRIDGE_SV
