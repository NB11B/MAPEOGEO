// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: mapeogeo_p0_cdc_fabric
// 6-Domain Asynchronous Spatial Hardware Substrate integrating real P0 Fabric Subsystems

`ifndef MAPEOGEO_P0_CDC_FABRIC_SV
`define MAPEOGEO_P0_CDC_FABRIC_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module mapeogeo_p0_cdc_fabric #(
    parameter int WORK_CELL_COUNT   = 4,
    parameter int OPERATOR_LANES    = 2,
    parameter int MEMORY_BANKS      = 2,
    parameter int AUTHORITY_ENGINES = 2,
    parameter int INGRESS_LANES     = 2,
    parameter int EGRESS_LANES      = 2,
    parameter int DATA_WIDTH        = 32,
    parameter int FRAC_BITS         = 16,
    parameter int STATE_WORDS       = 256,
    parameter int EVIDENCE_DEPTH    = 64,
    parameter int GRAPH_NODES       = 256,
    parameter int GRAPH_EDGES       = 1024,
    parameter int GRAPH_QUEUE_DEPTH = 128
) (
    // 6 Independent Physical Asynchronous Clock & Reset Domains
    input  logic                                clk_ingress,
    input  logic                                rst_ingress_async_n,

    input  logic                                clk_auth,
    input  logic                                rst_auth_async_n,

    input  logic                                clk_op,
    input  logic                                rst_op_async_n,

    input  logic                                clk_mem,
    input  logic                                rst_mem_async_n,

    input  logic                                clk_ev,
    input  logic                                rst_ev_async_n,

    input  logic                                clk_egress,
    input  logic                                rst_egress_async_n,

    // Autonomous Boot Control (clk_op domain)
    input  logic                                boot_trigger,
    output logic                                boot_complete,
    output logic                                fabric_halted,

    // External Work Ingress (Multi-Lane, clk_ingress domain)
    input  logic [INGRESS_LANES-1:0]            ingress_valid,
    output logic [INGRESS_LANES-1:0]            ingress_ready,
    input  logic [INGRESS_LANES*471-1:0]        ingress_desc,

    // External Result Egress (Multi-Lane, clk_egress domain)
    output logic [EGRESS_LANES-1:0]             egress_valid,
    input  logic [EGRESS_LANES-1:0]             egress_ready,
    output logic [EGRESS_LANES*32-1:0]          egress_uow_id,
    output logic [EGRESS_LANES*2-1:0]           egress_status,
    output logic [EGRESS_LANES*128-1:0]         egress_result,
    output logic [EGRESS_LANES*64-1:0]          egress_evidence_root,

    // Diagnostic Inspection Port
    output geo_telemetry_t                      telemetry_out,
    output logic [63:0]                         current_evidence_root_out,
    output logic [WORK_CELL_COUNT-1:0]          active_work_cells_out,
    output logic [63:0]                         semantic_evidence_root_out
);

    // ------------------------------------------------------------------------
    // Reset Synchronizers (RDC) for Each Physical Domain
    // ------------------------------------------------------------------------
    logic rst_ing_n, rst_auth_n, rst_op_n, rst_mem_n, rst_ev_n, rst_eg_n;

    geo_reset_sync u_sync_rst_ing  (.clk(clk_ingress), .async_rst_n(rst_ingress_async_n), .sync_rst_n(rst_ing_n));
    geo_reset_sync u_sync_rst_auth (.clk(clk_auth),    .async_rst_n(rst_auth_async_n),    .sync_rst_n(rst_auth_n));
    geo_reset_sync u_sync_rst_op   (.clk(clk_op),      .async_rst_n(rst_op_async_n),      .sync_rst_n(rst_op_n));
    geo_reset_sync u_sync_rst_mem  (.clk(clk_mem),     .async_rst_n(rst_mem_async_n),     .sync_rst_n(rst_mem_n));
    geo_reset_sync u_sync_rst_ev   (.clk(clk_ev),      .async_rst_n(rst_ev_async_n),      .sync_rst_n(rst_ev_n));
    geo_reset_sync u_sync_rst_eg   (.clk(clk_egress),  .async_rst_n(rst_egress_async_n),  .sync_rst_n(rst_eg_n));

    // ------------------------------------------------------------------------
    // Spatial Multi-Lane Ingress CDC FIFOs (clk_ingress -> clk_op)
    // ------------------------------------------------------------------------
    logic [INGRESS_LANES-1:0]     ing_fifo_wfull;
    logic [INGRESS_LANES-1:0]     ing_fifo_rempty;
    logic [INGRESS_LANES*471-1:0] ing_fifo_rdata;
    logic [INGRESS_LANES-1:0]     ing_fifo_rinc;

    genvar i_lane;
    generate
        for (i_lane = 0; i_lane < INGRESS_LANES; i_lane = i_lane + 1) begin : gen_ingress_cdc
            assign ingress_ready[i_lane] = !ing_fifo_wfull[i_lane];

            geo_async_fifo #(
                .DWIDTH(471),
                .AWIDTH(4)
            ) u_ing_cdc_fifo (
                .wclk          (clk_ingress),
                .wrst_n        (rst_ing_n),
                .winc          (ingress_valid[i_lane] && !ing_fifo_wfull[i_lane]),
                .wdata         (ingress_desc[i_lane*471 +: 471]),
                .wfull         (ing_fifo_wfull[i_lane]),
                .walmost_full  (),
                .rclk          (clk_op),
                .rrst_n        (rst_op_n),
                .rinc          (ing_fifo_rinc[i_lane]),
                .rdata         (ing_fifo_rdata[i_lane*471 +: 471]),
                .rempty        (ing_fifo_rempty[i_lane]),
                .ralmost_empty ()
            );
        end
    endgenerate

    // ------------------------------------------------------------------------
    // Internal Core Spatial Fabric (Instantiating mapeogeo_p0_fabric)
    // ------------------------------------------------------------------------
    logic [EGRESS_LANES-1:0]     core_egress_valid;
    logic [EGRESS_LANES-1:0]     core_egress_ready;
    logic [EGRESS_LANES*32-1:0]  core_egress_uow_id;
    logic [EGRESS_LANES*2-1:0]   core_egress_status;
    logic [EGRESS_LANES*128-1:0] core_egress_result;
    logic [EGRESS_LANES*64-1:0]  core_egress_evidence_root;

    // Connect core ingress ports from CDC FIFO outputs
    logic [INGRESS_LANES-1:0] core_ingress_valid;
    logic [INGRESS_LANES-1:0] core_ingress_ready;

    assign core_ingress_valid = ~ing_fifo_rempty;
    assign ing_fifo_rinc      = core_ingress_ready & core_ingress_valid;

    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT   (WORK_CELL_COUNT),
        .OPERATOR_LANES    (OPERATOR_LANES),
        .MEMORY_BANKS      (MEMORY_BANKS),
        .AUTHORITY_ENGINES (AUTHORITY_ENGINES),
        .INGRESS_LANES     (INGRESS_LANES),
        .EGRESS_LANES      (EGRESS_LANES),
        .DATA_WIDTH        (DATA_WIDTH),
        .FRAC_BITS         (FRAC_BITS),
        .STATE_WORDS       (STATE_WORDS),
        .EVIDENCE_DEPTH    (EVIDENCE_DEPTH),
        .GRAPH_NODES       (GRAPH_NODES),
        .GRAPH_EDGES       (GRAPH_EDGES),
        .GRAPH_QUEUE_DEPTH (GRAPH_QUEUE_DEPTH)
    ) u_core_spatial_fabric (
        .clk                       (clk_op),
        .reset_n                   (rst_op_n),
        .boot_trigger              (boot_trigger),
        .boot_complete             (boot_complete),
        .fabric_halted             (fabric_halted),
        .ingress_valid             (core_ingress_valid),
        .ingress_ready             (core_ingress_ready),
        .ingress_desc              (ing_fifo_rdata),
        .egress_valid              (core_egress_valid),
        .egress_ready              (core_egress_ready),
        .egress_uow_id             (core_egress_uow_id),
        .egress_status             (core_egress_status),
        .egress_result             (core_egress_result),
        .egress_evidence_root      (core_egress_evidence_root),
        .graph_node_wr_en          (1'b0),
        .graph_node_wr_addr        (16'd0),
        .graph_node_wr_data        ('0),
        .graph_edge_wr_en          (1'b0),
        .graph_edge_wr_addr        (16'd0),
        .graph_edge_wr_data        ('0),
        .telemetry_out             (telemetry_out),
        .current_evidence_root_out (current_evidence_root_out),
        .active_work_cells_out     (active_work_cells_out),
        .stall_inject_mem          ('0),
        .stall_inject_operator     ('0),
        .stall_inject_authority    ('0),
        .semantic_evidence_root_out(semantic_evidence_root_out)
    );

    // ------------------------------------------------------------------------
    // Spatial Multi-Lane Egress CDC FIFOs (clk_op -> clk_egress)
    // ------------------------------------------------------------------------
    localparam int EGRESS_BUNDLE_W = 32 + 2 + 128 + 64; // uow_id + status + result + evidence_root

    genvar e_lane;
    generate
        for (e_lane = 0; e_lane < EGRESS_LANES; e_lane = e_lane + 1) begin : gen_egress_cdc
            logic [EGRESS_BUNDLE_W-1:0] eg_wdata;
            logic [EGRESS_BUNDLE_W-1:0] eg_rdata;
            logic                       eg_fifo_wfull;
            logic                       eg_fifo_rempty;

            assign eg_wdata = {
                core_egress_uow_id[e_lane*32 +: 32],
                core_egress_status[e_lane*2 +: 2],
                core_egress_result[e_lane*128 +: 128],
                core_egress_evidence_root[e_lane*64 +: 64]
            };

            assign core_egress_ready[e_lane] = !eg_fifo_wfull;

            geo_async_fifo #(
                .DWIDTH(EGRESS_BUNDLE_W),
                .AWIDTH(4)
            ) u_eg_cdc_fifo (
                .wclk          (clk_op),
                .wrst_n        (rst_op_n),
                .winc          (core_egress_valid[e_lane] && !eg_fifo_wfull),
                .wdata         (eg_wdata),
                .wfull         (eg_fifo_wfull),
                .walmost_full  (),
                .rclk          (clk_egress),
                .rrst_n        (rst_eg_n),
                .rinc          (egress_ready[e_lane] && !eg_fifo_rempty),
                .rdata         (eg_rdata),
                .rempty        (eg_fifo_rempty),
                .ralmost_empty ()
            );

            assign egress_valid[e_lane] = !eg_fifo_rempty;
            assign {
                egress_uow_id[e_lane*32 +: 32],
                egress_status[e_lane*2 +: 2],
                egress_result[e_lane*128 +: 128],
                egress_evidence_root[e_lane*64 +: 64]
            } = eg_rdata;
        end
    endgenerate

endmodule

`endif // MAPEOGEO_P0_CDC_FABRIC_SV
