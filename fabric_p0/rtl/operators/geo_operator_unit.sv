// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_operator_unit
// Unified PSMSL / GEO functional execution unit supporting Section 5 operations

`ifndef GEO_OPERATOR_UNIT_SV
`define GEO_OPERATOR_UNIT_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_operator_unit #(
    parameter int WIDTH = 32,
    parameter int FRAC  = 16
) (
    input  logic              clk,
    input  logic              reset_n,
    input  logic              start,
    input  geo_opcode_t       opcode,
    input  cl20_mv_t          operand_a,
    input  cl20_mv_t          operand_b,

    output logic              done,
    output cl20_mv_t          result,
    output logic              overflow,
    output logic              comparison_result
);

    // --- Sub-module instantiations ---
    // 1. Scalar fixed-point arithmetic on scalar components
    logic signed [WIDTH-1:0] arith_sum, arith_diff, arith_prod;
    logic                    add_ovf, sub_ovf, mul_ovf;
    logic                    cmp_eq, cmp_lt, cmp_gt;

    geo_fixed_arith #(.WIDTH(WIDTH), .FRAC(FRAC)) u_arith (
        .a(operand_a.s),
        .b(operand_b.s),
        .sum(arith_sum),
        .add_overflow(add_ovf),
        .diff(arith_diff),
        .sub_overflow(sub_ovf),
        .prod(arith_prod),
        .mul_overflow(mul_ovf),
        .eq(cmp_eq),
        .lt(cmp_lt),
        .gt(cmp_gt)
    );

    // 2. Multivector addition & subtraction (elementwise)
    logic signed [WIDTH:0] ext_mv_sum_s, ext_mv_sum_e1, ext_mv_sum_e2, ext_mv_sum_e12;
    logic signed [WIDTH:0] ext_mv_sub_s, ext_mv_sub_e1, ext_mv_sub_e2, ext_mv_sub_e12;
    logic mv_add_ovf, mv_sub_ovf;

    assign ext_mv_sum_s   = {operand_a.s[WIDTH-1], operand_a.s}     + {operand_b.s[WIDTH-1], operand_b.s};
    assign ext_mv_sum_e1  = {operand_a.e1[WIDTH-1], operand_a.e1}   + {operand_b.e1[WIDTH-1], operand_b.e1};
    assign ext_mv_sum_e2  = {operand_a.e2[WIDTH-1], operand_a.e2}   + {operand_b.e2[WIDTH-1], operand_b.e2};
    assign ext_mv_sum_e12 = {operand_a.e12[WIDTH-1], operand_a.e12} + {operand_b.e12[WIDTH-1], operand_b.e12};

    assign mv_add_ovf = (ext_mv_sum_s[WIDTH]   != ext_mv_sum_s[WIDTH-1])   ||
                        (ext_mv_sum_e1[WIDTH]  != ext_mv_sum_e1[WIDTH-1])  ||
                        (ext_mv_sum_e2[WIDTH]  != ext_mv_sum_e2[WIDTH-1])  ||
                        (ext_mv_sum_e12[WIDTH] != ext_mv_sum_e12[WIDTH-1]);

    assign ext_mv_sub_s   = {operand_a.s[WIDTH-1], operand_a.s}     - {operand_b.s[WIDTH-1], operand_b.s};
    assign ext_mv_sub_e1  = {operand_a.e1[WIDTH-1], operand_a.e1}   - {operand_b.e1[WIDTH-1], operand_b.e1};
    assign ext_mv_sub_e2  = {operand_a.e2[WIDTH-1], operand_a.e2}   - {operand_b.e2[WIDTH-1], operand_b.e2};
    assign ext_mv_sub_e12 = {operand_a.e12[WIDTH-1], operand_a.e12} - {operand_b.e12[WIDTH-1], operand_b.e12};

    assign mv_sub_ovf = (ext_mv_sub_s[WIDTH]   != ext_mv_sub_s[WIDTH-1])   ||
                        (ext_mv_sub_e1[WIDTH]  != ext_mv_sub_e1[WIDTH-1])  ||
                        (ext_mv_sub_e2[WIDTH]  != ext_mv_sub_e2[WIDTH-1])  ||
                        (ext_mv_sub_e12[WIDTH] != ext_mv_sub_e12[WIDTH-1]);

    logic signed [WIDTH-1:0] sum_s_trunc, sum_e1_trunc, sum_e2_trunc, sum_e12_trunc;
    logic signed [WIDTH-1:0] sub_s_trunc, sub_e1_trunc, sub_e2_trunc, sub_e12_trunc;
    assign sum_s_trunc   = ext_mv_sum_s[WIDTH-1:0];
    assign sum_e1_trunc  = ext_mv_sum_e1[WIDTH-1:0];
    assign sum_e2_trunc  = ext_mv_sum_e2[WIDTH-1:0];
    assign sum_e12_trunc = ext_mv_sum_e12[WIDTH-1:0];
    assign sub_s_trunc   = ext_mv_sub_s[WIDTH-1:0];
    assign sub_e1_trunc  = ext_mv_sub_e1[WIDTH-1:0];
    assign sub_e2_trunc  = ext_mv_sub_e2[WIDTH-1:0];
    assign sub_e12_trunc = ext_mv_sub_e12[WIDTH-1:0];

    // 3. Cl(2,0) Geometric Product
    cl20_mv_t cl20_prod;
    logic     cl20_ovf;
    geo_cl20_multivector #(.WIDTH(WIDTH), .FRAC(FRAC)) u_cl20 (
        .a_s(operand_a.s), .a_e1(operand_a.e1), .a_e2(operand_a.e2), .a_e12(operand_a.e12),
        .b_s(operand_b.s), .b_e1(operand_b.e1), .b_e2(operand_b.e2), .b_e12(operand_b.e12),
        .y_s(cl20_prod.s), .y_e1(cl20_prod.e1), .y_e2(cl20_prod.e2), .y_e12(cl20_prod.e12),
        .overflow(cl20_ovf)
    );

    // 4. Unary operations
    logic [2:0] unary_sel;
    cl20_mv_t   unary_res;
    logic       unary_ovf;

    always @* begin
        case (opcode)
            OP_REVERSE:             unary_sel = 3'd0;
            OP_GRADE_INVOLUTION:    unary_sel = 3'd1;
            OP_CLIFFORD_CONJUGATE:  unary_sel = 3'd2;
            OP_SCALAR_PROJECTION:   unary_sel = 3'd3;
            OP_VECTOR_PROJECTION:   unary_sel = 3'd4;
            OP_BIVECTOR_PROJECTION: unary_sel = 3'd5;
            default:                unary_sel = 3'd0;
        endcase
    end

    geo_unary_ops #(.WIDTH(WIDTH)) u_unary (
        .in_s(operand_a.s), .in_e1(operand_a.e1), .in_e2(operand_a.e2), .in_e12(operand_a.e12),
        .op_sel(unary_sel),
        .out_s(unary_res.s), .out_e1(unary_res.e1), .out_e2(unary_res.e2), .out_e12(unary_res.e12),
        .overflow(unary_ovf)
    );

    // 5. Bilinear operations
    logic [2:0] bilinear_sel;
    cl20_mv_t   bilinear_res;
    logic       bilinear_ovf;

    always @* begin
        case (opcode)
            OP_VECTOR_DOT:     bilinear_sel = 3'd0;
            OP_VECTOR_WEDGE:   bilinear_sel = 3'd1;
            OP_COMMUTATOR:     bilinear_sel = 3'd2;
            OP_ANTICOMMUTATOR: bilinear_sel = 3'd3;
            OP_NORM_SQUARED:   bilinear_sel = 3'd4;
            default:           bilinear_sel = 3'd0;
        endcase
    end

    geo_bilinear_ops #(.WIDTH(WIDTH), .FRAC(FRAC)) u_bilinear (
        .a_s(operand_a.s), .a_e1(operand_a.e1), .a_e2(operand_a.e2), .a_e12(operand_a.e12),
        .b_s(operand_b.s), .b_e1(operand_b.e1), .b_e2(operand_b.e2), .b_e12(operand_b.e12),
        .op_sel(bilinear_sel),
        .out_s(bilinear_res.s), .out_e1(bilinear_res.e1), .out_e2(bilinear_res.e2), .out_e12(bilinear_res.e12),
        .overflow(bilinear_ovf)
    );

    // 6. Matrix bridge
    logic     bridge_dir;
    cl20_mv_t bridge_mv_out;
    mat2_t    bridge_mat_out;
    logic     bridge_ovf;

    assign bridge_dir = (opcode == OP_CL20_TO_MATRIX);

    geo_matrix_bridge #(.WIDTH(WIDTH)) u_bridge (
        .mat_a(operand_a.s), .mat_b(operand_a.e1), .mat_c(operand_a.e2), .mat_d(operand_a.e12),
        .mv_s(operand_a.s),  .mv_e1(operand_a.e1),  .mv_e2(operand_a.e2),  .mv_e12(operand_a.e12),
        .direction(bridge_dir),
        .out_mat_a(bridge_mat_out.a), .out_mat_b(bridge_mat_out.b),
        .out_mat_c(bridge_mat_out.c), .out_mat_d(bridge_mat_out.d),
        .out_mv_s(bridge_mv_out.s),   .out_mv_e1(bridge_mv_out.e1),
        .out_mv_e2(bridge_mv_out.e2), .out_mv_e12(bridge_mv_out.e12),
        .overflow(bridge_ovf)
    );

    // --- Combinational Execution Multiplexer ---
    cl20_mv_t comb_result;
    logic     comb_overflow;
    logic     comb_comparison;

    always @* begin
        comb_result.s     = '0;
        comb_result.e1    = '0;
        comb_result.e2    = '0;
        comb_result.e12   = '0;
        comb_overflow     = 1'b0;
        comb_comparison   = 1'b0;

        case (opcode)
            OP_ADD: begin
                comb_result.s   = sum_s_trunc;
                comb_result.e1  = sum_e1_trunc;
                comb_result.e2  = sum_e2_trunc;
                comb_result.e12 = sum_e12_trunc;
                comb_overflow   = mv_add_ovf;
            end
            OP_SUB: begin
                comb_result.s   = sub_s_trunc;
                comb_result.e1  = sub_e1_trunc;
                comb_result.e2  = sub_e2_trunc;
                comb_result.e12 = sub_e12_trunc;
                comb_overflow   = mv_sub_ovf;
            end
            OP_MUL: begin
                comb_result.s = arith_prod;
                comb_overflow = mul_ovf;
            end
            OP_COMPARE: begin
                comb_comparison = (operand_a == operand_b);
                comb_result.s   = comb_comparison ? (1 << FRAC) : '0;
                comb_overflow   = 1'b0;
            end
            OP_CL20_PRODUCT, OP_COMPOSE: begin
                comb_result   = cl20_prod;
                comb_overflow = cl20_ovf;
            end
            OP_REVERSE, OP_GRADE_INVOLUTION, OP_CLIFFORD_CONJUGATE,
            OP_SCALAR_PROJECTION, OP_VECTOR_PROJECTION, OP_BIVECTOR_PROJECTION: begin
                comb_result   = unary_res;
                comb_overflow = unary_ovf;
            end
            OP_VECTOR_DOT, OP_VECTOR_WEDGE, OP_COMMUTATOR,
            OP_ANTICOMMUTATOR, OP_NORM_SQUARED: begin
                comb_result   = bilinear_res;
                comb_overflow = bilinear_ovf;
            end
            OP_MATRIX_TO_CL20: begin
                comb_result   = bridge_mv_out;
                comb_overflow = bridge_ovf;
            end
            OP_CL20_TO_MATRIX: begin
                comb_result.s   = bridge_mat_out.a;
                comb_result.e1  = bridge_mat_out.b;
                comb_result.e2  = bridge_mat_out.c;
                comb_result.e12 = bridge_mat_out.d;
                comb_overflow   = bridge_ovf;
            end
            default: begin
                comb_result.s   = '0;
                comb_result.e1  = '0;
                comb_result.e2  = '0;
                comb_result.e12 = '0;
                comb_overflow   = 1'b0;
            end
        endcase

        if (comb_overflow) begin
            comb_result.s   = '0;
            comb_result.e1  = '0;
            comb_result.e2  = '0;
            comb_result.e12 = '0;
        end
    end

    // Single-cycle registered completion handshake
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            done              <= 1'b0;
            result.s          <= '0;
            result.e1         <= '0;
            result.e2         <= '0;
            result.e12        <= '0;
            overflow          <= 1'b0;
            comparison_result <= 1'b0;
        end else begin
            if (start) begin
                done              <= 1'b1;
                result            <= comb_result;
                overflow          <= comb_overflow;
                comparison_result <= comb_comparison;
            end else begin
                done <= 1'b0;
            end
        end
    end

endmodule

`endif // GEO_OPERATOR_UNIT_SV
