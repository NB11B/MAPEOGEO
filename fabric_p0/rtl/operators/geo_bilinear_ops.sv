// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_bilinear_ops
// Bilinear geometric operations: Dot, Wedge, Commutator, Anticommutator, Norm Squared

`ifndef GEO_BILINEAR_OPS_SV
`define GEO_BILINEAR_OPS_SV

`timescale 1ns/1ps

module geo_bilinear_ops #(
    parameter int WIDTH = 32,
    parameter int FRAC  = 16
) (
    input  logic signed [WIDTH-1:0] a_s,
    input  logic signed [WIDTH-1:0] a_e1,
    input  logic signed [WIDTH-1:0] a_e2,
    input  logic signed [WIDTH-1:0] a_e12,

    input  logic signed [WIDTH-1:0] b_s,
    input  logic signed [WIDTH-1:0] b_e1,
    input  logic signed [WIDTH-1:0] b_e2,
    input  logic signed [WIDTH-1:0] b_e12,

    input  logic [2:0]              op_sel, // 0: DOT, 1: WEDGE, 2: COMMUTATOR, 3: ANTICOMMUTATOR, 4: NORM_SQUARED

    output logic signed [WIDTH-1:0] out_s,
    output logic signed [WIDTH-1:0] out_e1,
    output logic signed [WIDTH-1:0] out_e2,
    output logic signed [WIDTH-1:0] out_e12,
    output logic                    overflow
);

    // Instances of geometric product for AB and BA
    logic signed [WIDTH-1:0] ab_s, ab_e1, ab_e2, ab_e12;
    logic                    ab_ovf;
    geo_cl20_multivector #(.WIDTH(WIDTH), .FRAC(FRAC)) u_ab (
        .a_s(a_s), .a_e1(a_e1), .a_e2(a_e2), .a_e12(a_e12),
        .b_s(b_s), .b_e1(b_e1), .b_e2(b_e2), .b_e12(b_e12),
        .y_s(ab_s), .y_e1(ab_e1), .y_e2(ab_e2), .y_e12(ab_e12),
        .overflow(ab_ovf)
    );

    logic signed [WIDTH-1:0] ba_s, ba_e1, ba_e2, ba_e12;
    logic                    ba_ovf;
    geo_cl20_multivector #(.WIDTH(WIDTH), .FRAC(FRAC)) u_ba (
        .a_s(b_s), .a_e1(b_e1), .a_e2(b_e2), .a_e12(b_e12),
        .b_s(a_s), .b_e1(a_e1), .b_e2(a_e2), .b_e12(a_e12),
        .y_s(ba_s), .y_e1(ba_e1), .y_e2(ba_e2), .y_e12(ba_e12),
        .overflow(ba_ovf)
    );

    // Multipliers for Dot & Wedge
    logic signed [WIDTH-1:0] p_e1e1, p_e2e2, p_e1e2, p_e2e1;
    logic                    ovf_e1e1, ovf_e2e2, ovf_e1e2, ovf_e2e1;

    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul1 (
        .a(a_e1), .b(b_e1), .prod(p_e1e1), .mul_overflow(ovf_e1e1),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );

    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul2 (
        .a(a_e2), .b(b_e2), .prod(p_e2e2), .mul_overflow(ovf_e2e2),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );

    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul3 (
        .a(a_e1), .b(b_e2), .prod(p_e1e2), .mul_overflow(ovf_e1e2),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );

    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul4 (
        .a(a_e2), .b(b_e1), .prod(p_e2e1), .mul_overflow(ovf_e2e1),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );

    // Dot sum: p_e1e1 + p_e2e2
    logic signed [WIDTH:0] dot_ext;
    assign dot_ext = {p_e1e1[WIDTH-1], p_e1e1} + {p_e2e2[WIDTH-1], p_e2e2};
    logic dot_ovf;
    assign dot_ovf = ovf_e1e1 || ovf_e2e2 || (dot_ext[WIDTH] != dot_ext[WIDTH-1]);

    // Wedge diff: p_e1e2 - p_e2e1
    logic signed [WIDTH:0] wedge_ext;
    assign wedge_ext = {p_e1e2[WIDTH-1], p_e1e2} - {p_e2e1[WIDTH-1], p_e2e1};
    logic wedge_ovf;
    assign wedge_ovf = ovf_e1e2 || ovf_e2e1 || (wedge_ext[WIDTH] != wedge_ext[WIDTH-1]);

    // Norm squared of vector a: a_e1^2 + a_e2^2
    logic signed [WIDTH-1:0] p_a1a1, p_a2a2;
    logic                    ovf_a1a1, ovf_a2a2;
    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul_norm1 (
        .a(a_e1), .b(a_e1), .prod(p_a1a1), .mul_overflow(ovf_a1a1),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );
    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_mul_norm2 (
        .a(a_e2), .b(a_e2), .prod(p_a2a2), .mul_overflow(ovf_a2a2),
        .sum(), .add_overflow(), .diff(), .sub_overflow(), .eq(), .lt(), .gt()
    );
    logic signed [WIDTH:0] norm_ext;
    assign norm_ext = {p_a1a1[WIDTH-1], p_a1a1} + {p_a2a2[WIDTH-1], p_a2a2};
    logic norm_ovf;
    assign norm_ovf = ovf_a1a1 || ovf_a2a2 || (norm_ext[WIDTH] != norm_ext[WIDTH-1]);

    // Commutator: (AB - BA)/2
    // Anticommutator: (AB + BA)/2
    logic signed [WIDTH:0] diff_s, diff_e1, diff_e2, diff_e12;
    logic signed [WIDTH:0] sum_s, sum_e1, sum_e2, sum_e12;

    assign diff_s   = {ab_s[WIDTH-1], ab_s}     - {ba_s[WIDTH-1], ba_s};
    assign diff_e1  = {ab_e1[WIDTH-1], ab_e1}   - {ba_e1[WIDTH-1], ba_e1};
    assign diff_e2  = {ab_e2[WIDTH-1], ab_e2}   - {ba_e2[WIDTH-1], ba_e2};
    assign diff_e12 = {ab_e12[WIDTH-1], ab_e12} - {ba_e12[WIDTH-1], ba_e12};

    assign sum_s    = {ab_s[WIDTH-1], ab_s}     + {ba_s[WIDTH-1], ba_s};
    assign sum_e1   = {ab_e1[WIDTH-1], ab_e1}   + {ba_e1[WIDTH-1], ba_e1};
    assign sum_e2   = {ab_e2[WIDTH-1], ab_e2}   + {ba_e2[WIDTH-1], ba_e2};
    assign sum_e12  = {ab_e12[WIDTH-1], ab_e12} + {ba_e12[WIDTH-1], ba_e12};

    logic signed [WIDTH-1:0] comm_s, comm_e1, comm_e2, comm_e12;
    assign comm_s   = diff_s[WIDTH:1];
    assign comm_e1  = diff_e1[WIDTH:1];
    assign comm_e2  = diff_e2[WIDTH:1];
    assign comm_e12 = diff_e12[WIDTH:1];

    logic signed [WIDTH-1:0] acomm_s, acomm_e1, acomm_e2, acomm_e12;
    assign acomm_s   = sum_s[WIDTH:1];
    assign acomm_e1  = sum_e1[WIDTH:1];
    assign acomm_e2  = sum_e2[WIDTH:1];
    assign acomm_e12 = sum_e12[WIDTH:1];

    always @* begin
        out_s    = '0;
        out_e1   = '0;
        out_e2   = '0;
        out_e12  = '0;
        overflow = 1'b0;

        case (op_sel)
            3'd0: begin // Vector Dot -> scalar
                out_s    = dot_ovf ? '0 : dot_ext[WIDTH-1:0];
                overflow = dot_ovf;
            end
            3'd1: begin // Vector Wedge -> bivector e12
                out_e12  = wedge_ovf ? '0 : wedge_ext[WIDTH-1:0];
                overflow = wedge_ovf;
            end
            3'd2: begin // Commutator: (AB - BA)/2
                out_s    = comm_s;
                out_e1   = comm_e1;
                out_e2   = comm_e2;
                out_e12  = comm_e12;
                overflow = ab_ovf || ba_ovf;
            end
            3'd3: begin // Anticommutator: (AB + BA)/2
                out_s    = acomm_s;
                out_e1   = acomm_e1;
                out_e2   = acomm_e2;
                out_e12  = acomm_e12;
                overflow = ab_ovf || ba_ovf;
            end
            3'd4: begin // Norm Squared -> scalar
                out_s    = norm_ovf ? '0 : norm_ext[WIDTH-1:0];
                overflow = norm_ovf;
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

`endif // GEO_BILINEAR_OPS_SV
