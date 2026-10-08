// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_fixed_arith
// Parameterized fixed-point arithmetic with hardened rounding and explicit fail-closed overflow detection

`ifndef GEO_FIXED_ARITH_SV
`define GEO_FIXED_ARITH_SV

`timescale 1ns/1ps

module geo_fixed_arith #(
    parameter int WIDTH = 32,
    parameter int FRAC  = 16
) (
    input  logic signed [WIDTH-1:0] a,
    input  logic signed [WIDTH-1:0] b,
    
    // Outputs
    output logic signed [WIDTH-1:0] sum,
    output logic                    add_overflow,
    
    output logic signed [WIDTH-1:0] diff,
    output logic                    sub_overflow,
    
    output logic signed [WIDTH-1:0] prod,
    output logic                    mul_overflow,
    
    output logic                    eq,
    output logic                    lt,
    output logic                    gt
);

    // --- Addition ---
    logic signed [WIDTH:0] ext_sum;
    assign ext_sum = {a[WIDTH-1], a} + {b[WIDTH-1], b};
    assign add_overflow = (ext_sum[WIDTH] != ext_sum[WIDTH-1]);
    assign sum = add_overflow ? '0 : ext_sum[WIDTH-1:0];

    // --- Subtraction ---
    logic signed [WIDTH:0] ext_diff;
    assign ext_diff = {a[WIDTH-1], a} - {b[WIDTH-1], b};
    assign sub_overflow = (ext_diff[WIDTH] != ext_diff[WIDTH-1]);
    assign diff = sub_overflow ? '0 : ext_diff[WIDTH-1:0];

    // --- Multiplication with Hardened Symmetric Rounding ---
    logic signed [2*WIDTH-1:0] full_prod;
    assign full_prod = a * b;

    function automatic logic signed [2*WIDTH:0] round_product(
        input logic signed [2*WIDTH-1:0] p
    );
        logic negative;
        logic [2*WIDTH-1:0] magnitude;
        logic [2*WIDTH-1:0] quotient;
        logic [2*WIDTH-1:0] remainder;
        logic [2*WIDTH-1:0] mask;
        logic [2*WIDTH-1:0] half;
        begin
            negative = p < 0;
            magnitude = negative ? $unsigned(-p) : $unsigned(p);
            mask = ({(2*WIDTH){1'b1}} >> (2*WIDTH - FRAC));
            half = {(2*WIDTH){1'b0}};
            half[FRAC-1] = 1'b1;
            quotient = magnitude >> FRAC;
            remainder = magnitude & mask;
            if (remainder >= half) quotient = quotient + 1'b1;
            round_product = negative ? -$signed({1'b0, quotient}) : $signed({1'b0, quotient});
        end
    endfunction

    logic signed [2*WIDTH:0] rounded_prod;
    assign rounded_prod = round_product(full_prod);

    // Overflow check on rounded product
    assign mul_overflow = (rounded_prod[2*WIDTH:WIDTH] != {(WIDTH+1){rounded_prod[WIDTH-1]}});
    assign prod = mul_overflow ? '0 : rounded_prod[WIDTH-1:0];

    // --- Comparisons ---
    assign eq = (a == b);
    assign lt = (a < b);
    assign gt = (a > b);

endmodule

`endif // GEO_FIXED_ARITH_SV
