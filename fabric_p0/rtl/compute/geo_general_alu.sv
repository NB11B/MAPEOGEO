// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_general_alu
// General Compute Fabric primitive ALU implementing Section 6 bounded computation

`ifndef GEO_GENERAL_ALU_SV
`define GEO_GENERAL_ALU_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_general_alu #(
    parameter int WIDTH = 32,
    parameter int FRAC  = 16
) (
    input  logic              clk,
    input  logic              reset_n,
    input  logic              start,
    input  geo_opcode_t       opcode,
    input  logic [WIDTH-1:0]  op_a,
    input  logic [WIDTH-1:0]  op_b,
    input  logic [WIDTH-1:0]  op_c, // For SELECT or auxiliary operand

    output logic              done,
    output logic [WIDTH-1:0]  result,
    output logic              branch_taken,
    output logic              halt_flag,
    output logic              emit_flag,
    output logic              overflow
);

    logic [WIDTH-1:0] comb_result;
    logic             comb_branch;
    logic             comb_halt;
    logic             comb_emit;
    logic             comb_ovf;

    // Full product for MUL
    logic signed [2*WIDTH-1:0] full_mul;
    assign full_mul = $signed(op_a) * $signed(op_b);

    // Sum and diff with overflow
    logic signed [WIDTH:0] ext_add, ext_sub;
    assign ext_add = {op_a[WIDTH-1], op_a} + {op_b[WIDTH-1], op_b};
    assign ext_sub = {op_a[WIDTH-1], op_a} - {op_b[WIDTH-1], op_b};

    logic add_ovf_wire, sub_ovf_wire, mul_ovf_wire;
    assign add_ovf_wire = (ext_add[WIDTH] != ext_add[WIDTH-1]);
    assign sub_ovf_wire = (ext_sub[WIDTH] != ext_sub[WIDTH-1]);
    assign mul_ovf_wire = (full_mul[2*WIDTH-1:WIDTH] != {(WIDTH){full_mul[WIDTH-1]}});

    logic [4:0] shift_amt;
    logic       shift_dir;
    assign shift_amt = op_b[4:0];
    assign shift_dir = op_b[7];

    logic signed [WIDTH-1:0] shift_right_res;
    logic [WIDTH-1:0]        shift_left_res;
    assign shift_right_res = $signed(op_a) >>> shift_amt;
    assign shift_left_res  = op_a << shift_amt;

    always @* begin
        comb_result = '0;
        comb_branch = 1'b0;
        comb_halt   = 1'b0;
        comb_emit   = 1'b0;
        comb_ovf    = 1'b0;

        case (opcode)
            OP_ALU_LOAD, OP_ALU_MOVE: begin
                comb_result = op_a;
            end
            OP_ALU_STORE: begin
                comb_result = op_a;
            end
            OP_ALU_ADD: begin
                comb_result = ext_add[WIDTH-1:0];
                comb_ovf    = add_ovf_wire;
            end
            OP_ALU_SUB: begin
                comb_result = ext_sub[WIDTH-1:0];
                comb_ovf    = sub_ovf_wire;
            end
            OP_ALU_MUL: begin
                comb_result = full_mul[WIDTH-1:0];
                comb_ovf    = mul_ovf_wire;
            end
            OP_ALU_SHIFT: begin
                comb_result = shift_dir ? shift_right_res : shift_left_res;
            end
            OP_ALU_AND: begin
                comb_result = op_a & op_b;
            end
            OP_ALU_OR: begin
                comb_result = op_a | op_b;
            end
            OP_ALU_XOR: begin
                comb_result = op_a ^ op_b;
            end
            OP_COMPARE: begin
                comb_result = (op_a == op_b) ? {{(WIDTH-1){1'b0}}, 1'b1} : '0;
            end
            OP_ALU_SELECT: begin
                comb_result = (op_a != '0) ? op_b : op_c;
            end
            OP_ALU_BRANCH_IF: begin
                comb_branch = (op_a != '0);
                comb_result = op_b;
            end
            OP_ALU_EMIT: begin
                comb_emit   = 1'b1;
                comb_result = op_a;
            end
            OP_ALU_HALT: begin
                comb_halt   = 1'b1;
                comb_result = op_a;
            end
            default: begin
                comb_result = '0;
            end
        endcase

        if (comb_ovf) begin
            comb_result = '0;
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            done         <= 1'b0;
            result       <= '0;
            branch_taken <= 1'b0;
            halt_flag    <= 1'b0;
            emit_flag    <= 1'b0;
            overflow     <= 1'b0;
        end else begin
            if (start) begin
                done         <= 1'b1;
                result       <= comb_result;
                branch_taken <= comb_branch;
                halt_flag    <= comb_halt;
                emit_flag    <= comb_emit;
                overflow     <= comb_ovf;
            end else begin
                done <= 1'b0;
            end
        end
    end

endmodule

`endif // GEO_GENERAL_ALU_SV
