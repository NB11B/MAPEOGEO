// SPDX-License-Identifier: MIT
// =============================================================================
// Module: geo_psmsl_scorer
// Project: MAPEOGEO fabric_p0 / Track PDI-v0.8
// Description:
//   Synthesizable 4-DSP Bit-Exact PSMSL Candidate Work Scorer (4,225 parameters).
//   Computes inference over 32 INT8 relational features using a 3-layer MLP:
//     Layer 1: 32 -> 64 (ReLU, INT8)
//     Layer 2: 64 -> 32 (ReLU, INT8)
//     Layer 3: 32 -> 1  (Linear, INT32 score)
//
// Hardware Resource Budget:
//   - 4x DSP48E1 MAC units (4 parallel MACs per clock cycle)
//   - 2x 36-Kb Block RAMs for quantized weights and biases
//   - Internal activation scratchpad (64B + 32B distributed RAM)
//   - Execution latency: ~1,040 clock cycles per candidate (~10.4 us @ 100 MHz)
//
// Authority Boundary:
//   - STRICTLY READ-ONLY ARITHMETIC CO-PROCESSOR.
//   - ZERO write ports, zero address buses, and zero strobes connected to
//     authoritative state memory (geo_state_memory.sv).
// =============================================================================

`timescale 1ns / 1ps

module geo_psmsl_scorer #(
    parameter MEM_DIR = "fabric_p0/rtl/scorer/"
)(
    input  wire        clk,
    input  wire        rst_n,

    // Command / Dispatch Interface
    input  wire        start,
    input  wire [3:0]  cand_id_in,
    input  wire [255:0] features_in_bus,  // 32 INT8 relational features (packed 256-bit bus)

    // Status / Result Interface
    output reg         busy,
    output reg         done,
    output reg  [3:0]  cand_id_out,
    output reg  signed [31:0] score_out
);

    // Unpack features from bus
    wire [7:0] features_in [0:31];
    genvar g;
    generate
        for (g = 0; g < 32; g = g + 1) begin : gen_feat_unpack
            assign features_in[g] = features_in_bus[g*8 +: 8];
        end
    endgenerate

    // =========================================================================
    // FSM States
    // =========================================================================
    localparam STATE_IDLE     = 3'd0;
    localparam STATE_LAYER1   = 3'd1;
    localparam STATE_LAYER2   = 3'd2;
    localparam STATE_LAYER3   = 3'd3;
    localparam STATE_DONE     = 3'd4;

    reg [2:0] state;

    // Fixed-Point Scale & Shift Constants (from bit_exact_scorer.py)
    localparam signed [31:0] M1     = 32'sd642;
    localparam        [4:0]  SHIFT1 = 5'd16;
    localparam signed [31:0] M2     = 32'sd173;
    localparam        [4:0]  SHIFT2 = 5'd16;

    // Weight & Bias ROM Arrays
    // L1: 64 neurons * 32 inputs = 2048 INT8 weights, 64 INT32 biases
    reg signed [7:0]  w1_rom [0:2047];
    reg signed [31:0] b1_rom [0:63];

    // L2: 32 neurons * 64 inputs = 2048 INT8 weights, 32 INT32 biases
    reg signed [7:0]  w2_rom [0:2047];
    reg signed [31:0] b2_rom [0:31];

    // L3: 1 neuron * 32 inputs = 32 INT8 weights, 1 INT32 bias
    reg signed [7:0]  w3_rom [0:31];
    reg signed [31:0] b3_rom [0:0];

    // Activation Scratchpads
    reg signed [7:0] in_buf [0:31];
    reg signed [7:0] h1_buf [0:63];
    reg signed [7:0] h2_buf [0:31];

    // Counters
    reg [5:0] neuron_idx;  // Up to 64
    reg [5:0] input_step;  // Steps of 4 inputs (up to 16 steps for 64 inputs)
    reg signed [31:0] accum;

    // Initialize Memory from Hex Files
    initial begin
        $readmemh({MEM_DIR, "psmsl_weights_l1.mem"}, w1_rom);
        $readmemh({MEM_DIR, "psmsl_biases_l1.mem"},  b1_rom);
        $readmemh({MEM_DIR, "psmsl_weights_l2.mem"}, w2_rom);
        $readmemh({MEM_DIR, "psmsl_biases_l2.mem"},  b2_rom);
        $readmemh({MEM_DIR, "psmsl_weights_l3.mem"}, w3_rom);
        $readmemh({MEM_DIR, "psmsl_biases_l3.mem"},  b3_rom);
    end

    // DSP MAC Operands & Products
    // 4 Parallel Multipliers
    wire signed [7:0]  op_a0, op_a1, op_a2, op_a3;
    wire signed [7:0]  op_w0, op_w1, op_w2, op_w3;

    // Address Generators for 4 parallel weights
    wire [11:0] w1_base = {neuron_idx, 5'd0} + {input_step, 2'd0};
    wire [11:0] w2_base = {neuron_idx[4:0], 6'd0} + {input_step, 2'd0};
    wire [4:0]  w3_base = {input_step[2:0], 2'd0};

    assign op_w0 = (state == STATE_LAYER1) ? w1_rom[w1_base + 12'd0] :
                   (state == STATE_LAYER2) ? w2_rom[w2_base + 12'd0] :
                   (state == STATE_LAYER3) ? w3_rom[w3_base + 5'd0]  : 8'sd0;

    assign op_w1 = (state == STATE_LAYER1) ? w1_rom[w1_base + 12'd1] :
                   (state == STATE_LAYER2) ? w2_rom[w2_base + 12'd1] :
                   (state == STATE_LAYER3) ? w3_rom[w3_base + 5'd1]  : 8'sd0;

    assign op_w2 = (state == STATE_LAYER1) ? w1_rom[w1_base + 12'd2] :
                   (state == STATE_LAYER2) ? w2_rom[w2_base + 12'd2] :
                   (state == STATE_LAYER3) ? w3_rom[w3_base + 5'd2]  : 8'sd0;

    assign op_w3 = (state == STATE_LAYER1) ? w1_rom[w1_base + 12'd3] :
                   (state == STATE_LAYER2) ? w2_rom[w2_base + 12'd3] :
                   (state == STATE_LAYER3) ? w3_rom[w3_base + 5'd3]  : 8'sd0;

    // Activation Multiplexers
    wire [5:0] act_idx0 = {input_step, 2'd0};
    wire [5:0] act_idx1 = {input_step, 2'd1};
    wire [5:0] act_idx2 = {input_step, 2'd2};
    wire [5:0] act_idx3 = {input_step, 2'd3};

    assign op_a0 = (state == STATE_LAYER1) ? in_buf[act_idx0[4:0]] :
                   (state == STATE_LAYER2) ? h1_buf[act_idx0]      :
                   (state == STATE_LAYER3) ? h2_buf[act_idx0[4:0]] : 8'sd0;

    assign op_a1 = (state == STATE_LAYER1) ? in_buf[act_idx1[4:0]] :
                   (state == STATE_LAYER2) ? h1_buf[act_idx1]      :
                   (state == STATE_LAYER3) ? h2_buf[act_idx1[4:0]] : 8'sd0;

    assign op_a2 = (state == STATE_LAYER1) ? in_buf[act_idx2[4:0]] :
                   (state == STATE_LAYER2) ? h1_buf[act_idx2]      :
                   (state == STATE_LAYER3) ? h2_buf[act_idx2[4:0]] : 8'sd0;

    assign op_a3 = (state == STATE_LAYER1) ? in_buf[act_idx3[4:0]] :
                   (state == STATE_LAYER2) ? h1_buf[act_idx3]      :
                   (state == STATE_LAYER3) ? h2_buf[act_idx3[4:0]] : 8'sd0;

    // Pipelined MAC sum of 4 multipliers
    wire signed [31:0] mac_quad = ($signed(op_a0) * $signed(op_w0)) +
                                  ($signed(op_a1) * $signed(op_w1)) +
                                  ($signed(op_a2) * $signed(op_w2)) +
                                  ($signed(op_a3) * $signed(op_w3));

    // Scaling & Activation Logic
    wire signed [31:0] final_accum_l1  = accum + mac_quad;
    wire signed [63:0] scaled_accum_l1 = $signed(final_accum_l1) * $signed(M1);
    wire signed [31:0] shifted_l1      = scaled_accum_l1 >>> SHIFT1;
    wire signed [7:0]  relu_l1          = (shifted_l1 < 0) ? 8'sd0 :
                                         (shifted_l1 > 127) ? 8'sd127 : shifted_l1[7:0];

    wire signed [31:0] final_accum_l2  = accum + mac_quad;
    wire signed [63:0] scaled_accum_l2 = $signed(final_accum_l2) * $signed(M2);
    wire signed [31:0] shifted_l2      = scaled_accum_l2 >>> SHIFT2;
    wire signed [7:0]  relu_l2          = (shifted_l2 < 0) ? 8'sd0 :
                                         (shifted_l2 > 127) ? 8'sd127 : shifted_l2[7:0];

    // Main FSM
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= STATE_IDLE;
            busy        <= 1'b0;
            done        <= 1'b0;
            cand_id_out <= 4'd0;
            score_out   <= 32'sd0;
            neuron_idx  <= 6'd0;
            input_step  <= 6'd0;
            accum       <= 32'sd0;
            for (i = 0; i < 32; i = i + 1) in_buf[i] <= 8'sd0;
            for (i = 0; i < 64; i = i + 1) h1_buf[i] <= 8'sd0;
            for (i = 0; i < 32; i = i + 1) h2_buf[i] <= 8'sd0;
        end else begin
            case (state)
                STATE_IDLE: begin
                    done <= 1'b0;
                    if (start) begin
                        busy        <= 1'b1;
                        cand_id_out <= cand_id_in;
                        for (i = 0; i < 32; i = i + 1) begin
                            in_buf[i] <= $signed(features_in[i]);
                        end
                        neuron_idx  <= 6'd0;
                        input_step  <= 6'd0;
                        accum       <= b1_rom[0];  // Seed with Layer 1 Bias
                        state       <= STATE_LAYER1;
                    end else begin
                        busy <= 1'b0;
                    end
                end

                // -------------------------------------------------------------
                // Layer 1: 64 neurons, 32 inputs each (8 steps of 4 per neuron)
                // -------------------------------------------------------------
                STATE_LAYER1: begin
                    accum <= accum + mac_quad;
                    if (input_step == 6'd7) begin
                        // Completed all 32 inputs for this neuron
                        // Store activated output
                        h1_buf[neuron_idx] <= (shifted_l1 < 0) ? 8'sd0 :
                                              (shifted_l1 > 127) ? 8'sd127 : shifted_l1[7:0];
                        input_step <= 6'd0;
                        if (neuron_idx == 6'd63) begin
                            // Layer 1 complete! Transition to Layer 2
                            neuron_idx <= 6'd0;
                            accum      <= b2_rom[0];
                            state      <= STATE_LAYER2;
                        end else begin
                            neuron_idx <= neuron_idx + 6'd1;
                            accum      <= b1_rom[neuron_idx + 6'd1];
                        end
                    end else begin
                        input_step <= input_step + 6'd1;
                    end
                end

                // -------------------------------------------------------------
                // Layer 2: 32 neurons, 64 inputs each (16 steps of 4 per neuron)
                // -------------------------------------------------------------
                STATE_LAYER2: begin
                    accum <= accum + mac_quad;
                    if (input_step == 6'd15) begin
                        // Completed all 64 inputs for this neuron
                        h2_buf[neuron_idx[4:0]] <= (shifted_l2 < 0) ? 8'sd0 :
                                                  (shifted_l2 > 127) ? 8'sd127 : shifted_l2[7:0];
                        input_step <= 6'd0;
                        if (neuron_idx == 6'd31) begin
                            // Layer 2 complete! Transition to Layer 3
                            neuron_idx <= 6'd0;
                            accum      <= b3_rom[0];
                            state      <= STATE_LAYER3;
                        end else begin
                            neuron_idx <= neuron_idx + 6'd1;
                            accum      <= b2_rom[neuron_idx + 6'd1];
                        end
                    end else begin
                        input_step <= input_step + 6'd1;
                    end
                end

                // -------------------------------------------------------------
                // Layer 3: 1 neuron, 32 inputs (8 steps of 4)
                // -------------------------------------------------------------
                STATE_LAYER3: begin
                    accum <= accum + mac_quad;
                    if (input_step == 6'd7) begin
                        // Layer 3 complete! Final 32-bit score is in accum
                        score_out <= accum + mac_quad;
                        state     <= STATE_DONE;
                    end else begin
                        input_step <= input_step + 6'd1;
                    end
                end

                STATE_DONE: begin
                    busy  <= 1'b0;
                    done  <= 1'b1;
                    state <= STATE_IDLE;
                end

                default: state <= STATE_IDLE;
            endcase
        end
    end

endmodule
