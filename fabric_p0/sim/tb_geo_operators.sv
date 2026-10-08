// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_geo_operators
// P0.1 Primitive Equivalence & Operator Qualification Testbench

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_geo_operators;

    parameter int WIDTH = 32;
    parameter int FRAC  = 16;

    localparam logic signed [WIDTH-1:0] ONE       = (1 << FRAC);
    localparam logic signed [WIDTH-1:0] TWO       = (FRAC <= 24) ? (2 << FRAC) : (1 << FRAC);
    localparam logic signed [WIDTH-1:0] HALF      = (1 << (FRAC - 1));
    localparam logic signed [WIDTH-1:0] TEST_VAL  = (FRAC <= 24) ? (2 << FRAC) : (1 << (FRAC - 1));
    localparam logic signed [WIDTH-1:0] MAX_FIXED = {1'b0, {(WIDTH-1){1'b1}}};
    localparam logic signed [WIDTH-1:0] MIN_FIXED = {1'b1, {(WIDTH-1){1'b0}}};

    logic              clk;
    logic              reset_n;
    logic              start;
    geo_opcode_t       opcode;
    cl20_mv_t          op_a;
    cl20_mv_t          op_b;
    logic              done;
    cl20_mv_t          result;
    logic              overflow;
    logic              cmp_res;

    cl20_mv_t          phi_A, phi_B, phi_AB;

`ifndef SYNTHESIS
    geo_operator_unit #(
        .WIDTH(WIDTH),
        .FRAC(FRAC)
    ) dut (
`else
    geo_operator_unit dut (
`endif
        .clk(clk),
        .reset_n(reset_n),
        .start(start),
        .opcode(opcode),
        .operand_a(op_a),
        .operand_b(op_b),
        .done(done),
        .result(result),
        .overflow(overflow),
        .comparison_result(cmp_res)
    );

    // Clock generator: 100 MHz (10ns period)
    always #5 clk = ~clk;

    task clear_operands();
        begin
            op_a.s   = '0; op_a.e1  = '0; op_a.e2  = '0; op_a.e12 = '0;
            op_b.s   = '0; op_b.e1  = '0; op_b.e2  = '0; op_b.e12 = '0;
        end
    endtask

    task exec_op(input geo_opcode_t op);
        begin
            @(negedge clk);
            opcode = op;
            start  = 1'b1;
            @(negedge clk);
            start  = 1'b0;
            while (!done) @(negedge clk);
        end
    endtask

    initial begin
        clk = 0;
        reset_n = 0;
        start = 0;
        clear_operands();
        #20 reset_n = 1;
        #10;

        $display("=== P0.1: BEGIN GEO OPERATOR QUALIFICATION (WIDTH=%0d, FRAC=%0d) ===", WIDTH, FRAC);

        // --- 1. Basic Fixed-point Arithmetic ---
        if (FRAC <= 24) begin
            clear_operands();
            op_a.s = ONE; op_b.s = TWO;
            exec_op(OP_ADD);
            if (overflow || result.s !== (3 << FRAC)) $fatal(1, "ADD failed: %0d != %0d", result.s, (3 << FRAC));

            clear_operands();
            op_a.s = TWO; op_b.s = ONE;
            exec_op(OP_SUB);
            if (overflow || result.s !== ONE) $fatal(1, "SUB failed: %0d != %0d", result.s, ONE);

            clear_operands();
            op_a.s = TWO; op_b.s = HALF;
            exec_op(OP_MUL);
            if (overflow || result.s !== ONE) $fatal(1, "MUL failed: %0d != %0d", result.s, ONE);
        end else begin
            clear_operands();
            op_a.s = ONE; op_b.s = HALF;
            exec_op(OP_ADD);
            if (overflow || result.s !== (ONE + HALF)) $fatal(1, "ADD failed: %0d != %0d", result.s, (ONE + HALF));

            clear_operands();
            op_a.s = ONE; op_b.s = HALF;
            exec_op(OP_SUB);
            if (overflow || result.s !== HALF) $fatal(1, "SUB failed: %0d != %0d", result.s, HALF);

            clear_operands();
            op_a.s = ONE; op_b.s = HALF;
            exec_op(OP_MUL);
            if (overflow || result.s !== HALF) $fatal(1, "MUL failed: %0d != %0d", result.s, HALF);
        end

        clear_operands();
        op_a.s = ONE; op_b.s = ONE;
        exec_op(OP_COMPARE);
        if (!cmp_res || result.s !== ONE) $fatal(1, "COMPARE equality failed");

        // --- 2. Cl(2,0) Geometric Product & Basis Algebra ---
        // Basis: e1 * e2 = e12
        clear_operands();
        op_a.e1 = ONE; op_b.e2 = ONE;
        exec_op(OP_CL20_PRODUCT);
        if (overflow || result.e12 !== ONE || result.s !== 0 || result.e1 !== 0 || result.e2 !== 0)
            $fatal(1, "CL20: e1 * e2 != e12");

        // Basis: e2 * e1 = -e12
        clear_operands();
        op_a.e2 = ONE; op_b.e1 = ONE;
        exec_op(OP_CL20_PRODUCT);
        if (overflow || result.e12 !== -ONE || result.s !== 0 || result.e1 !== 0 || result.e2 !== 0)
            $fatal(1, "CL20: e2 * e1 != -e12");

        // Basis: e1 * e1 = +1
        clear_operands();
        op_a.e1 = ONE; op_b.e1 = ONE;
        exec_op(OP_CL20_PRODUCT);
        if (overflow || result.s !== ONE || result.e1 !== 0 || result.e2 !== 0 || result.e12 !== 0)
            $fatal(1, "CL20: e1 * e1 != 1");

        // Basis: e2 * e2 = +1
        clear_operands();
        op_a.e2 = ONE; op_b.e2 = ONE;
        exec_op(OP_CL20_PRODUCT);
        if (overflow || result.s !== ONE || result.e1 !== 0 || result.e2 !== 0 || result.e12 !== 0)
            $fatal(1, "CL20: e2 * e2 != 1");

        // Basis: e12 * e12 = -1
        clear_operands();
        op_a.e12 = ONE; op_b.e12 = ONE;
        exec_op(OP_CL20_PRODUCT);
        if (overflow || result.s !== -ONE || result.e1 !== 0 || result.e2 !== 0 || result.e12 !== 0)
            $fatal(1, "CL20: e12 * e12 != -1");

        // Mixed multivector product: (1 + 2*e1) * (3 + 4*e2)
        // = 3 + 4*e2 + 6*e1 + 8*e12
        if (FRAC <= 24) begin
            clear_operands();
            op_a.s  = ONE; op_a.e1 = TWO;
            op_b.s  = (3 << FRAC); op_b.e2 = (4 << FRAC);
            exec_op(OP_CL20_PRODUCT);
            if (overflow ||
                result.s   !== (3 << FRAC) ||
                result.e1  !== (6 << FRAC) ||
                result.e2  !== (4 << FRAC) ||
                result.e12 !== (8 << FRAC))
                $fatal(1, "CL20 mixed product failed");
        end else begin
            clear_operands();
            op_a.s  = HALF; op_a.e1 = HALF;
            op_b.s  = HALF; op_b.e2 = HALF;
            exec_op(OP_CL20_PRODUCT);
            // (0.5 + 0.5*e1) * (0.5 + 0.5*e2) = 0.25 + 0.25*e2 + 0.25*e1 + 0.25*e12
            if (overflow ||
                result.s   !== (1 << (FRAC-2)) ||
                result.e1  !== (1 << (FRAC-2)) ||
                result.e2  !== (1 << (FRAC-2)) ||
                result.e12 !== (1 << (FRAC-2)))
                $fatal(1, "CL20 mixed product Q1.30 failed");
        end

        // --- 3. Involutions ---
        // Reverse: (s, e1, e2, -e12)
        clear_operands();
        op_a.s = ONE; op_a.e1 = TEST_VAL; op_a.e2 = -ONE; op_a.e12 = HALF;
        exec_op(OP_REVERSE);
        if (overflow || result.s !== ONE || result.e1 !== TEST_VAL || result.e2 !== -ONE || result.e12 !== -HALF)
            $fatal(1, "REVERSE failed");

        // Grade Involution: (s, -e1, -e2, e12)
        clear_operands();
        op_a.s = ONE; op_a.e1 = TEST_VAL; op_a.e2 = -ONE; op_a.e12 = HALF;
        exec_op(OP_GRADE_INVOLUTION);
        if (overflow || result.s !== ONE || result.e1 !== -TEST_VAL || result.e2 !== ONE || result.e12 !== HALF)
            $fatal(1, "GRADE_INVOLUTION failed");

        // Clifford Conjugation: (s, -e1, -e2, -e12)
        clear_operands();
        op_a.s = ONE; op_a.e1 = TEST_VAL; op_a.e2 = -ONE; op_a.e12 = HALF;
        exec_op(OP_CLIFFORD_CONJUGATE);
        if (overflow || result.s !== ONE || result.e1 !== -TEST_VAL || result.e2 !== ONE || result.e12 !== -HALF)
            $fatal(1, "CLIFFORD_CONJUGATE failed");

        // --- 4. Grade Projections ---
        clear_operands();
        op_a.s = ONE; op_a.e1 = TEST_VAL; op_a.e2 = -ONE; op_a.e12 = HALF;
        exec_op(OP_SCALAR_PROJECTION);
        if (result.s !== ONE || result.e1 !== 0 || result.e2 !== 0 || result.e12 !== 0)
            $fatal(1, "SCALAR_PROJECTION failed");

        exec_op(OP_VECTOR_PROJECTION);
        if (result.s !== 0 || result.e1 !== TEST_VAL || result.e2 !== -ONE || result.e12 !== 0)
            $fatal(1, "VECTOR_PROJECTION failed");

        exec_op(OP_BIVECTOR_PROJECTION);
        if (result.s !== 0 || result.e1 !== 0 || result.e2 !== 0 || result.e12 !== HALF)
            $fatal(1, "BIVECTOR_PROJECTION failed");

        // --- 5. Bilinear Ops: Dot, Wedge, Commutator, Anticommutator, Norm2 ---
        if (FRAC <= 24) begin
            // Dot: (e1 + 2*e2) . (3*e1 + 4*e2) = 1*3 + 2*4 = 11
            clear_operands();
            op_a.e1 = ONE; op_a.e2 = TWO;
            op_b.e1 = (3 << FRAC); op_b.e2 = (4 << FRAC);
            exec_op(OP_VECTOR_DOT);
            if (overflow || result.s !== (11 << FRAC))
                $fatal(1, "VECTOR_DOT failed: %0d != %0d", result.s, (11 << FRAC));

            // Wedge: (e1 + 2*e2) ^ (3*e1 + 4*e2) = (1*4 - 2*3) e12 = -2 e12
            clear_operands();
            op_a.e1 = ONE; op_a.e2 = TWO;
            op_b.e1 = (3 << FRAC); op_b.e2 = (4 << FRAC);
            exec_op(OP_VECTOR_WEDGE);
            if (overflow || result.e12 !== -(2 << FRAC))
                $fatal(1, "VECTOR_WEDGE failed: %0d != %0d", result.e12, -(2 << FRAC));
        end else begin
            clear_operands();
            op_a.e1 = ONE; op_a.e2 = HALF;
            op_b.e1 = HALF; op_b.e2 = ONE;
            exec_op(OP_VECTOR_DOT);
            if (overflow || result.s !== ONE)
                $fatal(1, "VECTOR_DOT Q1.30 failed: %0d != %0d", result.s, ONE);

            clear_operands();
            op_a.e1 = ONE; op_a.e2 = HALF;
            op_b.e1 = HALF; op_b.e2 = ONE;
            exec_op(OP_VECTOR_WEDGE);
            if (overflow || result.e12 !== (3 << (FRAC-2)))
                $fatal(1, "VECTOR_WEDGE Q1.30 failed: %0d != %0d", result.e12, (3 << (FRAC-2)));
        end

        // Commutator: [e1, e2] = (e1*e2 - e2*e1)/2 = (e12 - (-e12))/2 = e12
        clear_operands();
        op_a.e1 = ONE; op_b.e2 = ONE;
        exec_op(OP_COMMUTATOR);
        if (overflow || result.e12 !== ONE || result.s !== 0)
            $fatal(1, "COMMUTATOR [e1, e2] failed: %0d != %0d", result.e12, ONE);

        // Anticommutator: {e1, e1} = (e1^2 + e1^2)/2 = 1
        clear_operands();
        op_a.e1 = ONE; op_b.e1 = ONE;
        exec_op(OP_ANTICOMMUTATOR);
        if (overflow || result.s !== ONE)
            $fatal(1, "ANTICOMMUTATOR {e1, e1} failed: %0d != %0d", result.s, ONE);

        // Norm Squared
        if (FRAC <= 24) begin
            clear_operands();
            op_a.e1 = TWO; op_a.e2 = (3 << FRAC);
            exec_op(OP_NORM_SQUARED);
            if (overflow || result.s !== (13 << FRAC))
                $fatal(1, "NORM_SQUARED failed: %0d != %0d", result.s, (13 << FRAC));
        end else begin
            clear_operands();
            op_a.e1 = ONE; op_a.e2 = 0;
            exec_op(OP_NORM_SQUARED);
            if (overflow || result.s !== ONE)
                $fatal(1, "NORM_SQUARED Q1.30 failed: %0d != %0d", result.s, ONE);
        end

        // --- 6. Matrix Bridge M_2(R) <-> Cl(2,0) ---
        if (FRAC <= 24) begin
            clear_operands();
            op_a.s  = (3 << FRAC); // a
            op_a.e1 = (1 << FRAC); // b
            op_a.e2 = (2 << FRAC); // c
            op_a.e12= (5 << FRAC); // d
            exec_op(OP_MATRIX_TO_CL20);
            if (overflow ||
                result.s   !== (4 << FRAC) ||
                result.e1  !== -(1 << FRAC) ||
                result.e2  !== (3 << (FRAC-1)) || // 1.5
                result.e12 !== -(1 << (FRAC-1)))   // -0.5
                $fatal(1, "MATRIX_TO_CL20 failed");

            // Inverse reconstruction: Cl(2,0) -> M_2(R)
            op_a = result;
            exec_op(OP_CL20_TO_MATRIX);
            if (overflow ||
                result.s   !== (3 << FRAC) ||
                result.e1  !== (1 << FRAC) ||
                result.e2  !== (2 << FRAC) ||
                result.e12 !== (5 << FRAC))
                $fatal(1, "CL20_TO_MATRIX round-trip failed");

            // --- 7. Matrix Bridge Morphism: phi(AB) == phi(A) * phi(B) ---
            clear_operands();
            op_a.s = (1<<FRAC); op_a.e1 = (2<<FRAC); op_a.e2 = 0; op_a.e12 = (1<<FRAC);
            exec_op(OP_MATRIX_TO_CL20);
            phi_A = result;

            clear_operands();
            op_a.s = (2<<FRAC); op_a.e1 = 0; op_a.e2 = (1<<FRAC); op_a.e12 = (3<<FRAC);
            exec_op(OP_MATRIX_TO_CL20);
            phi_B = result;

            clear_operands();
            op_a.s = (4<<FRAC); op_a.e1 = (6<<FRAC); op_a.e2 = (1<<FRAC); op_a.e12 = (3<<FRAC);
            exec_op(OP_MATRIX_TO_CL20);
            phi_AB = result;

            clear_operands();
            op_a = phi_A; op_b = phi_B;
            exec_op(OP_CL20_PRODUCT);
            if (overflow ||
                result.s   !== phi_AB.s  ||
                result.e1  !== phi_AB.e1 ||
                result.e2  !== phi_AB.e2 ||
                result.e12 !== phi_AB.e12)
                $fatal(1, "MATRIX BRIDGE MORPHISM FAILED: phi(AB) != phi(A)*phi(B)");
        end else begin
            clear_operands();
            op_a.s  = ONE;  // a = 1.0
            op_a.e1 = HALF; // b = 0.5
            op_a.e2 = HALF; // c = 0.5
            op_a.e12= ONE;  // d = 1.0
            exec_op(OP_MATRIX_TO_CL20);
            if (overflow ||
                result.s   !== ONE ||
                result.e1  !== 0   ||
                result.e2  !== HALF||
                result.e12 !== 0)
                $fatal(1, "MATRIX_TO_CL20 Q1.30 failed");

            op_a = result;
            exec_op(OP_CL20_TO_MATRIX);
            if (overflow ||
                result.s   !== ONE  ||
                result.e1  !== HALF ||
                result.e2  !== HALF ||
                result.e12 !== ONE)
                $fatal(1, "CL20_TO_MATRIX round-trip Q1.30 failed");

            // Morphism: phi(I * B) = phi(I) * phi(B)
            clear_operands();
            op_a.s = ONE; op_a.e1 = 0; op_a.e2 = 0; op_a.e12 = ONE;
            exec_op(OP_MATRIX_TO_CL20);
            phi_A = result;

            clear_operands();
            op_a.s = HALF; op_a.e1 = HALF; op_a.e2 = 0; op_a.e12 = HALF;
            exec_op(OP_MATRIX_TO_CL20);
            phi_B = result;
            phi_AB = result;

            clear_operands();
            op_a = phi_A; op_b = phi_B;
            exec_op(OP_CL20_PRODUCT);
            if (overflow ||
                result.s   !== phi_AB.s  ||
                result.e1  !== phi_AB.e1 ||
                result.e2  !== phi_AB.e2 ||
                result.e12 !== phi_AB.e12)
                $fatal(1, "MATRIX BRIDGE MORPHISM Q1.30 FAILED: phi(AB) != phi(A)*phi(B)");
        end

        // --- 8. Overflow & Wide Cancellation Hardening ---
        // Multiplication overflow must be signaled and fail closed
        clear_operands();
        op_a.s = MAX_FIXED;
        op_b.s = (FRAC <= 24) ? TWO : (ONE + HALF);
        exec_op(OP_MUL);
        if (!overflow || result.s !== 0) $fatal(1, "Overflow check failed to fail-closed on MUL");

        // Intermediate Cl(2,0) product overflow
        clear_operands();
        op_a.e1 = MAX_FIXED;
        op_b.e1 = (FRAC <= 24) ? TWO : (ONE + HALF);
        exec_op(OP_CL20_PRODUCT);
        if (!overflow || result.s !== 0) $fatal(1, "Overflow check failed to fail-closed on CL20");

        // Wide cancellation: large terms must NOT be falsely rejected
        clear_operands();
        op_a.s   = -ONE;       op_a.e1  = -ONE;       op_a.e2  = -ONE; op_a.e12  = -ONE;
        op_b.s   = -MAX_FIXED; op_b.e1  = -MAX_FIXED; op_b.e2  = 0;    op_b.e12  = -MAX_FIXED;
        exec_op(OP_CL20_PRODUCT);
        if (overflow) $fatal(1, "Wide cancellation falsely flagged overflow");
        if (result.s !== MAX_FIXED || result.e1 !== MAX_FIXED || result.e2 !== MAX_FIXED || result.e12 !== MAX_FIXED)
            $fatal(1, "Wide cancellation produced incorrect result");

        $display("=== P0.1: PASS ALL OPERATOR QUALIFICATION TESTS ===");
        $finish;
    end

endmodule
