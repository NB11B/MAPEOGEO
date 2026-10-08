// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_work_cell
// Autonomous hardware work-cell maintaining UoW lifecycle, causal dependencies, and local state

`ifndef GEO_WORK_CELL_SV
`define GEO_WORK_CELL_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_work_cell #(
    parameter int CELL_INDEX = 0,
    parameter int TOTAL_CELLS = 4
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Work Ingress / Allocation
    input  logic                   alloc_en,
    input  uow_desc_t              alloc_desc,

    // Global Fabric Dependency Status
    input  logic [TOTAL_CELLS-1:0] global_committed_mask,
    input  logic                   resource_available, // R_available from scheduler

    // Operator Execution Interface
    output logic                   dispatch_req,
    output geo_opcode_t            dispatch_opcode,
    output cl20_mv_t               dispatch_op_a,
    output cl20_mv_t               dispatch_op_b,
    input  logic                   dispatch_ack,
    input  logic                   exec_done,
    input  cl20_mv_t               exec_result,
    input  logic                   exec_overflow,

    // Authority Interface
    output logic                   cert_req,
    output logic [31:0]            cert_uow_id,
    output logic [7:0]             cert_dest_addr,
    output cl20_mv_t               cert_candidate_result,
    output logic                   cert_candidate_overflow,
    output logic [31:0]            cert_pre_state_hash,
    output logic [31:0]            cert_auth_token,
    output logic                   cert_deps_satisfied,
    output logic                   cert_has_graph_mut,
    output graph_mut_cmd_t         cert_graph_cmd,
    output logic [15:0]            cert_graph_node,
    output logic [15:0]            cert_graph_target,
    output logic [7:0]             cert_graph_rel,
    output logic [7:0]             cert_graph_flags,
    input  logic                   cert_done,
    input  commit_outcome_t        cert_outcome,

    // State Memory Read Handshake (to populate operands)
    output logic                   mem_rd_req,
    output logic [7:0]             mem_rd_a_addr,
    output logic [7:0]             mem_rd_b_addr,
    input  cl20_mv_t               mem_rd_a_data,
    input  cl20_mv_t               mem_rd_b_data,
    input  logic                   mem_rd_valid,

    // Graph Query Interface (Section 7 & P0.5 Native Graph Work)
    output logic                   graph_req,
    output graph_cmd_t             graph_cmd,
    output graph_query_t           graph_query,
    input  logic                   graph_ack,
    input  logic                   graph_done,
    input  logic                   graph_matched,
    input  logic [15:0]            graph_hit_count,
    input  logic [15:0]            graph_target_node,

    // Status / Inspection
    output work_state_t            cell_state,
    output logic [31:0]            active_uow_id,
    output logic [31:0]            local_causal_counter,
    output commit_outcome_t        terminal_disposition,
    output logic                   is_ready,
    output logic                   is_active,
    output logic                   is_waiting_dep,
    output logic                   is_waiting_operator,
    output logic                   is_waiting_auth,
    output logic                   is_waiting_mem
);

    // --- Cell Internal Registers ---
    uow_desc_t       desc_reg;
    work_state_t     state_reg;
    logic [31:0]     causal_cnt;
    cl20_mv_t        op_a_reg;
    cl20_mv_t        op_b_reg;
    logic [1:0]      op_ready;
    cl20_mv_t        cand_res_reg;
    logic            cand_ovf_reg;
    commit_outcome_t disp_reg;
    logic            graph_query_active;

    assign cell_state            = state_reg;
    assign active_uow_id         = desc_reg.uow_id;
    assign local_causal_counter  = causal_cnt;
    assign terminal_disposition  = disp_reg;
    assign is_active             = (state_reg != STATE_EMPTY &&
                                    state_reg != STATE_COMMITTED &&
                                    state_reg != STATE_REJECTED &&
                                    state_reg != STATE_FAULT &&
                                    state_reg != STATE_HALTED);

    // --- Dependency & Boundary Predicates (Section 4.3) ---
    // D_satisfied: all dependent cells in the bitmask have COMMITTED
    logic d_satisfied;
    assign d_satisfied = ((desc_reg.dep_mask[TOTAL_CELLS-1:0] & global_committed_mask) == desc_reg.dep_mask[TOTAL_CELLS-1:0]);

    // B_satisfied: operands are ready and valid destination declared
    logic b_satisfied;
    assign b_satisfied = (op_ready == 2'b11);

    // R_available: passed from dispatch arbiter
    logic ready_cond;
    assign ready_cond = d_satisfied && resource_available && b_satisfied;
    assign is_ready   = (state_reg == STATE_READY);

    // Diagnostic stall indicators
    assign is_waiting_dep      = (state_reg == STATE_WAIT_DEPENDENCY);
    assign is_waiting_operator = (state_reg == STATE_READY);
    assign is_waiting_auth     = (state_reg == STATE_RESULT_PENDING || state_reg == STATE_CERTIFYING);
    assign is_waiting_mem      = (state_reg == STATE_LOADED && op_ready != 2'b11);

    // Memory read address outputs
    assign mem_rd_a_addr = desc_reg.src_a_addr;
    assign mem_rd_b_addr = desc_reg.src_b_addr;

    // Operator dispatch outputs
    assign dispatch_opcode = desc_reg.opcode;
    assign dispatch_op_a   = op_a_reg;
    assign dispatch_op_b   = desc_reg.use_immediate ? desc_reg.imm_operand : op_b_reg;

    // Authority certification outputs
    logic graph_cond_satisfied;
    assign cert_uow_id             = desc_reg.uow_id;
    assign cert_dest_addr          = desc_reg.dest_addr;
    assign cert_candidate_result   = cand_res_reg;
    assign cert_candidate_overflow = cand_ovf_reg;
    assign cert_pre_state_hash     = desc_reg.pre_state_hash;
    assign cert_auth_token         = desc_reg.auth_token;
    assign cert_deps_satisfied     = d_satisfied && graph_cond_satisfied;
    assign cert_has_graph_mut      = desc_reg.has_graph_mut;
    assign cert_graph_cmd          = desc_reg.graph_mut_cmd;
    assign cert_graph_node         = desc_reg.graph_mut_node;
    assign cert_graph_target       = desc_reg.graph_mut_target;
    assign cert_graph_rel          = desc_reg.graph_mut_rel;
    assign cert_graph_flags        = desc_reg.graph_mut_flags;

    // --- State Machine Transitions (Deterministic, Section 4.2) ---
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state_reg            <= STATE_EMPTY;
            desc_reg             <= '0;
            causal_cnt           <= '0;
            op_a_reg             <= '0;
            op_b_reg             <= '0;
            op_ready             <= 2'b00;
            cand_res_reg         <= '0;
            cand_ovf_reg         <= 1'b0;
            disp_reg             <= OUTCOME_REJECT;
            dispatch_req         <= 1'b0;
            cert_req             <= 1'b0;
            mem_rd_req           <= 1'b0;
            graph_req            <= 1'b0;
            graph_cmd            <= GRAPH_CMD_NOP;
            graph_query          <= '0;
            graph_query_active   <= 1'b0;
            graph_cond_satisfied <= 1'b1;
        end else begin
            case (state_reg)
                STATE_EMPTY, STATE_COMMITTED, STATE_REJECTED: begin
                    dispatch_req         <= 1'b0;
                    cert_req             <= 1'b0;
                    mem_rd_req           <= 1'b0;
                    graph_req            <= 1'b0;
                    graph_query_active   <= 1'b0;
                    graph_cond_satisfied <= 1'b1;
                    if (alloc_en) begin
                        desc_reg   <= alloc_desc;
                        causal_cnt <= causal_cnt + 1'b1;
                        op_ready   <= 2'b00;
                        if (alloc_desc.dep_cond == DEP_COND_BITMASK) begin
                            if ((alloc_desc.dep_mask[TOTAL_CELLS-1:0] & global_committed_mask) == alloc_desc.dep_mask[TOTAL_CELLS-1:0]) begin
                                // Dependencies already satisfied
                                mem_rd_req <= 1'b1;
                                state_reg  <= STATE_LOADED;
                            end else begin
                                // Wait for upstream dependencies to commit before reading state
                                mem_rd_req <= 1'b0;
                                state_reg  <= STATE_WAIT_DEPENDENCY;
                            end
                        end else begin
                            // Graph-derived condition (P0.5)
                            mem_rd_req <= 1'b0;
                            state_reg  <= STATE_WAIT_DEPENDENCY;
                        end
                    end
                end

                STATE_WAIT_DEPENDENCY: begin
                    if (desc_reg.dep_cond == DEP_COND_BITMASK) begin
                        if (d_satisfied) begin
                            mem_rd_req <= 1'b1; // Fetch freshly committed operands
                            state_reg  <= STATE_LOADED;
                        end
                    end else begin
                        // Graph-derived condition (P0.5)
                        if (d_satisfied) begin
                            if (!graph_query_active) begin
                                if (graph_ack) begin
                                    graph_req          <= 1'b0;
                                    graph_query_active <= 1'b1;
                                end else begin
                                    graph_req   <= 1'b1;
                                    graph_query <= desc_reg.graph_query;
                                    case (desc_reg.dep_cond)
                                        DEP_COND_RELATION_EXISTS:  graph_cmd <= GRAPH_CMD_RELATION_MATCH;
                                        DEP_COND_CAPABILITY_MATCH: graph_cmd <= GRAPH_CMD_NODE_TYPE_MATCH;
                                        DEP_COND_RELATION_FILTER:  graph_cmd <= GRAPH_CMD_RELATION_MATCH;
                                        DEP_COND_NEIGHBOR_EXPAND:  graph_cmd <= GRAPH_CMD_NEIGHBORHOOD_BEGIN;
                                        default:                   graph_cmd <= GRAPH_CMD_RELATION_MATCH;
                                    endcase
                                end
                            end else begin
                                graph_req <= 1'b0;
                                if (graph_done) begin
                                    graph_query_active <= 1'b0;
                                    if (graph_matched) begin
                                        graph_cond_satisfied <= 1'b1;
                                        mem_rd_req           <= 1'b1;
                                        state_reg            <= STATE_LOADED;
                                    end else begin
                                        // Relation does not exist: route to Authority for certified rejection
                                        graph_cond_satisfied <= 1'b0;
                                        cand_res_reg         <= '0;
                                        cand_ovf_reg         <= 1'b0;
                                        state_reg            <= STATE_RESULT_PENDING;
                                    end
                                end
                            end
                        end
                    end
                end

                STATE_LOADED: begin
                    if (mem_rd_valid) begin
                        op_a_reg   <= mem_rd_a_data;
                        op_b_reg   <= desc_reg.use_immediate ? desc_reg.imm_operand : mem_rd_b_data;
                        op_ready   <= 2'b11;
                        mem_rd_req <= 1'b0;
                        state_reg  <= STATE_READY;
                    end
                end

                STATE_READY: begin
                    if (resource_available) begin
                        dispatch_req <= 1'b1;
                        state_reg    <= STATE_DISPATCHED;
                    end
                end

                STATE_DISPATCHED: begin
                    if (dispatch_ack) begin
                        dispatch_req <= 1'b0;
                        state_reg    <= STATE_EXECUTING;
                    end
                end

                STATE_EXECUTING: begin
                    if (exec_done) begin
                        cand_res_reg <= exec_result;
                        cand_ovf_reg <= exec_overflow;
                        state_reg    <= STATE_RESULT_PENDING;
                    end
                end

                STATE_RESULT_PENDING: begin
                    cert_req  <= 1'b1;
                    state_reg <= STATE_CERTIFYING;
                end

                STATE_CERTIFYING: begin
                    if (cert_done) begin
                        cert_req <= 1'b0;
                        disp_reg <= cert_outcome;
                        case (cert_outcome)
                            OUTCOME_COMMIT: state_reg <= STATE_COMMITTED;
                            OUTCOME_REJECT: state_reg <= STATE_REJECTED;
                            OUTCOME_REFUSE: state_reg <= STATE_REJECTED;
                            OUTCOME_FAULT:  state_reg <= STATE_FAULT;
                            default:        state_reg <= STATE_FAULT;
                        endcase
                    end else begin
                        cert_req <= 1'b1;
                    end
                end

                STATE_FAULT: begin
                    // Terminal fault state for this UoW lifecycle
                    dispatch_req       <= 1'b0;
                    cert_req           <= 1'b0;
                    graph_req          <= 1'b0;
                    graph_query_active <= 1'b0;
                end

                STATE_HALTED: begin
                    dispatch_req       <= 1'b0;
                    cert_req           <= 1'b0;
                    graph_req          <= 1'b0;
                    graph_query_active <= 1'b0;
                end

                default: state_reg <= STATE_FAULT;
            endcase
        end
    end

endmodule

`endif // GEO_WORK_CELL_SV
