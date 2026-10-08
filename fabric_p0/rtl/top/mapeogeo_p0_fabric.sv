// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: mapeogeo_p0_fabric
// Standalone Top-Level Computational Fabric integrating Autonomous Boot, Work Fabric, Memory & Evidence

`ifndef MAPEOGEO_P0_FABRIC_SV
`define MAPEOGEO_P0_FABRIC_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module mapeogeo_p0_fabric #(
    parameter int WORK_CELL_COUNT   = 4,
    parameter int OPERATOR_LANES    = 1,
    parameter int MEMORY_BANKS      = 1,
    parameter int AUTHORITY_ENGINES = 1,
    parameter int INGRESS_LANES     = 1,
    parameter int EGRESS_LANES      = 1,
    parameter int DATA_WIDTH        = 32,
    parameter int FRAC_BITS         = 16,
    parameter int STATE_WORDS       = 256,
    parameter int EVIDENCE_DEPTH    = 64,
    parameter int GRAPH_NODES       = 256,
    parameter int GRAPH_EDGES       = 1024,
    parameter int GRAPH_QUEUE_DEPTH = 128
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Autonomous Boot Control (Section 11)
    input  logic                   boot_trigger,
    output logic                   boot_complete,
    output logic                   fabric_halted,

    // External Work Ingress (Multi-Lane, P0.6F)
    input  logic [INGRESS_LANES-1:0]           ingress_valid,
    output logic [INGRESS_LANES-1:0]           ingress_ready,
    input  logic [INGRESS_LANES*471-1:0]       ingress_desc,

    // External Result Egress (Multi-Lane, P0.6F)
    output logic [EGRESS_LANES-1:0]            egress_valid,
    input  logic [EGRESS_LANES-1:0]            egress_ready,
    output logic [EGRESS_LANES*32-1:0]         egress_uow_id,
    output logic [EGRESS_LANES*2-1:0]          egress_status,
    output logic [EGRESS_LANES*128-1:0]        egress_result,
    output logic [EGRESS_LANES*64-1:0]         egress_evidence_root,

    // Graph Memory Boot Programming Port (Section 7 & P0.5)
    input  logic                   graph_node_wr_en = 1'b0,
    input  logic [15:0]            graph_node_wr_addr = 16'd0,
    input  graph_node_t            graph_node_wr_data = '0,
    input  logic                   graph_edge_wr_en = 1'b0,
    input  logic [15:0]            graph_edge_wr_addr = 16'd0,
    input  graph_edge_t            graph_edge_wr_data = '0,

    // State Memory Boot Programming Port
    input  logic                   state_wr_en = 1'b0,
    input  logic [7:0]             state_wr_addr = 8'd0,
    input  cl20_mv_t               state_wr_data = '0,

    // Diagnostic Inspection Port (Section 13 / 17)
    output geo_telemetry_t         telemetry_out,
    output logic [63:0]            current_evidence_root_out,
    output logic [WORK_CELL_COUNT-1:0] active_work_cells_out,

    // P0.8 Spatial Timing Perturbation Injection Ports
    input  logic [MEMORY_BANKS-1:0]             stall_inject_mem = '0,
    input  logic [OPERATOR_LANES-1:0]           stall_inject_operator = '0,
    input  logic [AUTHORITY_ENGINES-1:0]        stall_inject_authority = '0,
    output logic [63:0]                         semantic_evidence_root_out,

    // P0.9 Integrated Candidate Scorer Co-Processor Ports
    input  logic                                pdi_scorer_start = 1'b0,
    input  logic [3:0]                          pdi_scorer_cand_id = 4'd0,
    input  logic [255:0]                        pdi_scorer_features = '0,
    output logic                                pdi_scorer_busy,
    output logic                                pdi_scorer_done,
    output logic [3:0]                          pdi_scorer_cand_out,
    output logic signed [31:0]                  pdi_scorer_score_out
);

    // --- Boot State Machine (Section 11.1) ---
    // RESET -> LOAD ROOT MANIFEST -> VERIFY ROOT -> INITIALIZE CAPABILITIES -> INITIALIZE STATE -> LOAD BOOT WORK -> RUN
    typedef enum logic [2:0] {
        BOOT_RESET        = 3'd0,
        BOOT_VERIFY_ROOT  = 3'd1,
        BOOT_INIT_CAPS    = 3'd2,
        BOOT_INIT_STATE   = 3'd3,
        BOOT_RUN          = 3'd4,
        BOOT_HALT         = 3'd5
    } boot_state_t;

    boot_state_t boot_fsm;
    logic [31:0] fabric_capabilities;
    logic        internal_boot_complete;

    assign boot_complete = internal_boot_complete;
    assign fabric_halted = (boot_fsm == BOOT_HALT);

    // Boot FSM
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            boot_fsm               <= BOOT_RESET;
            fabric_capabilities    <= '0;
            internal_boot_complete <= 1'b0;
        end else begin
            case (boot_fsm)
                BOOT_RESET: begin
                    if (boot_trigger) begin
                        boot_fsm <= BOOT_VERIFY_ROOT;
                    end
                end
                BOOT_VERIFY_ROOT: begin
                    // Verify deterministic root manifest
                    boot_fsm <= BOOT_INIT_CAPS;
                end
                BOOT_INIT_CAPS: begin
                    // Authorize standard PSMSL capabilities (0xFFFFFFFF = full operator & ALU capability)
                    fabric_capabilities <= 32'hFFFFFFFF;
                    boot_fsm            <= BOOT_INIT_STATE;
                end
                BOOT_INIT_STATE: begin
                    internal_boot_complete <= 1'b1;
                    boot_fsm               <= BOOT_RUN;
                end
                BOOT_RUN: begin
                    // Running autonomously without host intervention!
                end
                BOOT_HALT: begin
                    // Fabric halted
                end
            endcase
        end
    end

    // --- State Memory (Multi-Bank, P0.6D) ---
    logic [MEMORY_BANKS-1:0]             mem_commit_en;
    logic [MEMORY_BANKS*8-1:0]           mem_commit_addr;
    logic [MEMORY_BANKS*128-1:0]         mem_commit_data;
    logic [MEMORY_BANKS*16-1:0]          post_commit_version;

    logic [MEMORY_BANKS*8-1:0]           mem_rd_a_addr;
    logic [MEMORY_BANKS*8-1:0]           mem_rd_b_addr;
    logic [MEMORY_BANKS*128-1:0]         mem_rd_a_data;
    logic [MEMORY_BANKS*128-1:0]         mem_rd_b_data;
    logic [MEMORY_BANKS*16-1:0]          mem_rd_a_ver;
    logic [MEMORY_BANKS*16-1:0]          mem_rd_b_ver;

    logic [AUTHORITY_ENGINES*8-1:0]      auth_check_dest_addr;
    logic [AUTHORITY_ENGINES*16-1:0]     auth_current_dest_version;

    geo_state_memory #(
        .ADDR_WIDTH(8),
        .WORDS(STATE_WORDS),
        .MEMORY_BANKS(MEMORY_BANKS),
        .AUTHORITY_ENGINES(AUTHORITY_ENGINES)
    ) u_state_memory (
        .clk(clk),
        .reset_n(reset_n),
        .boot_wr_en(state_wr_en),
        .boot_wr_addr(state_wr_addr),
        .boot_wr_data(state_wr_data),
        .rd_a_addr(mem_rd_a_addr),
        .rd_a_data(mem_rd_a_data),
        .rd_a_version(mem_rd_a_ver),
        .rd_b_addr(mem_rd_b_addr),
        .rd_b_data(mem_rd_b_data),
        .rd_b_version(mem_rd_b_ver),
        .auth_check_addr(auth_check_dest_addr),
        .auth_current_version(auth_current_dest_version),
        .commit_en(mem_commit_en),
        .commit_addr(mem_commit_addr),
        .commit_data(mem_commit_data),
        .post_commit_version(post_commit_version),
        .diag_addr(8'd0),
        .diag_data(),
        .mem_reads(),
        .mem_writes()
    );

    // --- Evidence Engine ---
    logic        ev_append_req;
    logic        ev_append_ack;
    logic [31:0] ev_uow_id;
    logic [63:0] ev_pre_state_hash;
    logic [63:0] ev_post_state_hash;
    logic [63:0] ev_candidate_hash;
    logic [31:0] ev_cert_id;
    logic [31:0] ev_causal_seq;
    logic [255:0] ev_phys_root_256;
    logic [255:0] ev_sem_root_256;
    logic [63:0]  ev_sem_test_64;
    logic [63:0]  ev_current_root;
    logic [31:0]  ev_record_count;
    evidence_record_t ev_latest_record;

    geo_evidence_engine #(
        .BUFFER_DEPTH(EVIDENCE_DEPTH)
    ) u_evidence_engine (
        .clk(clk),
        .reset_n(reset_n),
        .append_req(ev_append_req),
        .uow_id(ev_uow_id),
        .pre_state_hash(ev_pre_state_hash),
        .post_state_hash(ev_post_state_hash),
        .candidate_hash(ev_candidate_hash),
        .cert_id(ev_cert_id),
        .causal_seq(ev_causal_seq),
        .append_ack(ev_append_ack),
        .engine_busy(),
        .record_count(ev_record_count),
        .latest_record(ev_latest_record),
        .physical_evidence_root_256(ev_phys_root_256),
        .semantic_evidence_root_256(ev_sem_root_256),
        .semantic_evidence_test_64(ev_sem_test_64),
        .current_evidence_root(ev_current_root)
    );

    assign current_evidence_root_out = ev_current_root;


    // --- Graph Subsystem (Section 7 & P0.5) ---
    logic        graph_query_start;
    graph_cmd_t  graph_cmd;
    graph_query_t graph_query;
    logic [15:0] graph_direct_edge_idx;
    logic        graph_neighbor_ack;
    logic        graph_busy;
    logic        graph_done;
    logic        graph_error_bounds;
    logic        graph_error_malformed;
    graph_node_t graph_out_node;
    graph_edge_t graph_out_edge;
    logic [15:0] graph_hit_count;
    logic [15:0] graph_current_neighbor;
    logic [1:0]  graph_current_distance;
    logic        graph_neighbor_valid;

    // Runtime Graph Mutation Signals (P0.7)
    logic                commit_graph_en;
    graph_mut_cmd_t      commit_graph_cmd;
    logic [15:0]         commit_graph_node;
    logic [15:0]         commit_graph_target;
    logic [7:0]          commit_graph_rel;
    logic [7:0]          commit_graph_flags;

    geo_graph_memory #(
        .MAX_NODES(GRAPH_NODES),
        .MAX_EDGES(GRAPH_EDGES),
        .QUEUE_DEPTH(GRAPH_QUEUE_DEPTH)
    ) u_graph_memory (
        .clk(clk),
        .reset_n(reset_n),
        .node_wr_en(graph_node_wr_en),
        .node_wr_addr(graph_node_wr_addr),
        .node_wr_data(graph_node_wr_data),
        .edge_wr_en(graph_edge_wr_en),
        .edge_wr_addr(graph_edge_wr_addr),
        .edge_wr_data(graph_edge_wr_data),
        .commit_graph_en(commit_graph_en),
        .commit_graph_cmd(commit_graph_cmd),
        .commit_graph_node(commit_graph_node),
        .commit_graph_target(commit_graph_target),
        .commit_graph_rel(commit_graph_rel),
        .commit_graph_flags(commit_graph_flags),
        .query_start(graph_query_start),
        .cmd(graph_cmd),
        .query(graph_query),
        .direct_edge_idx(graph_direct_edge_idx),
        .neighbor_ack(graph_neighbor_ack),
        .busy(graph_busy),
        .done(graph_done),
        .error_bounds(graph_error_bounds),
        .error_malformed(graph_error_malformed),
        .out_node(graph_out_node),
        .out_edge(graph_out_edge),
        .hit_count(graph_hit_count),
        .current_neighbor(graph_current_neighbor),
        .current_distance(graph_current_distance),
        .neighbor_valid(graph_neighbor_valid)
    );

    // --- Work Fabric ---
    logic [WORK_CELL_COUNT-1:0] fabric_committed_mask;
    logic                       fabric_all_completed;
    geo_telemetry_t             fabric_telemetry;

    geo_work_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .OPERATOR_LANES(OPERATOR_LANES),
        .MEMORY_BANKS(MEMORY_BANKS),
        .AUTHORITY_ENGINES(AUTHORITY_ENGINES),
        .INGRESS_LANES(INGRESS_LANES),
        .EGRESS_LANES(EGRESS_LANES),
        .STATE_WORDS(STATE_WORDS),
        .WIDTH(DATA_WIDTH),
        .FRAC(FRAC_BITS)
    ) u_work_fabric (
        .clk(clk),
        .reset_n(reset_n),
        .ingress_valid(ingress_valid & {INGRESS_LANES{internal_boot_complete}}),
        .ingress_ready(ingress_ready),
        .ingress_desc(ingress_desc),
        .egress_valid(egress_valid),
        .egress_ready(egress_ready),
        .egress_uow_id(egress_uow_id),
        .egress_status(egress_status),
        .egress_result(egress_result),
        .egress_evidence_root(egress_evidence_root),
        .commit_graph_en(commit_graph_en),
        .commit_graph_cmd(commit_graph_cmd),
        .commit_graph_node(commit_graph_node),
        .commit_graph_target(commit_graph_target),
        .commit_graph_rel(commit_graph_rel),
        .commit_graph_flags(commit_graph_flags),
        .mem_commit_en(mem_commit_en),
        .mem_commit_addr(mem_commit_addr),
        .mem_commit_data(mem_commit_data),
        .post_commit_version(post_commit_version),
        .mem_rd_a_addr(mem_rd_a_addr),
        .mem_rd_b_addr(mem_rd_b_addr),
        .mem_rd_a_data(mem_rd_a_data),
        .mem_rd_b_data(mem_rd_b_data),
        .mem_dest_version(mem_rd_a_ver),
        .auth_check_dest_addr(auth_check_dest_addr),
        .auth_current_dest_version(auth_current_dest_version),
        .evidence_append_req(ev_append_req),
        .ev_uow_id(ev_uow_id),
        .ev_pre_state_hash(ev_pre_state_hash),
        .ev_post_state_hash(ev_post_state_hash),
        .ev_candidate_hash(ev_candidate_hash),
        .ev_cert_id(ev_cert_id),
        .ev_causal_seq(ev_causal_seq),
        .ev_append_ack(ev_append_ack),
        .ev_current_root(ev_current_root),
        .authorized_capability_mask(fabric_capabilities),
        .graph_query_start(graph_query_start),
        .graph_cmd(graph_cmd),
        .graph_query(graph_query),
        .graph_direct_edge_idx(graph_direct_edge_idx),
        .graph_neighbor_ack(graph_neighbor_ack),
        .graph_busy(graph_busy),
        .graph_done(graph_done),
        .graph_error_bounds(graph_error_bounds),
        .graph_error_malformed(graph_error_malformed),
        .graph_out_node(graph_out_node),
        .graph_out_edge(graph_out_edge),
        .graph_hit_count(graph_hit_count),
        .graph_current_neighbor(graph_current_neighbor),
        .graph_current_distance(graph_current_distance),
        .graph_neighbor_valid(graph_neighbor_valid),
        .stall_inject_mem(stall_inject_mem),
        .stall_inject_operator(stall_inject_operator),
        .stall_inject_authority(stall_inject_authority),
        .semantic_evidence_root(semantic_evidence_root_out),
        .committed_mask(fabric_committed_mask),
        .all_work_completed(fabric_all_completed),
        .telemetry(fabric_telemetry)
    );

    assign telemetry_out         = fabric_telemetry;
    assign active_work_cells_out = fabric_committed_mask;

    // =========================================================================
    // P0.9: Integrated PSMSL Candidate Scorer Co-Processor
    // =========================================================================
    // Strictly read-only: zero memory write ports, zero authority mutation signals.
`ifdef PDI_ENABLE_ONCHIP_SCORER
    geo_psmsl_scorer #(
        .MEM_DIR("fabric_p0/rtl/scorer/")
    ) u_psmsl_scorer (
        .clk(clk),
        .rst_n(reset_n),
        .start(pdi_scorer_start),
        .cand_id_in(pdi_scorer_cand_id),
        .features_in_bus(pdi_scorer_features),
        .busy(pdi_scorer_busy),
        .done(pdi_scorer_done),
        .cand_id_out(pdi_scorer_cand_out),
        .score_out(pdi_scorer_score_out)
    );
`else
    assign pdi_scorer_busy      = 1'b0;
    assign pdi_scorer_done      = 1'b0;
    assign pdi_scorer_cand_out  = 4'd0;
    assign pdi_scorer_score_out = 32'sd0;
`endif

endmodule

`endif // MAPEOGEO_P0_FABRIC_SV
