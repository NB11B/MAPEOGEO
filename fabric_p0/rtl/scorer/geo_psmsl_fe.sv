// SPDX-License-Identifier: MIT
// =============================================================================
// Module: geo_psmsl_fe
// Project: MAPEOGEO fabric_p0 / Track PDI-v0.9
// Description:
//   Synthesizable On-Chip PSMSL 32-Dimensional Relational Feature Extractor.
//   Transforms hardware ingress candidate metadata and observable context into
//   a 256-bit packed bus of 32 INT8 relational features for geo_psmsl_scorer.
//
// Resource Budget:
//   - Combinational / 1-cycle registered architecture (~150-200 LUTs, 0 DSPs, 0 BRAMs)
// =============================================================================

`timescale 1ns / 1ps

module geo_psmsl_fe (
    input  wire        clk,
    input  wire        rst_n,

    // Ingress Candidate Metadata
    input  wire        cand_valid,
    input  wire [5:0]  opcode,
    input  wire [1:0]  arity,
    input  wire        has_dest,
    input  wire [7:0]  dest_addr,
    input  wire        has_goal,
    input  wire [7:0]  goal_addr,
    input  wire [1:0]  num_operands,
    input  wire [7:0]  src_addr0,
    input  wire [7:0]  src_addr1,
    input  wire [15:0] state_version,
    input  wire [31:0] cap_mask,
    input  wire [15:0] goal_intent_mask,

    // Output Feature Bus to Scorer
    output reg         fe_valid,
    output reg  [255:0] features_out_bus
);

    // Opcode scaling lookup table: round(op / 34.0 * 127)
    function [7:0] get_op_scale(input [5:0] op);
        case (op)
            6'd0:  get_op_scale = 8'd0;
            6'd1:  get_op_scale = 8'd4;
            6'd2:  get_op_scale = 8'd7;
            6'd3:  get_op_scale = 8'd11;
            6'd4:  get_op_scale = 8'd15;
            6'd5:  get_op_scale = 8'd19;
            6'd6:  get_op_scale = 8'd22;
            6'd7:  get_op_scale = 8'd26;
            6'd8:  get_op_scale = 8'd30;
            6'd9:  get_op_scale = 8'd34;
            6'd10: get_op_scale = 8'd37;
            6'd11: get_op_scale = 8'd41;
            6'd12: get_op_scale = 8'd45;
            6'd13: get_op_scale = 8'd49;
            6'd14: get_op_scale = 8'd52;
            6'd15: get_op_scale = 8'd56;
            6'd31: get_op_scale = 8'd116;
            6'd32: get_op_scale = 8'd120;
            6'd33: get_op_scale = 8'd123;
            6'd34: get_op_scale = 8'd127;
            default: get_op_scale = 8'd0;
        endcase
    endfunction

    // Structural & Category Decoders
    wire is_commutative = (opcode == 6'd1  || opcode == 6'd3  || opcode == 6'd9 ||
                           opcode == 6'd31 || opcode == 6'd33);
    wire is_unary_geom  = (opcode == 6'd6  || opcode == 6'd7  || opcode == 6'd8);
    wire is_bilinear_g  = (opcode == 6'd5  || opcode == 6'd9  || opcode == 6'd10 ||
                           opcode == 6'd11 || opcode == 6'd12);
    wire is_alu_arith   = (opcode == 6'd1  || opcode == 6'd2  || opcode == 6'd3 ||
                           opcode == 6'd31 || opcode == 6'd32 || opcode == 6'd33);

    wire dest_match_goal = (has_dest && has_goal && (dest_addr == goal_addr));

    // Combinational Feature Generation
    reg [7:0] f [0:31];
    integer j;

    always @(*) begin
        // 1. Structural [0..7]
        f[0] = get_op_scale(opcode);
        f[1] = (arity == 2'd2) ? 8'd127 : (arity == 2'd1) ? 8'd64 : 8'd0;
        f[2] = has_dest ? 8'd127 : 8'd0;
        f[3] = dest_match_goal ? 8'd127 : 8'd0;
        f[4] = is_commutative ? 8'd127 : 8'd0;
        f[5] = is_unary_geom ? 8'd127 : 8'd0;
        f[6] = is_bilinear_g ? 8'd127 : 8'd0;
        f[7] = is_alu_arith ? 8'd127 : 8'd0;

        // 2. Causal [8..11]
        f[8]  = (state_version < 16'd1500) ? 8'd127 : 8'd0;
        f[9]  = 8'd0;
        f[10] = (num_operands >= 2'd2) ? 8'd85 : (num_operands == 2'd1) ? 8'd42 : 8'd0;
        f[11] = (dest_addr >= 8'd224) ? 8'd127 : 8'd0;

        // 3. Geometric Algebra [12..19]
        f[12] = 8'd127; // Grade compatible
        f[13] = (opcode == 6'd9) ? 8'd127 : 8'd0;                                     // Scalar
        f[14] = (opcode == 6'd1 || opcode == 6'd2 || opcode == 6'd6 || opcode == 6'd7 ||
                 opcode == 6'd8 || opcode == 6'd31 || opcode == 6'd32) ? 8'd127 : 8'd0; // Vector
        f[15] = (opcode == 6'd10) ? 8'd127 : 8'd0;                                    // Bivector / Wedge
        f[16] = (opcode == 6'd3 || opcode == 6'd5 || opcode == 6'd11 || opcode == 6'd12 ||
                 opcode == 6'd33) ? 8'd127 : 8'd0;                                    // Multivector
        f[17] = 8'd127;
        f[18] = (opcode == 6'd6) ? 8'd127 : 8'd0; // Reversion
        f[19] = (opcode == 6'd4 || opcode == 6'd6 || opcode == 6'd7 || opcode == 6'd8) ? 8'd127 : 8'd0;

        // 4. Intent Alignment [20..25]
        f[20] = goal_intent_mask[0] ? 8'd127 : 8'd0;
        f[21] = (goal_intent_mask[1] && opcode == 6'd10) ? 8'd127 : 8'd0; // Wedge
        f[22] = (goal_intent_mask[2] && opcode == 6'd9)  ? 8'd127 : 8'd0; // Dot
        f[23] = (goal_intent_mask[3] && (opcode == 6'd5 || opcode == 6'd11)) ? 8'd127 : 8'd0; // Bracket
        f[24] = (goal_intent_mask[4] && (opcode == 6'd5 || opcode == 6'd6))  ? 8'd127 : 8'd0; // Rotor
        f[25] = 8'd0;

        // 5. Hardware Constraints [26..31]
        f[26] = 8'd127; // Addresses in bounds
        f[27] = cap_mask[0] ? 8'd127 : 8'd0;
        f[28] = (opcode == 6'd0) ? 8'd127 : 8'd0; // Abstain
        f[29] = 8'd0;
        f[30] = dest_match_goal ? 8'd127 : 8'd0;
        f[31] = 8'd127;
    end

    // Registered Output
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fe_valid         <= 1'b0;
            features_out_bus <= 256'd0;
        end else begin
            fe_valid <= cand_valid;
            if (cand_valid) begin
                for (j = 0; j < 32; j = j + 1) begin
                    features_out_bus[j*8 +: 8] <= f[j];
                end
            end
        end
    end

endmodule
