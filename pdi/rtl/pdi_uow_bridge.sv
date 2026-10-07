// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Unified Proposal-Disposition Bridge Top-Level
// Module: pdi_uow_bridge
// Integrates 32-bit streaming ingress/egress, proposal validator, and MAPEOGEO P0 Fabric

`ifndef PDI_UOW_BRIDGE_SV
`define PDI_UOW_BRIDGE_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module pdi_uow_bridge #(
    parameter int WORK_CELL_COUNT   = 4,
    parameter int OPERATOR_LANES    = 1,
    parameter int MEMORY_BANKS      = 1,
    parameter int AUTHORITY_ENGINES = 1,
    parameter int STATE_WORDS       = 256,
    parameter int GRAPH_NODES       = 256
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Autonomous Boot Control
    input  logic                   boot_trigger,
    output logic                   boot_complete,
    output logic                   fabric_halted,

    // Host 32-bit Streaming Logical Interface (Ingress)
    input  logic                   pdi_rx_valid,
    output logic                   pdi_rx_ready,
    input  logic [31:0]            pdi_rx_data,
    input  logic                   pdi_rx_last,

    // Host 32-bit Streaming Logical Interface (Egress)
    output logic                   pdi_tx_valid,
    input  logic                   pdi_tx_ready,
    output logic [31:0]            pdi_tx_data,
    output logic                   pdi_tx_last,

    // System Authority Mask Configuration
    input  logic [31:0]            authorized_capability_mask
);

    // --- Ingress to Validator Interconnect ---
    logic         pkt_assembled_valid;
    logic         pkt_consumed_ack;
    logic [511:0] pkt_raw_data;
    logic         pkt_framing_error;
    logic         pkt_crc_error;

    pdi_ingress u_ingress (
        .clk(clk),
        .reset_n(reset_n),
        .pdi_rx_valid(pdi_rx_valid),
        .pdi_rx_ready(pdi_rx_ready),
        .pdi_rx_data(pdi_rx_data),
        .pdi_rx_last(pdi_rx_last),
        .pkt_assembled_valid(pkt_assembled_valid),
        .pkt_consumed_ack(pkt_consumed_ack),
        .pkt_raw_data(pkt_raw_data),
        .pkt_framing_error(pkt_framing_error),
        .pkt_crc_error(pkt_crc_error)
    );

    // --- Validator to Fabric Ingress Interconnect ---
    logic         uow_valid;
    uow_desc_t    uow_desc;
    logic [31:0]  uow_seq_id;
    logic         uow_ack;

    logic         refusal_valid;
    logic [31:0]  refusal_seq_id;
    logic [31:0]  refusal_proposal_id;
    logic [31:0]  refusal_reason_code;
    logic         refusal_ack;

    pdi_packet_validator #(
        .STATE_WORDS(STATE_WORDS),
        .GRAPH_NODES(GRAPH_NODES)
    ) u_validator (
        .clk(clk),
        .reset_n(reset_n),
        .pkt_valid(pkt_assembled_valid),
        .pkt_raw_data(pkt_raw_data),
        .pkt_framing_error(pkt_framing_error),
        .pkt_crc_error(pkt_crc_error),
        .pkt_ack(pkt_consumed_ack),
        .authorized_capability_mask(authorized_capability_mask),
        .uow_valid(uow_valid),
        .uow_desc(uow_desc),
        .uow_seq_id(uow_seq_id),
        .uow_ack(uow_ack),
        .refusal_valid(refusal_valid),
        .refusal_seq_id(refusal_seq_id),
        .refusal_proposal_id(refusal_proposal_id),
        .refusal_reason_code(refusal_reason_code),
        .refusal_ack(refusal_ack)
    );

    // --- Fabric Core Ingress / Egress Ports ---
    logic         fabric_ingress_ready;
    logic         fabric_egress_valid;
    logic         fabric_egress_ready;
    logic [31:0]  fabric_uow_id;
    logic [1:0]   fabric_status;
    logic [127:0] fabric_result_raw;
    logic [63:0]  fabric_evidence_root;

    // Simple tracking table for sequence ID recovery: seq_map[uow_id % 16]
    logic [31:0] seq_map [0:15];
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            for (int i = 0; i < 16; i++) seq_map[i] <= 32'd0;
        end else if (uow_valid && fabric_ingress_ready) begin
            seq_map[uow_desc.uow_id[3:0]] <= uow_seq_id;
        end
    end

    assign uow_ack = fabric_ingress_ready;

    // Instantiate MAPEOGEO P0 Fabric
    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .OPERATOR_LANES(OPERATOR_LANES),
        .MEMORY_BANKS(MEMORY_BANKS),
        .AUTHORITY_ENGINES(AUTHORITY_ENGINES),
        .STATE_WORDS(STATE_WORDS),
        .GRAPH_NODES(GRAPH_NODES)
    ) u_fabric (
        .clk(clk),
        .reset_n(reset_n),
        .boot_trigger(boot_trigger),
        .boot_complete(boot_complete),
        .fabric_halted(fabric_halted),
        .ingress_valid(uow_valid),
        .ingress_ready(fabric_ingress_ready),
        .ingress_desc(uow_desc),
        .egress_valid(fabric_egress_valid),
        .egress_ready(fabric_egress_ready),
        .egress_uow_id(fabric_uow_id),
        .egress_status(fabric_status),
        .egress_result(fabric_result_raw),
        .egress_evidence_root(fabric_evidence_root),
        .telemetry_out(),
        .current_evidence_root_out(),
        .active_work_cells_out(),
        .semantic_evidence_root_out()
    );

    cl20_mv_t fabric_mv_result;
    assign fabric_mv_result = cl20_mv_t'(fabric_result_raw);

    wire [31:0] matching_seq_id = seq_map[fabric_uow_id[3:0]];

    // --- Egress Formatter ---
    pdi_egress u_egress (
        .clk(clk),
        .reset_n(reset_n),
        .pdi_tx_valid(pdi_tx_valid),
        .pdi_tx_ready(pdi_tx_ready),
        .pdi_tx_data(pdi_tx_data),
        .pdi_tx_last(pdi_tx_last),
        .fabric_egress_valid(fabric_egress_valid),
        .fabric_egress_ready(fabric_egress_ready),
        .fabric_uow_id(fabric_uow_id),
        .fabric_seq_id(matching_seq_id),
        .fabric_status(fabric_status),
        .fabric_result(fabric_mv_result),
        .fabric_evidence_root(fabric_evidence_root),
        .fabric_dest_addr(8'd0),
        .fabric_dest_version(16'd0),
        .refusal_valid(refusal_valid),
        .refusal_ready(refusal_ack),
        .refusal_seq_id(refusal_seq_id),
        .refusal_proposal_id(refusal_proposal_id),
        .refusal_reason_code(refusal_reason_code)
    );

endmodule

`endif // PDI_UOW_BRIDGE_SV
