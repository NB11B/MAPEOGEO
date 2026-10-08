// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_work_fabric
// Parameterized array of work cells with multi-lane operator dispatch, banked memory, and partitioned authority (P0.6D)

`ifndef GEO_WORK_FABRIC_SV
`define GEO_WORK_FABRIC_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_work_fabric #(
    parameter int WORK_CELL_COUNT   = 4,
    parameter int OPERATOR_LANES    = 1,
    parameter int MEMORY_BANKS      = 1,
    parameter int AUTHORITY_ENGINES = 1,
    parameter int INGRESS_LANES     = 1,
    parameter int EGRESS_LANES      = 1,
    parameter int STATE_WORDS       = 256,
    parameter int WIDTH             = 32,
    parameter int FRAC              = 16
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Work Ingress (Multi-Lane, P0.6F)
    input  logic [INGRESS_LANES-1:0]           ingress_valid,
    output logic [INGRESS_LANES-1:0]           ingress_ready,
    input  logic [INGRESS_LANES*471-1:0]       ingress_desc,

    // Result Egress (Multi-Lane, P0.6F)
    output logic [EGRESS_LANES-1:0]            egress_valid,
    input  logic [EGRESS_LANES-1:0]            egress_ready,
    output logic [EGRESS_LANES*32-1:0]         egress_uow_id,
    output logic [EGRESS_LANES*2-1:0]          egress_status,
    output logic [EGRESS_LANES*128-1:0]        egress_result,
    output logic [EGRESS_LANES*64-1:0]         egress_evidence_root,

    // Authoritative State Memory Interface (Multi-Bank, P0.6D)
    output logic [MEMORY_BANKS-1:0]             mem_commit_en,
    output logic [MEMORY_BANKS*8-1:0]           mem_commit_addr,
    output logic [MEMORY_BANKS*128-1:0]         mem_commit_data,
    input  logic [MEMORY_BANKS*16-1:0]          post_commit_version,

    output logic [MEMORY_BANKS*8-1:0]           mem_rd_a_addr,
    output logic [MEMORY_BANKS*8-1:0]           mem_rd_b_addr,
    input  logic [MEMORY_BANKS*128-1:0]         mem_rd_a_data,
    input  logic [MEMORY_BANKS*128-1:0]         mem_rd_b_data,
    input  logic [MEMORY_BANKS*16-1:0]          mem_dest_version,

    // Authority Version Inspection Port (Atomic CAS verification)
    output logic [AUTHORITY_ENGINES*8-1:0]      auth_check_dest_addr,
    input  logic [AUTHORITY_ENGINES*16-1:0]     auth_current_dest_version,

    // Evidence Engine Interface
    output logic                   evidence_append_req,
    output logic [31:0]            ev_uow_id,
    output logic [63:0]            ev_pre_state_hash,
    output logic [63:0]            ev_post_state_hash,
    output logic [63:0]            ev_candidate_hash,
    output logic [31:0]            ev_cert_id,
    output logic [31:0]            ev_causal_seq,
    input  logic                   ev_append_ack,
    input  logic [63:0]            ev_current_root,

    // Authority Configuration
    input  logic [31:0]            authorized_capability_mask,

    // Graph Memory Subsystem Interface (Section 7 & P0.5)
    output logic                   graph_query_start,
    output graph_cmd_t             graph_cmd,
    output graph_query_t           graph_query,
    output logic [15:0]            graph_direct_edge_idx,
    output logic                   graph_neighbor_ack,
    input  logic                   graph_busy,
    input  logic                   graph_done,
    input  logic                   graph_error_bounds,
    input  logic                   graph_error_malformed,
    input  graph_node_t            graph_out_node,
    input  graph_edge_t            graph_out_edge,
    input  logic [15:0]            graph_hit_count,
    input  logic [15:0]            graph_current_neighbor,
    input  logic [1:0]             graph_current_distance,
    input  logic                   graph_neighbor_valid,

    // Authoritative Runtime Graph Mutation Port (From Authority Commit to Graph Memory)
    output logic                   commit_graph_en,
    output graph_mut_cmd_t         commit_graph_cmd,
    output logic [15:0]            commit_graph_node,
    output logic [15:0]            commit_graph_target,
    output logic [7:0]             commit_graph_rel,
    output logic [7:0]             commit_graph_flags,

    // Telemetry / Status
    output logic [WORK_CELL_COUNT-1:0] committed_mask,
    output logic                       all_work_completed,
    output geo_telemetry_t             telemetry,

    // P0.8 Spatial Timing Perturbation Injection Ports
    input  logic [MEMORY_BANKS-1:0]             stall_inject_mem,
    input  logic [OPERATOR_LANES-1:0]           stall_inject_operator,
    input  logic [AUTHORITY_ENGINES-1:0]        stall_inject_authority,
    output logic [63:0]                         semantic_evidence_root
);

    // --- Work Cell Signals (Packed vectors to prevent synthesis array-flattening issues) ---
    logic [WORK_CELL_COUNT-1:0]         alloc_en;
    logic [WORK_CELL_COUNT*471-1:0]     alloc_desc;

    logic [WORK_CELL_COUNT-1:0]         cell_dispatch_req;
    logic [WORK_CELL_COUNT*6-1:0]       cell_dispatch_opcode;
    logic [WORK_CELL_COUNT*128-1:0]     cell_dispatch_op_a;
    logic [WORK_CELL_COUNT*128-1:0]     cell_dispatch_op_b;
    logic [WORK_CELL_COUNT-1:0]         cell_dispatch_ack;
    logic [WORK_CELL_COUNT-1:0]         cell_exec_done;
    logic [WORK_CELL_COUNT*128-1:0]     cell_exec_result;
    logic [WORK_CELL_COUNT-1:0]         cell_exec_overflow;

    logic [WORK_CELL_COUNT-1:0]         cell_waiting_dep;
    logic [WORK_CELL_COUNT-1:0]         cell_waiting_operator;
    logic [WORK_CELL_COUNT-1:0]         cell_waiting_auth;
    logic [WORK_CELL_COUNT-1:0]         cell_waiting_mem;

    logic [WORK_CELL_COUNT-1:0]         cell_cert_req;
    logic [WORK_CELL_COUNT*32-1:0]      cell_cert_uow_id;
    logic [WORK_CELL_COUNT*8-1:0]       cell_cert_dest_addr;
    logic [WORK_CELL_COUNT*128-1:0]     cell_cert_cand_res;
    logic [WORK_CELL_COUNT-1:0]         cell_cert_cand_ovf;
    logic [WORK_CELL_COUNT*32-1:0]      cell_cert_pre_hash;
    logic [WORK_CELL_COUNT*32-1:0]      cell_cert_auth_token;
    logic [WORK_CELL_COUNT-1:0]         cell_cert_deps_sat;
    logic [WORK_CELL_COUNT-1:0]         cell_cert_has_graph_mut;
    logic [WORK_CELL_COUNT*2-1:0]       cell_cert_graph_cmd;
    logic [WORK_CELL_COUNT*16-1:0]      cell_cert_graph_node;
    logic [WORK_CELL_COUNT*16-1:0]      cell_cert_graph_target;
    logic [WORK_CELL_COUNT*8-1:0]       cell_cert_graph_rel;
    logic [WORK_CELL_COUNT*8-1:0]       cell_cert_graph_flags;
    logic [WORK_CELL_COUNT-1:0]         cell_cert_done;
    logic [WORK_CELL_COUNT*2-1:0]       cell_cert_outcome;

    logic [WORK_CELL_COUNT-1:0]         cell_mem_rd_req;
    logic [WORK_CELL_COUNT*8-1:0]       cell_mem_rd_a_addr;
    logic [WORK_CELL_COUNT*8-1:0]       cell_mem_rd_b_addr;
    logic [WORK_CELL_COUNT*128-1:0]     cell_mem_rd_a_data;
    logic [WORK_CELL_COUNT*128-1:0]     cell_mem_rd_b_data;
    logic [WORK_CELL_COUNT-1:0]         cell_mem_rd_valid;

    // Cell Graph Query Signals (P0.5)
    logic [WORK_CELL_COUNT-1:0]         cell_graph_req;
    logic [WORK_CELL_COUNT*4-1:0]       cell_graph_cmd;
    logic [WORK_CELL_COUNT*34-1:0]      cell_graph_query;
    logic [WORK_CELL_COUNT-1:0]         cell_graph_ack;
    logic [WORK_CELL_COUNT-1:0]         cell_graph_done;
    logic [WORK_CELL_COUNT-1:0]         cell_graph_matched;

    logic [WORK_CELL_COUNT*4-1:0]       cell_state;
    logic [WORK_CELL_COUNT*32-1:0]      cell_active_uow;
    logic [WORK_CELL_COUNT*32-1:0]      cell_causal_cnt;
    logic [WORK_CELL_COUNT*2-1:0]       cell_disp;
    logic [WORK_CELL_COUNT-1:0]         cell_ready;
    logic [WORK_CELL_COUNT-1:0]         cell_active_mask;

    // Committed status register
    logic [WORK_CELL_COUNT-1:0] committed_reg;
    assign committed_mask = committed_reg;

    // Generate work-cells
    genvar c;
    generate
        for (c = 0; c < WORK_CELL_COUNT; c = c + 1) begin : gen_cells
            geo_work_cell #(
                .CELL_INDEX(c),
                .TOTAL_CELLS(WORK_CELL_COUNT)
            ) u_cell (
                .clk(clk),
                .reset_n(reset_n),
                .alloc_en(alloc_en[c]),
                .alloc_desc(alloc_desc[c*471 +: 471]),
                .global_committed_mask(committed_reg),
                .resource_available(1'b1), // Shared resources arbitrated below
                .dispatch_req(cell_dispatch_req[c]),
                .dispatch_opcode(cell_dispatch_opcode[c*6 +: 6]),
                .dispatch_op_a(cell_dispatch_op_a[c*128 +: 128]),
                .dispatch_op_b(cell_dispatch_op_b[c*128 +: 128]),
                .dispatch_ack(cell_dispatch_ack[c]),
                .exec_done(cell_exec_done[c]),
                .exec_result(cell_exec_result[c*128 +: 128]),
                .exec_overflow(cell_exec_overflow[c]),
                .cert_req(cell_cert_req[c]),
                .cert_uow_id(cell_cert_uow_id[c*32 +: 32]),
                .cert_dest_addr(cell_cert_dest_addr[c*8 +: 8]),
                .cert_candidate_result(cell_cert_cand_res[c*128 +: 128]),
                .cert_candidate_overflow(cell_cert_cand_ovf[c]),
                .cert_pre_state_hash(cell_cert_pre_hash[c*32 +: 32]),
                .cert_auth_token(cell_cert_auth_token[c*32 +: 32]),
                .cert_deps_satisfied(cell_cert_deps_sat[c]),
                .cert_has_graph_mut(cell_cert_has_graph_mut[c]),
                .cert_graph_cmd(cell_cert_graph_cmd[c*2 +: 2]),
                .cert_graph_node(cell_cert_graph_node[c*16 +: 16]),
                .cert_graph_target(cell_cert_graph_target[c*16 +: 16]),
                .cert_graph_rel(cell_cert_graph_rel[c*8 +: 8]),
                .cert_graph_flags(cell_cert_graph_flags[c*8 +: 8]),
                .cert_done(cell_cert_done[c]),
                .cert_outcome(cell_cert_outcome[c*2 +: 2]),
                .mem_rd_req(cell_mem_rd_req[c]),
                .mem_rd_a_addr(cell_mem_rd_a_addr[c*8 +: 8]),
                .mem_rd_b_addr(cell_mem_rd_b_addr[c*8 +: 8]),
                .mem_rd_a_data(cell_mem_rd_a_data[c*128 +: 128]),
                .mem_rd_b_data(cell_mem_rd_b_data[c*128 +: 128]),
                .mem_rd_valid(cell_mem_rd_valid[c]),
                .graph_req(cell_graph_req[c]),
                .graph_cmd(cell_graph_cmd[c*4 +: 4]),
                .graph_query(cell_graph_query[c*34 +: 34]),
                .graph_ack(cell_graph_ack[c]),
                .graph_done(cell_graph_done[c]),
                .graph_matched(cell_graph_matched[c]),
                .graph_hit_count(graph_hit_count),
                .graph_target_node(graph_out_edge.target_node),
                .cell_state(cell_state[c*4 +: 4]),
                .active_uow_id(cell_active_uow[c*32 +: 32]),
                .local_causal_counter(cell_causal_cnt[c*32 +: 32]),
                .terminal_disposition(cell_disp[c*2 +: 2]),
                .is_ready(cell_ready[c]),
                .is_active(cell_active_mask[c]),
                .is_waiting_dep(cell_waiting_dep[c]),
                .is_waiting_operator(cell_waiting_operator[c]),
                .is_waiting_auth(cell_waiting_auth[c]),
                .is_waiting_mem(cell_waiting_mem[c])
            );
        end
    endgenerate

    // --- Ingress Allocation Logic (Multi-Lane, P0.6F) ---
    // Finds first EMPTY or recyclable cell for each active ingress lane
    logic [WORK_CELL_COUNT-1:0] empty_cells;
    logic [WORK_CELL_COUNT-1:0] recyclable_cells;
    always_comb begin
        for (int e = 0; e < WORK_CELL_COUNT; e = e + 1) begin
            empty_cells[e]      = (cell_state[e*4 +: 4] == STATE_EMPTY);
            recyclable_cells[e] = (cell_state[e*4 +: 4] == STATE_COMMITTED || cell_state[e*4 +: 4] == STATE_REJECTED);
        end
    end

    logic [WORK_CELL_COUNT-1:0] cell_allocated_comb;
    logic [INGRESS_LANES-1:0]   lane_served;
    always_comb begin
        cell_allocated_comb = '0;
        alloc_en            = '0;
        lane_served         = '0;
        ingress_ready       = '0;
        alloc_desc          = '0;

        for (int l = 0; l < INGRESS_LANES; l = l + 1) begin
            for (int e = 0; e < WORK_CELL_COUNT; e = e + 1) begin
                if (!cell_allocated_comb[e] && !lane_served[l]) begin
                    if (empty_cells[e] || ((cell_active_mask == '0) && recyclable_cells[e])) begin
                        ingress_ready[l] = 1'b1;
                        if (ingress_valid[l]) begin
                            cell_allocated_comb[e]        = 1'b1;
                            lane_served[l]                = 1'b1;
                            alloc_en[e]                   = 1'b1;
                            alloc_desc[e*471 +: 471]      = ingress_desc[l*471 +: 471];
                        end
                    end
                end
            end
        end
    end

    // --- Multi-Bank Memory Read Arbitrator (P0.6D) ---
    // Connects pending cell read requests to matching independent memory banks in parallel
    logic [MEMORY_BANKS-1:0] bank_read_served;
    always_comb begin
        bank_read_served   = '0;
        cell_mem_rd_valid  = '0;
        mem_rd_a_addr      = '0;
        mem_rd_b_addr      = '0;
        cell_mem_rd_a_data = '0;
        cell_mem_rd_b_data = '0;

        for (int c_idx = 0; c_idx < WORK_CELL_COUNT; c_idx = c_idx + 1) begin
            if (cell_mem_rd_req[c_idx]) begin
                int req_bank;
                req_bank = cell_mem_rd_a_addr[c_idx*8 +: 8] % MEMORY_BANKS;
                if (!bank_read_served[req_bank] && !stall_inject_mem[req_bank]) begin
                    bank_read_served[req_bank]                    = 1'b1;
                    mem_rd_a_addr[req_bank*8 +: 8]                = cell_mem_rd_a_addr[c_idx*8 +: 8];
                    mem_rd_b_addr[req_bank*8 +: 8]                = cell_mem_rd_b_addr[c_idx*8 +: 8];
                    cell_mem_rd_valid[c_idx]                      = 1'b1;
                    cell_mem_rd_a_data[c_idx*128 +: 128]          = mem_rd_a_data[req_bank*128 +: 128];
                    cell_mem_rd_b_data[c_idx*128 +: 128]          = mem_rd_b_data[req_bank*128 +: 128];
                end
            end
        end
    end

    // --- Shared Functional Execution Units (Multi-Lane Datapath) ---
    logic [OPERATOR_LANES-1:0]          op_lane_start;
    logic [OPERATOR_LANES*6-1:0]        op_lane_opcode;
    logic [OPERATOR_LANES*128-1:0]      op_lane_op_a;
    logic [OPERATOR_LANES*128-1:0]      op_lane_op_b;

    logic [OPERATOR_LANES-1:0]          op_lane_done_raw;
    logic [OPERATOR_LANES*128-1:0]      op_lane_result_raw;
    logic [OPERATOR_LANES-1:0]          op_lane_overflow_raw;
    logic [OPERATOR_LANES-1:0]          op_lane_cmp_raw;

    logic [OPERATOR_LANES-1:0]          op_lane_done;
    logic [OPERATOR_LANES*128-1:0]      op_lane_result;
    logic [OPERATOR_LANES-1:0]          op_lane_overflow;
    logic [OPERATOR_LANES-1:0]          op_lane_cmp;

    logic [OPERATOR_LANES-1:0]          lane_hold_valid;
    logic [OPERATOR_LANES*128-1:0]      lane_hold_result;
    logic [OPERATOR_LANES-1:0]          lane_hold_overflow;
    logic [OPERATOR_LANES-1:0]          lane_hold_cmp;

    genvar l_idx;
    generate
        for (l_idx = 0; l_idx < OPERATOR_LANES; l_idx = l_idx + 1) begin : gen_op_lanes
            geo_operator_unit #(.WIDTH(WIDTH), .FRAC(FRAC)) u_operator (
                .clk(clk),
                .reset_n(reset_n),
                .start(op_lane_start[l_idx]),
                .opcode(op_lane_opcode[l_idx*6 +: 6]),
                .operand_a(op_lane_op_a[l_idx*128 +: 128]),
                .operand_b(op_lane_op_b[l_idx*128 +: 128]),
                .done(op_lane_done_raw[l_idx]),
                .result(op_lane_result_raw[l_idx*128 +: 128]),
                .overflow(op_lane_overflow_raw[l_idx]),
                .comparison_result(op_lane_cmp_raw[l_idx])
            );
        end
    endgenerate

    // P0.8 Operator Lane Stall Injection Skid Buffering
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            lane_hold_valid    <= '0;
            lane_hold_result   <= '0;
            lane_hold_overflow <= '0;
            lane_hold_cmp      <= '0;
        end else begin
            for (int l = 0; l < OPERATOR_LANES; l = l + 1) begin
                if (op_lane_done_raw[l] && stall_inject_operator[l]) begin
                    lane_hold_valid[l]                    <= 1'b1;
                    lane_hold_result[l*128 +: 128]        <= op_lane_result_raw[l*128 +: 128];
                    lane_hold_overflow[l]                 <= op_lane_overflow_raw[l];
                    lane_hold_cmp[l]                      <= op_lane_cmp_raw[l];
                end else if (lane_hold_valid[l] && !stall_inject_operator[l]) begin
                    lane_hold_valid[l]                    <= 1'b0;
                end
            end
        end
    end

    always_comb begin
        for (int l = 0; l < OPERATOR_LANES; l = l + 1) begin
            if (lane_hold_valid[l]) begin
                op_lane_done[l]                 = !stall_inject_operator[l];
                op_lane_result[l*128 +: 128]    = lane_hold_result[l*128 +: 128];
                op_lane_overflow[l]             = lane_hold_overflow[l];
                op_lane_cmp[l]                  = lane_hold_cmp[l];
            end else begin
                op_lane_done[l]                 = op_lane_done_raw[l] && !stall_inject_operator[l];
                op_lane_result[l*128 +: 128]    = op_lane_result_raw[l*128 +: 128];
                op_lane_overflow[l]             = op_lane_overflow_raw[l];
                op_lane_cmp[l]                  = op_lane_cmp_raw[l];
            end
        end
    end

    // Multi-Lane Operator Dispatch Arbiter
    logic [OPERATOR_LANES-1:0]                      lane_busy;
    logic [OPERATOR_LANES*WORK_CELL_COUNT-1:0]      lane_cell_mask;
    logic [OPERATOR_LANES-1:0]                      lane_dispatch_start;
    logic [OPERATOR_LANES*WORK_CELL_COUNT-1:0]      lane_dispatch_cell;

    always_comb begin
        cell_dispatch_ack   = '0;
        lane_dispatch_start = '0;
        op_lane_start       = '0;
        op_lane_opcode      = '0;
        op_lane_op_a        = '0;
        op_lane_op_b        = '0;
        lane_dispatch_cell  = '0;

        for (int d = 0; d < WORK_CELL_COUNT; d = d + 1) begin
            if (cell_dispatch_req[d]) begin
                for (int l = 0; l < OPERATOR_LANES; l = l + 1) begin
                    if (!lane_busy[l] && !lane_dispatch_start[l] && !cell_dispatch_ack[d]) begin
                        op_lane_start[l]                          = 1'b1;
                        lane_dispatch_start[l]                    = 1'b1;
                        op_lane_opcode[l*6 +: 6]                  = cell_dispatch_opcode[d*6 +: 6];
                        op_lane_op_a[l*128 +: 128]                = cell_dispatch_op_a[d*128 +: 128];
                        op_lane_op_b[l*128 +: 128]                = cell_dispatch_op_b[d*128 +: 128];
                        cell_dispatch_ack[d]                      = 1'b1;
                        lane_dispatch_cell[l*WORK_CELL_COUNT + d] = 1'b1;
                    end
                end
            end
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            lane_busy      <= '0;
            lane_cell_mask <= '0;
        end else begin
            for (int l = 0; l < OPERATOR_LANES; l = l + 1) begin
                if (lane_dispatch_start[l]) begin
                    lane_busy[l]                                          <= 1'b1;
                    lane_cell_mask[l*WORK_CELL_COUNT +: WORK_CELL_COUNT] <= lane_dispatch_cell[l*WORK_CELL_COUNT +: WORK_CELL_COUNT];
                end else if (op_lane_done[l]) begin
                    lane_busy[l]                                          <= 1'b0;
                    lane_cell_mask[l*WORK_CELL_COUNT +: WORK_CELL_COUNT] <= '0;
                end
            end
        end
    end

    always_comb begin
        cell_exec_done     = '0;
        cell_exec_result   = '0;
        cell_exec_overflow = '0;

        for (int l = 0; l < OPERATOR_LANES; l = l + 1) begin
            if (op_lane_done[l]) begin
                for (int d = 0; d < WORK_CELL_COUNT; d = d + 1) begin
                    if (lane_cell_mask[l*WORK_CELL_COUNT + d]) begin
                        cell_exec_done[d]              = 1'b1;
                        cell_exec_result[d*128 +: 128] = op_lane_result[l*128 +: 128];
                        cell_exec_overflow[d]          = op_lane_overflow[l];
                    end
                end
            end
        end
    end

    // --- Graph Query Arbiter (Section 7 & P0.5 Native Graph Work) ---
    logic [WORK_CELL_COUNT-1:0] active_graph_cell_reg;
    logic                       graph_busy_latch;
    logic                       graph_found;

    assign graph_neighbor_ack    = 1'b1;
    assign graph_direct_edge_idx = 16'd0;

    always_comb begin
        graph_query_start = 1'b0;
        graph_cmd         = GRAPH_CMD_NOP;
        graph_query       = '0;
        cell_graph_ack    = '0;
        graph_found       = 1'b0;

        if (!graph_busy && !graph_busy_latch) begin
            for (int g = 0; g < WORK_CELL_COUNT; g = g + 1) begin
                if (cell_graph_req[g] && !graph_found) begin
                    graph_query_start = 1'b1;
`ifdef SYNTHESIS
                    graph_cmd         = cell_graph_cmd[g*4 +: 4];
`else
                    graph_cmd         = graph_cmd_t'(cell_graph_cmd[g*4 +: 4]);
`endif
                    graph_query       = cell_graph_query[g*34 +: 34];
                    cell_graph_ack[g] = 1'b1;
                    graph_found       = 1'b1;
                end
            end
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            active_graph_cell_reg <= '0;
            graph_busy_latch      <= 1'b0;
        end else begin
            if (graph_query_start) begin
                active_graph_cell_reg <= cell_graph_ack;
                graph_busy_latch      <= 1'b1;
            end else if (graph_done) begin
                active_graph_cell_reg <= '0;
                graph_busy_latch      <= 1'b0;
            end
        end
    end

    assign cell_graph_done    = graph_done ? active_graph_cell_reg : '0;
    assign cell_graph_matched = (graph_hit_count > 16'd0 && !graph_error_bounds && !graph_error_malformed) ? active_graph_cell_reg : '0;

    logic [AUTHORITY_ENGINES-1:0]       auth_cert_req;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_candidate_uow_id;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_candidate_dest_addr;
    logic [AUTHORITY_ENGINES*128-1:0]   auth_candidate_result;
    logic [AUTHORITY_ENGINES-1:0]       auth_candidate_overflow;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_req_pre_state_hash;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_req_auth_token;
    logic [AUTHORITY_ENGINES-1:0]       auth_deps_all_satisfied;
    logic [AUTHORITY_ENGINES-1:0]       auth_candidate_has_graph_mut;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_candidate_graph_cmd;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_candidate_graph_node;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_candidate_graph_target;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_candidate_graph_rel;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_candidate_graph_flags;

    logic [AUTHORITY_ENGINES-1:0]       auth_cert_done_raw;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_outcome_raw;
    logic [AUTHORITY_ENGINES-1:0]       auth_commit_permit_raw;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_addr_raw;
    logic [AUTHORITY_ENGINES*128-1:0]   auth_commit_data_raw;
    logic [AUTHORITY_ENGINES-1:0]       auth_commit_graph_en_raw;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_commit_graph_cmd_raw;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_commit_graph_node_raw;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_commit_graph_target_raw;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_graph_rel_raw;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_graph_flags_raw;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_cert_id_raw;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_certified_uow_id_raw;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_failed_checks_raw;

    logic [AUTHORITY_ENGINES-1:0]       auth_cert_done;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_outcome;
    logic [AUTHORITY_ENGINES-1:0]       auth_commit_permit;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_addr;
    logic [AUTHORITY_ENGINES*128-1:0]   auth_commit_data;
    logic [AUTHORITY_ENGINES-1:0]       auth_commit_graph_en;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_commit_graph_cmd;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_commit_graph_node;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_commit_graph_target;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_graph_rel;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_commit_graph_flags;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_cert_id;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_certified_uow_id;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_failed_checks;

    logic [AUTHORITY_ENGINES-1:0]       auth_hold_valid;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_hold_outcome;
    logic [AUTHORITY_ENGINES-1:0]       auth_hold_permit;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_hold_commit_addr;
    logic [AUTHORITY_ENGINES*128-1:0]   auth_hold_commit_data;
    logic [AUTHORITY_ENGINES-1:0]       auth_hold_graph_en;
    logic [AUTHORITY_ENGINES*2-1:0]     auth_hold_graph_cmd;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_hold_graph_node;
    logic [AUTHORITY_ENGINES*16-1:0]    auth_hold_graph_target;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_hold_graph_rel;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_hold_graph_flags;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_hold_cert_id;
    logic [AUTHORITY_ENGINES*32-1:0]    auth_hold_certified_uow_id;
    logic [AUTHORITY_ENGINES*8-1:0]     auth_hold_failed_checks;

    genvar a_chk;
    generate
        for (a_chk = 0; a_chk < AUTHORITY_ENGINES; a_chk = a_chk + 1) begin : gen_auth_chk
            assign auth_check_dest_addr[a_chk*8 +: 8] = auth_candidate_dest_addr[a_chk*8 +: 8];
        end
    endgenerate

    genvar a_idx;
    generate
        for (a_idx = 0; a_idx < AUTHORITY_ENGINES; a_idx = a_idx + 1) begin : gen_auth
            geo_authority_engine #(
                .STATE_WORDS(STATE_WORDS)
            ) u_auth (
                .clk(clk),
                .reset_n(reset_n),
                .cert_req(auth_cert_req[a_idx]),
                .candidate_uow_id(auth_candidate_uow_id[a_idx*32 +: 32]),
                .candidate_dest_addr(auth_candidate_dest_addr[a_idx*8 +: 8]),
                .candidate_result(auth_candidate_result[a_idx*128 +: 128]),
                .candidate_overflow(auth_candidate_overflow[a_idx]),
                .req_pre_state_hash(auth_req_pre_state_hash[a_idx*32 +: 32]),
                .req_auth_token(auth_req_auth_token[a_idx*32 +: 32]),
                .deps_all_satisfied(auth_deps_all_satisfied[a_idx]),
                .candidate_has_graph_mut(auth_candidate_has_graph_mut[a_idx]),
                .candidate_graph_cmd(auth_candidate_graph_cmd[a_idx*2 +: 2]),
                .candidate_graph_node(auth_candidate_graph_node[a_idx*16 +: 16]),
                .candidate_graph_target(auth_candidate_graph_target[a_idx*16 +: 16]),
                .candidate_graph_rel(auth_candidate_graph_rel[a_idx*8 +: 8]),
                .candidate_graph_flags(auth_candidate_graph_flags[a_idx*8 +: 8]),
                .actual_pre_state_hash(32'd0),
                .read_dest_version(auth_req_pre_state_hash[a_idx*32 +: 16]),
                .current_dest_version(auth_current_dest_version[a_idx*16 +: 16]),
                .authorized_capability_mask(authorized_capability_mask),
                .cert_done(auth_cert_done_raw[a_idx]),
                .outcome(auth_outcome_raw[a_idx*2 +: 2]),
                .commit_permit(auth_commit_permit_raw[a_idx]),
                .commit_addr(auth_commit_addr_raw[a_idx*8 +: 8]),
                .commit_data(auth_commit_data_raw[a_idx*128 +: 128]),
                .commit_graph_en(auth_commit_graph_en_raw[a_idx]),
                .commit_graph_cmd(auth_commit_graph_cmd_raw[a_idx*2 +: 2]),
                .commit_graph_node(auth_commit_graph_node_raw[a_idx*16 +: 16]),
                .commit_graph_target(auth_commit_graph_target_raw[a_idx*16 +: 16]),
                .commit_graph_rel(auth_commit_graph_rel_raw[a_idx*8 +: 8]),
                .commit_graph_flags(auth_commit_graph_flags_raw[a_idx*8 +: 8]),
                .cert_id(auth_cert_id_raw[a_idx*32 +: 32]),
                .certified_uow_id(auth_certified_uow_id_raw[a_idx*32 +: 32]),
                .failed_check_mask(auth_failed_checks_raw[a_idx*8 +: 8])
            );
        end
    endgenerate

    // P0.8 Authority Engine Stall Injection Skid Buffering
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            auth_hold_valid            <= '0;
            auth_hold_outcome          <= '0;
            auth_hold_permit           <= '0;
            auth_hold_commit_addr      <= '0;
            auth_hold_commit_data      <= '0;
            auth_hold_graph_en         <= '0;
            auth_hold_graph_cmd        <= '0;
            auth_hold_graph_node       <= '0;
            auth_hold_graph_target     <= '0;
            auth_hold_graph_rel        <= '0;
            auth_hold_graph_flags      <= '0;
            auth_hold_cert_id          <= '0;
            auth_hold_certified_uow_id <= '0;
            auth_hold_failed_checks    <= '0;
        end else begin
            for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
                if (auth_cert_done_raw[a] && stall_inject_authority[a]) begin
                    auth_hold_valid[a]                     <= 1'b1;
                    auth_hold_outcome[a*2 +: 2]            <= auth_outcome_raw[a*2 +: 2];
                    auth_hold_permit[a]                    <= auth_commit_permit_raw[a];
                    auth_hold_commit_addr[a*8 +: 8]        <= auth_commit_addr_raw[a*8 +: 8];
                    auth_hold_commit_data[a*128 +: 128]    <= auth_commit_data_raw[a*128 +: 128];
                    auth_hold_graph_en[a]                  <= auth_commit_graph_en_raw[a];
                    auth_hold_graph_cmd[a*2 +: 2]          <= auth_commit_graph_cmd_raw[a*2 +: 2];
                    auth_hold_graph_node[a*16 +: 16]       <= auth_commit_graph_node_raw[a*16 +: 16];
                    auth_hold_graph_target[a*16 +: 16]     <= auth_commit_graph_target_raw[a*16 +: 16];
                    auth_hold_graph_rel[a*8 +: 8]          <= auth_commit_graph_rel_raw[a*8 +: 8];
                    auth_hold_graph_flags[a*8 +: 8]        <= auth_commit_graph_flags_raw[a*8 +: 8];
                    auth_hold_cert_id[a*32 +: 32]          <= auth_cert_id_raw[a*32 +: 32];
                    auth_hold_certified_uow_id[a*32 +: 32] <= auth_certified_uow_id_raw[a*32 +: 32];
                    auth_hold_failed_checks[a*8 +: 8]      <= auth_failed_checks_raw[a*8 +: 8];
                end else if (auth_hold_valid[a] && !stall_inject_authority[a]) begin
                    auth_hold_valid[a]                     <= 1'b0;
                end
            end
        end
    end

    always_comb begin
        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            if (auth_hold_valid[a]) begin
                auth_cert_done[a]                        = !stall_inject_authority[a];
                auth_outcome[a*2 +: 2]                   = auth_hold_outcome[a*2 +: 2];
                auth_commit_permit[a]                    = auth_hold_permit[a] && !stall_inject_authority[a];
                auth_commit_addr[a*8 +: 8]               = auth_hold_commit_addr[a*8 +: 8];
                auth_commit_data[a*128 +: 128]           = auth_hold_commit_data[a*128 +: 128];
                auth_commit_graph_en[a]                  = auth_hold_graph_en[a] && !stall_inject_authority[a];
                auth_commit_graph_cmd[a*2 +: 2]          = auth_hold_graph_cmd[a*2 +: 2];
                auth_commit_graph_node[a*16 +: 16]       = auth_hold_graph_node[a*16 +: 16];
                auth_commit_graph_target[a*16 +: 16]     = auth_hold_graph_target[a*16 +: 16];
                auth_commit_graph_rel[a*8 +: 8]          = auth_hold_graph_rel[a*8 +: 8];
                auth_commit_graph_flags[a*8 +: 8]        = auth_hold_graph_flags[a*8 +: 8];
                auth_cert_id[a*32 +: 32]                 = auth_hold_cert_id[a*32 +: 32];
                auth_certified_uow_id[a*32 +: 32]        = auth_hold_certified_uow_id[a*32 +: 32];
                auth_failed_checks[a*8 +: 8]             = auth_hold_failed_checks[a*8 +: 8];
            end else begin
                auth_cert_done[a]                        = auth_cert_done_raw[a] && !stall_inject_authority[a];
                auth_outcome[a*2 +: 2]                   = auth_outcome_raw[a*2 +: 2];
                auth_commit_permit[a]                    = auth_commit_permit_raw[a] && !stall_inject_authority[a];
                auth_commit_addr[a*8 +: 8]               = auth_commit_addr_raw[a*8 +: 8];
                auth_commit_data[a*128 +: 128]           = auth_commit_data_raw[a*128 +: 128];
                auth_commit_graph_en[a]                  = auth_commit_graph_en_raw[a] && !stall_inject_authority[a];
                auth_commit_graph_cmd[a*2 +: 2]          = auth_commit_graph_cmd_raw[a*2 +: 2];
                auth_commit_graph_node[a*16 +: 16]       = auth_commit_graph_node_raw[a*16 +: 16];
                auth_commit_graph_target[a*16 +: 16]     = auth_commit_graph_target_raw[a*16 +: 16];
                auth_commit_graph_rel[a*8 +: 8]          = auth_commit_graph_rel_raw[a*8 +: 8];
                auth_commit_graph_flags[a*8 +: 8]        = auth_commit_graph_flags_raw[a*8 +: 8];
                auth_cert_id[a*32 +: 32]                 = auth_cert_id_raw[a*32 +: 32];
                auth_certified_uow_id[a*32 +: 32]        = auth_certified_uow_id_raw[a*32 +: 32];
                auth_failed_checks[a*8 +: 8]             = auth_failed_checks_raw[a*8 +: 8];
            end
        end
    end

    // Domain-Partitioned Authority Arbiter:
    logic [AUTHORITY_ENGINES-1:0]                 engine_busy;
    logic [AUTHORITY_ENGINES*WORK_CELL_COUNT-1:0] engine_eval_cell;
    logic [AUTHORITY_ENGINES*WORK_CELL_COUNT-1:0] certifying_cell_reg;

    always_comb begin
        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            engine_busy[a] = auth_hold_valid[a] || stall_inject_authority[a];
        end
    end

    always_comb begin
        auth_cert_req                = '0;
        auth_candidate_overflow      = '0;
        auth_deps_all_satisfied      = '0;
        auth_candidate_has_graph_mut = '0;
        auth_candidate_uow_id        = '0;
        auth_candidate_dest_addr     = '0;
        auth_candidate_result        = '0;
        auth_req_pre_state_hash      = '0;
        auth_req_auth_token          = '0;
        auth_candidate_graph_cmd     = '0;
        auth_candidate_graph_node    = '0;
        auth_candidate_graph_target  = '0;
        auth_candidate_graph_rel     = '0;
        auth_candidate_graph_flags   = '0;
        engine_eval_cell             = '0;

        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            for (int c = 0; c < WORK_CELL_COUNT; c = c + 1) begin
                if (cell_cert_req[c] && !cell_cert_done[c] && !engine_busy[a]) begin
                    if ((cell_cert_dest_addr[c*8 +: 8] % AUTHORITY_ENGINES) == a) begin
                        if (!auth_cert_req[a]) begin
                            auth_cert_req[a]                               = 1'b1;
                            auth_candidate_uow_id[a*32 +: 32]              = cell_cert_uow_id[c*32 +: 32];
                            auth_candidate_dest_addr[a*8 +: 8]             = cell_cert_dest_addr[c*8 +: 8];
                            auth_candidate_result[a*128 +: 128]            = cell_cert_cand_res[c*128 +: 128];
                            auth_candidate_overflow[a]                     = cell_cert_cand_ovf[c];
                            auth_req_pre_state_hash[a*32 +: 32]            = cell_cert_pre_hash[c*32 +: 32];
                            auth_req_auth_token[a*32 +: 32]                = cell_cert_auth_token[c*32 +: 32];
                            auth_deps_all_satisfied[a]                     = cell_cert_deps_sat[c];
                            auth_candidate_has_graph_mut[a]                = cell_cert_has_graph_mut[c];
                            auth_candidate_graph_cmd[a*2 +: 2]             = cell_cert_graph_cmd[c*2 +: 2];
                            auth_candidate_graph_node[a*16 +: 16]          = cell_cert_graph_node[c*16 +: 16];
                            auth_candidate_graph_target[a*16 +: 16]        = cell_cert_graph_target[c*16 +: 16];
                            auth_candidate_graph_rel[a*8 +: 8]             = cell_cert_graph_rel[c*8 +: 8];
                            auth_candidate_graph_flags[a*8 +: 8]           = cell_cert_graph_flags[c*8 +: 8];
                            engine_eval_cell[a*WORK_CELL_COUNT + c]        = 1'b1;
                        end
                    end
                end
            end
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            certifying_cell_reg <= '0;
        end else begin
            for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
                if (auth_cert_req[a]) begin
                    certifying_cell_reg[a*WORK_CELL_COUNT +: WORK_CELL_COUNT] <= engine_eval_cell[a*WORK_CELL_COUNT +: WORK_CELL_COUNT];
                end else if (auth_cert_done[a]) begin
                    certifying_cell_reg[a*WORK_CELL_COUNT +: WORK_CELL_COUNT] <= '0;
                end
            end
        end
    end

    always_comb begin
        cell_cert_done    = '0;
        cell_cert_outcome = '0;
        for (int c_idx = 0; c_idx < WORK_CELL_COUNT; c_idx = c_idx + 1) begin
            cell_cert_outcome[c_idx*2 +: 2] = OUTCOME_REJECT;
        end
        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            if (auth_cert_done[a]) begin
                for (int c_idx = 0; c_idx < WORK_CELL_COUNT; c_idx = c_idx + 1) begin
                    if (certifying_cell_reg[a*WORK_CELL_COUNT + c_idx]) begin
                        cell_cert_done[c_idx]           = 1'b1;
                        cell_cert_outcome[c_idx*2 +: 2] = auth_outcome[a*2 +: 2];
                    end
                end
            end
        end
    end

    // Multi-Bank Memory Commit Routing
    always_comb begin
        mem_commit_en   = '0;
        mem_commit_addr = '0;
        mem_commit_data = '0;

        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            if (auth_commit_permit[a]) begin
                int b_dest;
                b_dest = auth_commit_addr[a*8 +: 8] % MEMORY_BANKS;
                if (!mem_commit_en[b_dest]) begin
                    mem_commit_en[b_dest]              = 1'b1;
                    mem_commit_addr[b_dest*8 +: 8]     = auth_commit_addr[a*8 +: 8];
                    mem_commit_data[b_dest*128 +: 128] = auth_commit_data[a*128 +: 128];
                end
            end
        end
    end

    // Graph mutation commit routing (single graph commit port)
    always_comb begin
        commit_graph_en     = 1'b0;
        commit_graph_cmd    = GRAPH_MUT_NOP;
        commit_graph_node   = '0;
        commit_graph_target = '0;
        commit_graph_rel    = '0;
        commit_graph_flags  = '0;
        for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
            if (auth_commit_graph_en[a] && !commit_graph_en) begin
                commit_graph_en     = 1'b1;
`ifdef SYNTHESIS
                commit_graph_cmd    = auth_commit_graph_cmd[a*2 +: 2];
`else
                commit_graph_cmd    = graph_mut_cmd_t'(auth_commit_graph_cmd[a*2 +: 2]);
`endif
                commit_graph_node   = auth_commit_graph_node[a*16 +: 16];
                commit_graph_target = auth_commit_graph_target[a*16 +: 16];
                commit_graph_rel    = auth_commit_graph_rel[a*8 +: 8];
                commit_graph_flags  = auth_commit_graph_flags[a*8 +: 8];
            end
        end
    end

    // Multi-lane completion aggregation
    logic [7:0] lane_done_count;
    logic [7:0] lane_overflow_count;
    always_comb begin
        lane_done_count     = '0;
        lane_overflow_count = '0;
        for (int l_c = 0; l_c < OPERATOR_LANES; l_c = l_c + 1) begin
            if (op_lane_done[l_c]) begin
                lane_done_count = lane_done_count + 1'b1;
                if (op_lane_overflow[l_c]) begin
                    lane_overflow_count = lane_overflow_count + 1'b1;
                end
            end
        end
    end

    // Multi-engine commit and memory read counting
    logic [7:0] engine_commit_count;
    logic [7:0] active_read_banks;
    logic [7:0] active_write_banks;
    always_comb begin
        engine_commit_count = '0;
        active_read_banks   = '0;
        active_write_banks  = '0;
        for (int a_c = 0; a_c < AUTHORITY_ENGINES; a_c = a_c + 1) begin
            if (auth_cert_done[a_c] && (auth_outcome[a_c*2 +: 2] == OUTCOME_COMMIT)) begin
                engine_commit_count = engine_commit_count + 1'b1;
            end
        end
        for (int b_c = 0; b_c < MEMORY_BANKS; b_c = b_c + 1) begin
            if (bank_read_served[b_c]) active_read_banks  = active_read_banks + 1'b1;
            if (mem_commit_en[b_c])    active_write_banks = active_write_banks + 1'b1;
        end
    end

    // Real-time cell occupancy
    logic [31:0] current_occupancy;
    always_comb begin
        current_occupancy = '0;
        for (int o_idx = 0; o_idx < WORK_CELL_COUNT; o_idx = o_idx + 1) begin
            if (cell_active_mask[o_idx]) begin
                current_occupancy = current_occupancy + 1'b1;
            end
        end
    end

    // Egress and Evidence Queue (Buffers completions from multi-engine parallel commits)
    localparam int CMPL_DEPTH = 64;
    logic [31:0]       cmpl_uow_id    [0:CMPL_DEPTH-1];
    logic [1:0]        cmpl_status    [0:CMPL_DEPTH-1];
    logic [127:0]      cmpl_result    [0:CMPL_DEPTH-1];
    logic [31:0]       cmpl_cert_id   [0:CMPL_DEPTH-1];
    logic [5:0]        cmpl_wr_ptr;
    logic [5:0]        cmpl_rd_ptr;
    logic [6:0]        cmpl_count;

    // Committed status register & Telemetry tracking
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            committed_reg             <= '0;
            egress_valid              <= '0;
            egress_uow_id             <= '0;
            egress_status             <= '0;
            egress_result             <= '0;
            egress_evidence_root      <= '0;
            semantic_evidence_root    <= 64'hC0FFEE_D00D_FEED;
            evidence_append_req       <= 1'b0;
            ev_uow_id                 <= '0;
            ev_pre_state_hash         <= '0;
            ev_post_state_hash        <= '0;
            ev_candidate_hash         <= '0;
            ev_cert_id                <= '0;
            ev_causal_seq             <= '0;
            cmpl_wr_ptr               <= '0;
            cmpl_rd_ptr               <= '0;
            cmpl_count                <= '0;
            telemetry.cycles          <= '0;
            telemetry.uow_admitted    <= '0;
            telemetry.uow_committed   <= '0;
            telemetry.uow_rejected    <= '0;
            telemetry.uow_refused     <= '0;
            telemetry.ops_executed    <= '0;
            telemetry.op_stalls       <= '0;
            telemetry.mem_reads       <= '0;
            telemetry.mem_writes      <= '0;
            telemetry.evidence_records<= '0;
            telemetry.overflow_events <= '0;
            telemetry.fault_events    <= '0;
            telemetry.stall_operator_wait  <= '0;
            telemetry.stall_dep_wait       <= '0;
            telemetry.stall_auth_wait      <= '0;
            telemetry.stall_mem_wait       <= '0;
            telemetry.peak_queue_occupancy <= '0;
            telemetry.backpressure_cycles  <= '0;
        end else begin
            telemetry.cycles <= telemetry.cycles + 1'b1;

            begin
                int admitted_cnt;
                admitted_cnt = 0;
                for (int l = 0; l < INGRESS_LANES; l = l + 1) begin
                    if (ingress_valid[l] && ingress_ready[l]) begin
                        admitted_cnt = admitted_cnt + 1;
                    end
                end
                telemetry.uow_admitted <= telemetry.uow_admitted + admitted_cnt;
                if ((admitted_cnt > 0) && (cell_active_mask == '0) && !(|empty_cells)) begin
                    committed_reg <= '0;
                end
            end

            // Banked Memory activity counters
            if (|active_read_banks) begin
                telemetry.mem_reads <= telemetry.mem_reads + {24'd0, active_read_banks};
            end
            if (|active_write_banks) begin
                telemetry.mem_writes <= telemetry.mem_writes + {24'd0, active_write_banks};
            end

            // Operator execution and overflow counters (Multi-Lane)
            if (|lane_done_count) begin
                telemetry.ops_executed <= telemetry.ops_executed + {24'd0, lane_done_count};
            end
            if (|lane_overflow_count) begin
                telemetry.overflow_events <= telemetry.overflow_events + {24'd0, lane_overflow_count};
            end

            // Capacity & Stall Profiling
            if (|cell_waiting_operator) begin
                telemetry.op_stalls           <= telemetry.op_stalls + 1'b1;
                telemetry.stall_operator_wait <= telemetry.stall_operator_wait + 1'b1;
            end
            if (|cell_waiting_dep) begin
                telemetry.stall_dep_wait <= telemetry.stall_dep_wait + 1'b1;
            end
            if (|cell_waiting_auth) begin
                telemetry.stall_auth_wait <= telemetry.stall_auth_wait + 1'b1;
            end
            if (|cell_waiting_mem) begin
                telemetry.stall_mem_wait <= telemetry.stall_mem_wait + 1'b1;
            end

            // Backpressure & Queue occupancy
            if ((|ingress_valid) && !(&ingress_ready)) begin
                telemetry.backpressure_cycles <= telemetry.backpressure_cycles + 1'b1;
            end
            if (current_occupancy > telemetry.peak_queue_occupancy) begin
                telemetry.peak_queue_occupancy <= current_occupancy;
            end

            evidence_append_req <= 1'b0;

            // Enqueue completed UoWs from Authority Engines
            begin
                logic [5:0]  push_count;
                int          pop_count;
                int          commits_this_cycle;
                int          rejects_this_cycle;
                int          refuses_this_cycle;
                int          faults_this_cycle;
                logic [63:0] cycle_semantic_xor;
                push_count         = '0;
                pop_count          = 0;
                commits_this_cycle = 0;
                rejects_this_cycle = 0;
                refuses_this_cycle = 0;
                faults_this_cycle  = 0;
                cycle_semantic_xor = '0;

                for (int a = 0; a < AUTHORITY_ENGINES; a = a + 1) begin
                    if (auth_cert_done[a]) begin
                        logic [5:0] slot;
                        slot = (cmpl_wr_ptr + push_count) % CMPL_DEPTH;
                        case (auth_outcome[a*2 +: 2])
                            OUTCOME_COMMIT: begin
                                logic [127:0] a_data;
                                logic [63:0]  commit_fingerprint;
                                a_data = auth_commit_data[a*128 +: 128];
                                commit_fingerprint = {auth_certified_uow_id[a*32 +: 32], auth_commit_addr[a*8 +: 8], 24'h5A5A5A} ^
                                                     a_data[127:64] ^
                                                     a_data[63:0];
                                cycle_semantic_xor = cycle_semantic_xor ^ commit_fingerprint;
                                commits_this_cycle = commits_this_cycle + 1;
                                for (int k = 0; k < WORK_CELL_COUNT; k = k + 1) begin
                                    if (certifying_cell_reg[a*WORK_CELL_COUNT + k]) begin
                                        committed_reg[k] <= 1'b1;
                                    end
                                end
                                evidence_append_req <= 1'b1;
                                ev_uow_id           <= auth_certified_uow_id[a*32 +: 32];
                                ev_pre_state_hash   <= 64'd0;
                                ev_post_state_hash  <= 64'd0;
                                ev_candidate_hash   <= a_data[127:64];
                                ev_cert_id          <= auth_cert_id[a*32 +: 32];
                                ev_causal_seq       <= telemetry.uow_committed + commits_this_cycle;
                            end
                            OUTCOME_REJECT: rejects_this_cycle = rejects_this_cycle + 1;
                            OUTCOME_REFUSE: refuses_this_cycle = refuses_this_cycle + 1;
                            OUTCOME_FAULT:  faults_this_cycle  = faults_this_cycle + 1;
                        endcase

                        cmpl_uow_id[slot]  <= auth_certified_uow_id[a*32 +: 32];
                        cmpl_status[slot]  <= auth_outcome[a*2 +: 2];
                        cmpl_result[slot]  <= auth_commit_data[a*128 +: 128];
                        cmpl_cert_id[slot] <= auth_cert_id[a*32 +: 32];
                        push_count         = push_count + 1'b1;
                    end
                end

                semantic_evidence_root  <= semantic_evidence_root ^ cycle_semantic_xor;
                telemetry.uow_committed <= telemetry.uow_committed + commits_this_cycle;
                telemetry.uow_rejected  <= telemetry.uow_rejected  + rejects_this_cycle;
                telemetry.uow_refused   <= telemetry.uow_refused   + refuses_this_cycle;
                telemetry.fault_events  <= telemetry.fault_events  + faults_this_cycle;

                // Determine in-order multi-lane dequeue count
                for (int k = 0; k < EGRESS_LANES; k = k + 1) begin
                    if ((k < cmpl_count) && (!egress_valid[k] || egress_ready[k])) begin
                        if (pop_count == k) begin
                            pop_count = pop_count + 1;
                        end
                    end
                end

                // Dequeue to Multi-Lane Egress Stream
                for (int k = 0; k < EGRESS_LANES; k = k + 1) begin
                    if (k < pop_count) begin
                        logic [5:0] rslot;
                        rslot = (cmpl_rd_ptr + k) % CMPL_DEPTH;
                        egress_valid[k]                  <= 1'b1;
                        egress_uow_id[k*32 +: 32]        <= cmpl_uow_id[rslot];
                        egress_status[k*2 +: 2]          <= cmpl_status[rslot];
                        egress_result[k*128 +: 128]      <= cmpl_result[rslot];
                        egress_evidence_root[k*64 +: 64] <= ev_current_root;
                    end else if (egress_ready[k] && egress_valid[k]) begin
                        egress_valid[k]                  <= 1'b0;
                    end
                end

                // Synchronous update of wr_ptr, rd_ptr and occupancy count
                cmpl_wr_ptr <= (cmpl_wr_ptr + push_count) % CMPL_DEPTH;
                cmpl_rd_ptr <= (cmpl_rd_ptr + pop_count[5:0]) % CMPL_DEPTH;
                cmpl_count  <= cmpl_count + {1'b0, push_count} - pop_count[6:0];
            end

            if (ev_append_ack) begin
                telemetry.evidence_records <= telemetry.evidence_records + 1'b1;
            end
        end
    end

    // All work completed indicator
    assign all_work_completed = (telemetry.uow_admitted > 0) && (cell_active_mask == '0) && (cmpl_count == 0);

endmodule

`endif // GEO_WORK_FABRIC_SV
