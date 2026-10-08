// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Authoritative Hardware Proposal Validator
// Module: pdi_packet_validator
// Enforces Section 5/9 checks on reassembled candidate packets before admission

`ifndef PDI_PACKET_VALIDATOR_SV
`define PDI_PACKET_VALIDATOR_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module pdi_packet_validator #(
    parameter int STATE_WORDS = 256,
    parameter int GRAPH_NODES = 256
) (
    input  logic              clk,
    input  logic              reset_n,

    // Ingress packet interface
    input  logic              pkt_valid,
    input  logic [511:0]      pkt_raw_data, // 16 * 32
    input  logic              pkt_framing_error,
    input  logic              pkt_crc_error,
    output logic              pkt_ack,

    // Authoritative capability mask
    input  logic [31:0]       authorized_capability_mask,

    // Admitted UoW Descriptor output (471 bits)
    output logic              uow_valid,
    output uow_desc_t         uow_desc,
    output logic [31:0]       uow_seq_id,
    input  logic              uow_ack,

    // Refusal output (if packet is malformed or unauthorized)
    output logic              refusal_valid,
    output logic [31:0]       refusal_seq_id,
    output logic [31:0]       refusal_proposal_id,
    output logic [31:0]       refusal_reason_code,
    input  logic              refusal_ack
);

    // Unpack fields from 16 words
    logic [31:0] w [0:15];
    always_comb begin
        for (int i = 0; i < 16; i++) begin
            w[i] = pkt_raw_data[i*32 +: 32];
        end
    end

    wire [7:0]  pkt_type  = w[1][7:0];
    wire [7:0]  proto_ver = w[1][15:8];
    wire [31:0] seq_id    = w[2];
    wire [31:0] prop_id   = w[3];
    wire [31:0] state_ver = w[4];
    wire [5:0]  opcode    = w[5][5:0];
    wire [7:0]  dest_addr = w[5][15:8];
    wire [7:0]  src_a     = w[5][23:16];
    wire [7:0]  src_b     = w[5][31:24];
    wire [31:0] auth_tok  = w[6];
    wire        use_imm   = w[7][0];
    wire        has_gmut  = w[7][1];
    wire [2:0]  dep_cond  = w[7][4:2];

    // Multivector immediate
    cl20_mv_t imm_val;
    assign imm_val.s   = w[8];
    assign imm_val.e1  = w[9];
    assign imm_val.e2  = w[10];
    assign imm_val.e12 = w[11];

    // Graph parameters
    wire [15:0] g_node    = w[12][15:0];
    wire [7:0]  g_rel     = w[12][23:16];
    wire [7:0]  g_type    = w[12][31:24];
    wire [1:0]  g_rad     = w[13][1:0];
    wire [1:0]  g_mut_cmd = w[13][3:2];
    wire [15:0] g_target  = w[13][19:4];
    wire [7:0]  g_mrel    = w[13][27:20];
    wire [7:0]  g_mflags  = {4'b0000, w[13][31:28]};

    // Validation checks
    wire chk_magic_pass    = !pkt_framing_error && (w[0] == 32'h50444930);
    wire chk_crc_pass      = !pkt_crc_error;
    wire chk_type_pass     = (pkt_type == 8'd1) && (proto_ver == 8'd1);
    wire chk_opcode_pass   = (opcode <= 6'd33);
    wire chk_addr_pass     = (dest_addr < STATE_WORDS) && (src_a < STATE_WORDS) && (src_b < STATE_WORDS);
    wire chk_auth_pass     = (auth_tok != 32'd0) && ((auth_tok & authorized_capability_mask) == auth_tok);
    wire chk_version_pass  = (state_ver < 32'd1000);
    wire chk_graph_pass    = (!has_gmut) || (g_node < GRAPH_NODES && g_target < GRAPH_NODES);

    typedef enum logic [1:0] {
        V_IDLE    = 2'd0,
        V_ADMIT   = 2'd1,
        V_REFUSE  = 2'd2
    } val_state_t;

    val_state_t v_state;
    logic [31:0] r_reason;

    assign uow_valid     = (v_state == V_ADMIT);
    assign refusal_valid = (v_state == V_REFUSE);
    assign pkt_ack       = (v_state == V_ADMIT && uow_ack) || (v_state == V_REFUSE && refusal_ack);

    assign uow_seq_id          = seq_id;
    assign refusal_seq_id      = seq_id;
    assign refusal_proposal_id = prop_id;
    assign refusal_reason_code = r_reason;

    // Build uow_desc_t
    always_comb begin
        uow_desc.uow_id          = prop_id;
        uow_desc.opcode          = geo_opcode_t'(opcode);
        uow_desc.dest_addr       = dest_addr;
        uow_desc.src_a_addr      = src_a;
        uow_desc.src_b_addr      = src_b;
        uow_desc.dep_mask        = 128'd0;
        uow_desc.pre_state_hash  = state_ver;
        uow_desc.auth_token      = auth_tok;
        uow_desc.imm_operand     = imm_val;
        uow_desc.use_immediate   = use_imm;
        uow_desc.dep_cond        = dep_cond_type_t'(dep_cond);
        uow_desc.graph_query     = {g_node, g_rel, g_type, g_rad};
        uow_desc.has_graph_mut   = has_gmut;
        uow_desc.graph_mut_cmd   = graph_mut_cmd_t'(g_mut_cmd);
        uow_desc.graph_mut_node  = g_node;
        uow_desc.graph_mut_target= g_target;
        uow_desc.graph_mut_rel   = g_mrel;
        uow_desc.graph_mut_flags = g_mflags;
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            v_state  <= V_IDLE;
            r_reason <= 32'd0;
        end else begin
            case (v_state)
                V_IDLE: begin
                    if (pkt_valid) begin
                        if (!chk_magic_pass) begin
                            r_reason <= 32'd1; // ERR_BAD_MAGIC
                            v_state  <= V_REFUSE;
                        end else if (!chk_crc_pass) begin
                            r_reason <= 32'd2; // ERR_BAD_CRC
                            v_state  <= V_REFUSE;
                        end else if (!chk_type_pass) begin
                            r_reason <= 32'd3; // ERR_BAD_LENGTH / TYPE
                            v_state  <= V_REFUSE;
                        end else if (!chk_opcode_pass) begin
                            r_reason <= 32'd4; // ERR_UNKNOWN_OPERATOR
                            v_state  <= V_REFUSE;
                        end else if (!chk_addr_pass || !chk_graph_pass) begin
                            r_reason <= 32'd5; // ERR_OUT_OF_BOUNDS_REF
                            v_state  <= V_REFUSE;
                        end else if (!chk_version_pass) begin
                            r_reason <= 32'd6; // ERR_STALE_STATE_VERSION
                            v_state  <= V_REFUSE;
                        end else if (!chk_auth_pass) begin
                            r_reason <= 32'd7; // ERR_UNAUTHORIZED_CAPABILITY
                            v_state  <= V_REFUSE;
                        end else begin
                            // All checks pass: admit candidate UoW
                            v_state <= V_ADMIT;
                        end
                    end
                end

                V_ADMIT: begin
                    if (uow_ack) begin
                        v_state <= V_IDLE;
                    end
                end

                V_REFUSE: begin
                    if (refusal_ack) begin
                        v_state <= V_IDLE;
                    end
                end

                default: v_state <= V_IDLE;
            endcase
        end
    end

endmodule

`endif // PDI_PACKET_VALIDATOR_SV
