// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_cl20_multivector
// Hardened Cl(2,0) geometric product with intermediate overflow, accumulator overflow, and wide cancellation

`ifndef GEO_CL20_MULTIVECTOR_SV
`define GEO_CL20_MULTIVECTOR_SV

`timescale 1ns/1ps

module geo_cl20_multivector #(
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

    output logic signed [WIDTH-1:0] y_s,
    output logic signed [WIDTH-1:0] y_e1,
    output logic signed [WIDTH-1:0] y_e2,
    output logic signed [WIDTH-1:0] y_e12,
    output logic                    overflow
);

    function automatic logic signed [2*WIDTH:0] round_product(
        input logic signed [2*WIDTH-1:0] product
    );
        logic negative;
        logic [2*WIDTH-1:0] magnitude;
        logic [2*WIDTH-1:0] quotient;
        logic [2*WIDTH-1:0] remainder;
        logic [2*WIDTH-1:0] mask;
        logic [2*WIDTH-1:0] half;
        begin
            negative = product < 0;
            magnitude = negative ? $unsigned(-product) : $unsigned(product);
            mask = ({(2*WIDTH){1'b1}} >> (2*WIDTH-FRAC));
            half = {(2*WIDTH){1'b0}};
            half[FRAC-1] = 1'b1;
            quotient = magnitude >> FRAC;
            remainder = magnitude & mask;
            if (remainder >= half) quotient = quotient + 1'b1;
            round_product = negative ? -$signed({1'b0, quotient}) : $signed({1'b0, quotient});
        end
    endfunction

    function automatic logic rounded_overflow(
        input logic signed [2*WIDTH:0] value
    );
        begin
            rounded_overflow = (value[2*WIDTH:WIDTH] != {(WIDTH+1){value[WIDTH-1]}});
        end
    endfunction

    function automatic logic accumulated_overflow(
        input logic signed [WIDTH+2:0] value
    );
        begin
            accumulated_overflow = (value[WIDTH+2:WIDTH] != {3{value[WIDTH-1]}});
        end
    endfunction

    // 16 elementary product pairs
    logic signed [2*WIDTH-1:0] p00, p11, p22, p33;
    logic signed [2*WIDTH-1:0] p01, p10, p23, p32;
    logic signed [2*WIDTH-1:0] p02, p20, p13, p31;
    logic signed [2*WIDTH-1:0] p03, p30, p12, p21;

    assign p00 = a_s   * b_s;
    assign p11 = a_e1  * b_e1;
    assign p22 = a_e2  * b_e2;
    assign p33 = a_e12 * b_e12;

    assign p01 = a_s   * b_e1;
    assign p10 = a_e1  * b_s;
    assign p23 = a_e2  * b_e12;
    assign p32 = a_e12 * b_e2;

    assign p02 = a_s   * b_e2;
    assign p20 = a_e2  * b_s;
    assign p13 = a_e1  * b_e12;
    assign p31 = a_e12 * b_e1;

    assign p03 = a_s   * b_e12;
    assign p30 = a_e12 * b_s;
    assign p12 = a_e1  * b_e2;
    assign p21 = a_e2  * b_e1;

    // Rounded product representations
    logic signed [2*WIDTH:0] q00, q11, q22, q33;
    logic signed [2*WIDTH:0] q01, q10, q23, q32;
    logic signed [2*WIDTH:0] q02, q20, q13, q31;
    logic signed [2*WIDTH:0] q03, q30, q12, q21;

    assign q00 = round_product(p00);
    assign q11 = round_product(p11);
    assign q22 = round_product(p22);
    assign q33 = round_product(p33);

    assign q01 = round_product(p01);
    assign q10 = round_product(p10);
    assign q23 = round_product(p23);
    assign q32 = round_product(p32);

    assign q02 = round_product(p02);
    assign q20 = round_product(p20);
    assign q13 = round_product(p13);
    assign q31 = round_product(p31);

    assign q03 = round_product(p03);
    assign q30 = round_product(p30);
    assign q12 = round_product(p12);
    assign q21 = round_product(p21);

    // Truncated to WIDTH
    logic signed [WIDTH-1:0] n00, n11, n22, n33;
    logic signed [WIDTH-1:0] n01, n10, n23, n32;
    logic signed [WIDTH-1:0] n02, n20, n13, n31;
    logic signed [WIDTH-1:0] n03, n30, n12, n21;

    assign n00 = q00[WIDTH-1:0];
    assign n11 = q11[WIDTH-1:0];
    assign n22 = q22[WIDTH-1:0];
    assign n33 = q33[WIDTH-1:0];

    assign n01 = q01[WIDTH-1:0];
    assign n10 = q10[WIDTH-1:0];
    assign n23 = q23[WIDTH-1:0];
    assign n32 = q32[WIDTH-1:0];

    assign n02 = q02[WIDTH-1:0];
    assign n20 = q20[WIDTH-1:0];
    assign n13 = q13[WIDTH-1:0];
    assign n31 = q31[WIDTH-1:0];

    assign n03 = q03[WIDTH-1:0];
    assign n30 = q30[WIDTH-1:0];
    assign n12 = q12[WIDTH-1:0];
    assign n21 = q21[WIDTH-1:0];

    // Sign-extended for wide accumulator
    logic signed [WIDTH+2:0] x00, x11, x22, x33;
    logic signed [WIDTH+2:0] x01, x10, x23, x32;
    logic signed [WIDTH+2:0] x02, x20, x13, x31;
    logic signed [WIDTH+2:0] x03, x30, x12, x21;

    assign x00 = {{3{n00[WIDTH-1]}}, n00};
    assign x11 = {{3{n11[WIDTH-1]}}, n11};
    assign x22 = {{3{n22[WIDTH-1]}}, n22};
    assign x33 = {{3{n33[WIDTH-1]}}, n33};

    assign x01 = {{3{n01[WIDTH-1]}}, n01};
    assign x10 = {{3{n10[WIDTH-1]}}, n10};
    assign x23 = {{3{n23[WIDTH-1]}}, n23};
    assign x32 = {{3{n32[WIDTH-1]}}, n32};

    assign x02 = {{3{n02[WIDTH-1]}}, n02};
    assign x20 = {{3{n20[WIDTH-1]}}, n20};
    assign x13 = {{3{n13[WIDTH-1]}}, n13};
    assign x31 = {{3{n31[WIDTH-1]}}, n31};

    assign x03 = {{3{n03[WIDTH-1]}}, n03};
    assign x30 = {{3{n30[WIDTH-1]}}, n30};
    assign x12 = {{3{n12[WIDTH-1]}}, n12};
    assign x21 = {{3{n21[WIDTH-1]}}, n21};

    // Product overflow check
    logic product_overflow;
    assign product_overflow =
        rounded_overflow(q00) || rounded_overflow(q11) || rounded_overflow(q22) || rounded_overflow(q33) ||
        rounded_overflow(q01) || rounded_overflow(q10) || rounded_overflow(q23) || rounded_overflow(q32) ||
        rounded_overflow(q02) || rounded_overflow(q20) || rounded_overflow(q13) || rounded_overflow(q31) ||
        rounded_overflow(q03) || rounded_overflow(q30) || rounded_overflow(q12) || rounded_overflow(q21);

    // Summation along Clifford basis e_s, e_1, e_2, e_12
    logic signed [WIDTH+2:0] sum_s;
    logic signed [WIDTH+2:0] sum_e1;
    logic signed [WIDTH+2:0] sum_e2;
    logic signed [WIDTH+2:0] sum_e12;

    assign sum_s   = x00 + x11 + x22 - x33;
    assign sum_e1  = x01 + x10 - x23 + x32;
    assign sum_e2  = x02 + x20 + x13 - x31;
    assign sum_e12 = x03 + x30 + x12 - x21;

    logic final_overflow;
    assign final_overflow = accumulated_overflow(sum_s)  ||
                            accumulated_overflow(sum_e1) ||
                            accumulated_overflow(sum_e2) ||
                            accumulated_overflow(sum_e12);

    assign overflow = product_overflow || final_overflow;

    // Fail-closed outputs: zero if overflow
    assign y_s   = overflow ? '0 : sum_s[WIDTH-1:0];
    assign y_e1  = overflow ? '0 : sum_e1[WIDTH-1:0];
    assign y_e2  = overflow ? '0 : sum_e2[WIDTH-1:0];
    assign y_e12 = overflow ? '0 : sum_e12[WIDTH-1:0];

endmodule

`endif // GEO_CL20_MULTIVECTOR_SV
