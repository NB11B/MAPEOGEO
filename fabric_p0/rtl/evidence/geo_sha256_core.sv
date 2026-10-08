// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_sha256_core
// Standards-Conformant FIPS 180-4 SHA-256 Iterative Compression Engine

`ifndef GEO_SHA256_CORE_SV
`define GEO_SHA256_CORE_SV

`timescale 1ns/1ps

module geo_sha256_core (
    input  logic         clk,
    input  logic         rst_n,

    // Control & Initialization
    input  logic         start,          // Pulse to start block processing
    input  logic         init_state,     // 1: Load NIST standard IV; 0: Use state_in
    input  logic [255:0] state_in,       // Chained state (H0..H7) if init_state == 0
    input  logic [511:0] block_in,       // 512-bit message block (big-endian)

    // Status & Result
    output logic         busy,
    output logic         done,           // 1-cycle pulse when compression complete
    output logic [255:0] digest_out      // Resulting 256-bit state {H0, H1, ..., H7}
);

    // NIST FIPS 180-4 Initial Hash Values (H0 .. H7)
    localparam logic [31:0] H0_INIT = 32'h6a09e667;
    localparam logic [31:0] H1_INIT = 32'hbb67ae85;
    localparam logic [31:0] H2_INIT = 32'h3c6ef372;
    localparam logic [31:0] H3_INIT = 32'ha54ff53a;
    localparam logic [31:0] H4_INIT = 32'h510e527f;
    localparam logic [31:0] H5_INIT = 32'h9b05688c;
    localparam logic [31:0] H6_INIT = 32'h1f83d9ab;
    localparam logic [31:0] H7_INIT = 32'h5be0cd19;

    // 64 Round Constants K[0..63]
    function automatic logic [31:0] get_k(input logic [5:0] round_idx);
        case (round_idx)
            6'd00: get_k = 32'h428a2f98; 6'd01: get_k = 32'h71374491;
            6'd02: get_k = 32'hb5c0fbcf; 6'd03: get_k = 32'he9b5dba5;
            6'd04: get_k = 32'h3956c25b; 6'd05: get_k = 32'h59f111f1;
            6'd06: get_k = 32'h923f82a4; 6'd07: get_k = 32'hab1c5ed5;
            6'd08: get_k = 32'hd807aa98; 6'd09: get_k = 32'h12835b01;
            6'd10: get_k = 32'h243185be; 6'd11: get_k = 32'h550c7dc3;
            6'd12: get_k = 32'h72be5d74; 6'd13: get_k = 32'h80deb1fe;
            6'd14: get_k = 32'h9bdc06a7; 6'd15: get_k = 32'hc19bf174;
            6'd16: get_k = 32'he49b69c1; 6'd17: get_k = 32'hefbe4786;
            6'd18: get_k = 32'h0fc19dc6; 6'd19: get_k = 32'h240ca1cc;
            6'd20: get_k = 32'h2de92c6f; 6'd21: get_k = 32'h4a7484aa;
            6'd22: get_k = 32'h5cb0a9dc; 6'd23: get_k = 32'h76f988da;
            6'd24: get_k = 32'h983e5152; 6'd25: get_k = 32'ha831c66d;
            6'd26: get_k = 32'hb00327c8; 6'd27: get_k = 32'hbf597fc7;
            6'd28: get_k = 32'hc6e00bf3; 6'd29: get_k = 32'hd5a79147;
            6'd30: get_k = 32'h06ca6351; 6'd31: get_k = 32'h14292967;
            6'd32: get_k = 32'h27b70a85; 6'd33: get_k = 32'h2e1b2138;
            6'd34: get_k = 32'h4d2c6dfc; 6'd35: get_k = 32'h53380d13;
            6'd36: get_k = 32'h650a7354; 6'd37: get_k = 32'h766a0abb;
            6'd38: get_k = 32'h81c2c92e; 6'd39: get_k = 32'h92722c85;
            6'd40: get_k = 32'ha2bfe8a1; 6'd41: get_k = 32'ha81a664b;
            6'd42: get_k = 32'hc24b8b70; 6'd43: get_k = 32'hc76c51a3;
            6'd44: get_k = 32'hd192e819; 6'd45: get_k = 32'hd6990624;
            6'd46: get_k = 32'hf40e3585; 6'd47: get_k = 32'h106aa070;
            6'd48: get_k = 32'h19a4c116; 6'd49: get_k = 32'h1e376c08;
            6'd50: get_k = 32'h2748774c; 6'd51: get_k = 32'h34b0bcb5;
            6'd52: get_k = 32'h391c0cb3; 6'd53: get_k = 32'h4ed8aa4a;
            6'd54: get_k = 32'h5b9cca4f; 6'd55: get_k = 32'h682e6ff3;
            6'd56: get_k = 32'h748f82ee; 6'd57: get_k = 32'h78a5636f;
            6'd58: get_k = 32'h84c87814; 6'd59: get_k = 32'h8cc70208;
            6'd60: get_k = 32'h90befffa; 6'd61: get_k = 32'ha4506ceb;
            6'd62: get_k = 32'hbef9a3f7; 6'd63: get_k = 32'hc67178f2;
        endcase
    endfunction

    // SHA-256 Bitwise Functions
    function automatic logic [31:0] rotr(input logic [31:0] x, input logic [31:0] n);
        rotr = (x >> n) | (x << (32 - n));
    endfunction

    function automatic logic [31:0] sigma0(input logic [31:0] x);
        sigma0 = rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3);
    endfunction

    function automatic logic [31:0] sigma1(input logic [31:0] x);
        sigma1 = rotr(x, 17) ^ rotr(x, 19) ^ (x >> 10);
    endfunction

    function automatic logic [31:0] cap_sigma0(input logic [31:0] x);
        cap_sigma0 = rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22);
    endfunction

    function automatic logic [31:0] cap_sigma1(input logic [31:0] x);
        cap_sigma1 = rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25);
    endfunction

    function automatic logic [31:0] ch(input logic [31:0] x, input logic [31:0] y, input logic [31:0] z);
        ch = (x & y) ^ (~x & z);
    endfunction

    function automatic logic [31:0] maj(input logic [31:0] x, input logic [31:0] y, input logic [31:0] z);
        maj = (x & y) ^ (x & z) ^ (y & z);
    endfunction

    // Internal State Registers
    typedef enum logic [1:0] {
        ST_IDLE     = 2'd0,
        ST_COMPRESS = 2'd1,
        ST_FINALIZE = 2'd2
    } fsm_state_e;

    fsm_state_e state_q;
    logic [5:0]  round_q;

    // Working variables (a .. h)
    logic [31:0] a_q, b_q, c_q, d_q, e_q, f_q, g_q, h_q;

    // Chained hash state registers (H0 .. H7)
    logic [31:0] H0_q, H1_q, H2_q, H3_q, H4_q, H5_q, H6_q, H7_q;

    // 16-word sliding message schedule window W[0..15]
    logic [31:0] w_mem [0:15];

    // Current W_t computation
    logic [31:0] current_w;
    always_comb begin
        if (round_q < 6'd16) begin
            // First 16 words directly extracted from 512-bit block (big-endian 32-bit words)
            current_w = block_in[(15 - round_q)*32 +: 32];
        end else begin
            // Schedule recurrence: W_t = sigma1(W_{t-2}) + W_{t-7} + sigma0(W_{t-15}) + W_{t-16}
            current_w = sigma1(w_mem[(round_q - 2) & 4'hF]) +
                        w_mem[(round_q - 7) & 4'hF] +
                        sigma0(w_mem[(round_q - 15) & 4'hF]) +
                        w_mem[(round_q - 16) & 4'hF];
        end
    end

    // Compression step combinational calculation
    logic [31:0] t1, t2;
    always_comb begin
        t1 = h_q + cap_sigma1(e_q) + ch(e_q, f_q, g_q) + get_k(round_q) + current_w;
        t2 = cap_sigma0(a_q) + maj(a_q, b_q, c_q);
    end

    assign busy = (state_q != ST_IDLE);
    assign digest_out = {H0_q, H1_q, H2_q, H3_q, H4_q, H5_q, H6_q, H7_q};

    // Sequential Engine
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q    <= ST_IDLE;
            round_q    <= '0;
            done       <= 1'b0;
            a_q        <= '0; b_q <= '0; c_q <= '0; d_q <= '0;
            e_q        <= '0; f_q <= '0; g_q <= '0; h_q <= '0;
            H0_q       <= H0_INIT; H1_q <= H1_INIT; H2_q <= H2_INIT; H3_q <= H3_INIT;
            H4_q       <= H4_INIT; H5_q <= H5_INIT; H6_q <= H6_INIT; H7_q <= H7_INIT;
        end else begin
            done <= 1'b0;

            case (state_q)
                ST_IDLE: begin
                    if (start) begin
                        state_q <= ST_COMPRESS;
                        round_q <= 6'd0;

                        // Set/load current hash state
                        if (init_state) begin
                            H0_q <= H0_INIT; H1_q <= H1_INIT; H2_q <= H2_INIT; H3_q <= H3_INIT;
                            H4_q <= H4_INIT; H5_q <= H5_INIT; H6_q <= H6_INIT; H7_q <= H7_INIT;
                            a_q  <= H0_INIT; b_q  <= H1_INIT; c_q  <= H2_INIT; d_q  <= H3_INIT;
                            e_q  <= H4_INIT; f_q  <= H5_INIT; g_q  <= H6_INIT; h_q  <= H7_INIT;
                        end else begin
                            H0_q <= state_in[255:224]; H1_q <= state_in[223:192];
                            H2_q <= state_in[191:160]; H3_q <= state_in[159:128];
                            H4_q <= state_in[127:96];  H5_q <= state_in[95:64];
                            H6_q <= state_in[63:32];   H7_q <= state_in[31:0];
                            a_q  <= state_in[255:224]; b_q  <= state_in[223:192];
                            c_q  <= state_in[191:160]; d_q  <= state_in[159:128];
                            e_q  <= state_in[127:96];  f_q  <= state_in[95:64];
                            g_q  <= state_in[63:32];   h_q  <= state_in[31:0];
                        end
                    end
                end

                ST_COMPRESS: begin
                    // Store current word in message schedule ring buffer
                    w_mem[round_q & 4'hF] <= current_w;

                    // Update working variables
                    h_q <= g_q;
                    g_q <= f_q;
                    f_q <= e_q;
                    e_q <= d_q + t1;
                    d_q <= c_q;
                    c_q <= b_q;
                    b_q <= a_q;
                    a_q <= t1 + t2;

                    if (round_q == 6'd63) begin
                        state_q <= ST_FINALIZE;
                    end else begin
                        round_q <= round_q + 1'b1;
                    end
                end

                ST_FINALIZE: begin
                    // Add accumulated round values into state registers
                    H0_q <= H0_q + a_q;
                    H1_q <= H1_q + b_q;
                    H2_q <= H2_q + c_q;
                    H3_q <= H3_q + d_q;
                    H4_q <= H4_q + e_q;
                    H5_q <= H5_q + f_q;
                    H6_q <= H6_q + g_q;
                    H7_q <= H7_q + h_q;

                    done    <= 1'b1;
                    state_q <= ST_IDLE;
                end
            endcase
        end
    end

endmodule

`endif // GEO_SHA256_CORE_SV
