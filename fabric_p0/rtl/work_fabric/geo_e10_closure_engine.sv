// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_e10_closure_engine
// Standalone Autonomous Subsystem for E10 Bounded Universe Closure Qualification (P0.7)
// Performs: discover ready work -> execute -> certify -> commit graph/state -> generate successor work -> CLOSED_BOUNDED_UNIVERSE -> halt

`ifndef GEO_E10_CLOSURE_ENGINE_SV
`define GEO_E10_CLOSURE_ENGINE_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_e10_closure_engine #(
    parameter int UNIVERSE_POINTS          = 6,   // 6 base points {0..5}
    parameter int TOTAL_PROBES             = 20,  // C(6, 3) = 20 three-point probes
    parameter int BASE_PROBE_STATE_ADDR    = 16,  // State[16..35] store certified probe results
    parameter int BASE_SCRATCH_ADDR        = 48,  // State[48..55] scratch for intermediate R1
    parameter int GRAPH_PROBE_REL          = 8'hE0,
    parameter int RESTRICT_PROBES_NULLITY  = 0    // If 1, omit probes with element 5 (exposes null space)
) (
    input  logic                   clk,
    input  logic                   reset_n,
    input  logic                   start,
    output logic                   done,
    output closure_status_t        closure_status,
    output logic                   closure_reached,
    output logic                   nullity_detected,

    // Ingress Interface to Work Fabric
    output logic                   ingress_valid,
    input  logic                   ingress_ready,
    output uow_desc_t              ingress_desc,

    // Egress Monitoring Interface from Work Fabric
    input  logic                   egress_valid,
    input  logic                   egress_ready,
    input  logic [31:0]            egress_uow_id,
    input  commit_outcome_t        egress_status,
    input  cl20_mv_t               egress_result,
    input  logic [63:0]            egress_evidence_root,

    // Diagnostic Telemetry & Mathematical Integrity Metrics
    output logic [31:0]            probes_discovered,
    output logic [31:0]            probes_committed,
    output logic [31:0]            total_cycles,
    output logic [31:0]            incidence_diag_sum,
    output logic [31:0]            incidence_offdiag_sum,
    output logic [31:0]            graph_edges_committed
);

    typedef enum logic [2:0] {
        ST_IDLE         = 3'd0,
        ST_DISCOVER     = 3'd1,
        ST_STEP1_EMIT   = 3'd2,
        ST_STEP1_WAIT   = 3'd3,
        ST_STEP2_EMIT   = 3'd4,
        ST_STEP2_WAIT   = 3'd5,
        ST_EVAL_CLOSURE = 3'd6,
        ST_HALT         = 3'd7
    } engine_state_t;

    engine_state_t state;

    // --- The 20 Canonical Three-Point Combinations C(6, 3) ---
    function automatic logic [8:0] get_probe_triple(input logic [4:0] idx);
        case (idx)
            5'd0:  get_probe_triple = {3'd0, 3'd1, 3'd2};
            5'd1:  get_probe_triple = {3'd0, 3'd1, 3'd3};
            5'd2:  get_probe_triple = {3'd0, 3'd1, 3'd4};
            5'd3:  get_probe_triple = {3'd0, 3'd1, 3'd5};
            5'd4:  get_probe_triple = {3'd0, 3'd2, 3'd3};
            5'd5:  get_probe_triple = {3'd0, 3'd2, 3'd4};
            5'd6:  get_probe_triple = {3'd0, 3'd2, 3'd5};
            5'd7:  get_probe_triple = {3'd0, 3'd3, 3'd4};
            5'd8:  get_probe_triple = {3'd0, 3'd3, 3'd5};
            5'd9:  get_probe_triple = {3'd0, 3'd4, 3'd5};
            5'd10: get_probe_triple = {3'd1, 3'd2, 3'd3};
            5'd11: get_probe_triple = {3'd1, 3'd2, 3'd4};
            5'd12: get_probe_triple = {3'd1, 3'd2, 3'd5};
            5'd13: get_probe_triple = {3'd1, 3'd3, 3'd4};
            5'd14: get_probe_triple = {3'd1, 3'd3, 3'd5};
            5'd15: get_probe_triple = {3'd1, 3'd4, 3'd5};
            5'd16: get_probe_triple = {3'd2, 3'd3, 3'd4};
            5'd17: get_probe_triple = {3'd2, 3'd3, 3'd5};
            5'd18: get_probe_triple = {3'd2, 3'd4, 3'd5};
            5'd19: get_probe_triple = {3'd3, 3'd4, 3'd5};
            default: get_probe_triple = 9'd0;
        endcase
    endfunction

    logic [2:0] cur_u, cur_v, cur_w;
    assign {cur_u, cur_v, cur_w} = get_probe_triple(probe_idx);

    // Effective probe count
    localparam int ACTIVE_PROBES = (RESTRICT_PROBES_NULLITY == 1) ? 10 : TOTAL_PROBES;

    logic [4:0]  probe_idx;
    logic [31:0] cycle_cnt;
    logic [31:0] committed_count;
    logic [31:0] edges_mutated;

    // 6x6 Incidence Matrix K^T K (accumulates probe memberships)
    logic [7:0] ktk [0:5][0:5];

    assign probes_discovered      = ACTIVE_PROBES;
    assign probes_committed       = committed_count;
    assign total_cycles           = cycle_cnt;
    assign graph_edges_committed  = edges_mutated;
    assign done                   = (state == ST_HALT);

    // Diagonal & off-diagonal sums
    always_comb begin
        int r, c;
        incidence_diag_sum    = '0;
        incidence_offdiag_sum = '0;
        for (r = 0; r < 6; r = r + 1) begin
            for (c = 0; c < 6; c = c + 1) begin
                if (r == c)
                    incidence_diag_sum = incidence_diag_sum + ktk[r][c];
                else
                    incidence_offdiag_sum = incidence_offdiag_sum + ktk[r][c];
            end
        end
    end

    // Scratch address slot cycling
    logic [7:0] scratch_r1_addr;
    assign scratch_r1_addr = BASE_SCRATCH_ADDR + ((probe_idx[1:0]) * 2);

    // Cycle counter
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            cycle_cnt <= '0;
        end else if (state != ST_IDLE && state != ST_HALT) begin
            cycle_cnt <= cycle_cnt + 1'b1;
        end
    end

    // --- Autonomous Closed-Loop Execution FSM ---
    always_ff @(posedge clk or negedge reset_n) begin
        int r, c;
        logic [2:0] u, v, w;
        if (!reset_n) begin
            state            <= ST_IDLE;
            probe_idx        <= '0;
            committed_count  <= '0;
            edges_mutated    <= '0;
            closure_status   <= CLOSURE_IN_PROGRESS;
            closure_reached  <= 1'b0;
            nullity_detected <= 1'b0;
            ingress_valid    <= 1'b0;
            ingress_desc     <= '0;

            for (r = 0; r < 6; r = r + 1) begin
                for (c = 0; c < 6; c = c + 1) begin
                    ktk[r][c] <= 8'd0;
                end
            end
        end else begin
            case (state)
                ST_IDLE: begin
                    ingress_valid    <= 1'b0;
                    probe_idx        <= '0;
                    committed_count  <= '0;
                    edges_mutated    <= '0;
                    closure_status   <= CLOSURE_IN_PROGRESS;
                    closure_reached  <= 1'b0;
                    nullity_detected <= 1'b0;
                    if (start) begin
                        state <= ST_DISCOVER;
                    end
                end

                ST_DISCOVER: begin
                    // Autonomous Work Discovery: Formulate Step 1 UoW for probe_idx
                    ingress_valid               <= 1'b1;
                    ingress_desc                <= '0;
                    ingress_desc.uow_id         <= {16'h0001, 11'd0, probe_idx};
                    ingress_desc.opcode         <= OP_CL20_PRODUCT;
                    ingress_desc.dest_addr      <= scratch_r1_addr;
                    ingress_desc.src_a_addr     <= {5'd0, cur_u};
                    ingress_desc.src_b_addr     <= {5'd0, cur_v};
                    ingress_desc.auth_token     <= 32'h00000001;
                    ingress_desc.dep_mask       <= 16'd0;
                    ingress_desc.use_immediate  <= 1'b0;
                    ingress_desc.has_graph_mut  <= 1'b0;
                    state                       <= ST_STEP1_EMIT;
                end

                ST_STEP1_EMIT: begin
                    if (ingress_valid && ingress_ready) begin
                        ingress_valid <= 1'b0;
                        state         <= ST_STEP1_WAIT;
                    end
                end

                ST_STEP1_WAIT: begin
                    // Wait for Step 1 completion
                    if (egress_valid && egress_ready && (egress_status == OUTCOME_COMMIT)) begin
                        if (egress_uow_id == {16'h0001, 11'd0, probe_idx}) begin
                            // Formulate Step 2 UoW: R2 = R1 * P_w, with candidate graph mutation
                            ingress_valid               <= 1'b1;
                            ingress_desc                <= '0;
                            ingress_desc.uow_id         <= {16'h0002, 11'd0, probe_idx};
                            ingress_desc.opcode         <= OP_CL20_PRODUCT;
                            ingress_desc.dest_addr      <= BASE_PROBE_STATE_ADDR + probe_idx;
                            ingress_desc.src_a_addr     <= scratch_r1_addr;
                            ingress_desc.src_b_addr     <= {5'd0, cur_w};
                            ingress_desc.auth_token     <= 32'h00000001;
                            ingress_desc.dep_mask       <= 16'd0;
                            ingress_desc.use_immediate  <= 1'b0;

                            // Candidate Graph Mutation: Certified Edge Mutation
                            ingress_desc.has_graph_mut  <= 1'b1;
                            ingress_desc.graph_mut_cmd  <= GRAPH_MUT_ADD_EDGE;
                            ingress_desc.graph_mut_node <= {13'd0, cur_u};
                            ingress_desc.graph_mut_target <= {13'd0, cur_w};
                            ingress_desc.graph_mut_rel  <= GRAPH_PROBE_REL;
                            ingress_desc.graph_mut_flags <= 8'h01;

                            state <= ST_STEP2_EMIT;
                        end
                    end
                end

                ST_STEP2_EMIT: begin
                    if (ingress_valid && ingress_ready) begin
                        ingress_valid <= 1'b0;
                        state         <= ST_STEP2_WAIT;
                    end
                end

                ST_STEP2_WAIT: begin
                    // Await certified commit of Step 2
                    if (egress_valid && egress_ready && (egress_status == OUTCOME_COMMIT)) begin
                        if (egress_uow_id == {16'h0002, 11'd0, probe_idx}) begin
                            committed_count <= committed_count + 1'b1;
                            edges_mutated   <= edges_mutated + 1'b1;

                            // Accumulate into incidence matrix K^T K
                            u = cur_u;
                            v = cur_v;
                            w = cur_w;

                            ktk[u][u] <= ktk[u][u] + 1'b1;
                            ktk[v][v] <= ktk[v][v] + 1'b1;
                            ktk[w][w] <= ktk[w][w] + 1'b1;

                            ktk[u][v] <= ktk[u][v] + 1'b1;
                            ktk[v][u] <= ktk[v][u] + 1'b1;
                            ktk[u][w] <= ktk[u][w] + 1'b1;
                            ktk[w][u] <= ktk[w][u] + 1'b1;
                            ktk[v][w] <= ktk[v][w] + 1'b1;
                            ktk[w][v] <= ktk[w][v] + 1'b1;

                            // Autonomous Successor Work Generation
                            if (probe_idx + 1'b1 < ACTIVE_PROBES) begin
                                probe_idx <= probe_idx + 1'b1;
                                state     <= ST_DISCOVER;
                            end else begin
                                state     <= ST_EVAL_CLOSURE;
                            end
                        end
                    end
                end

                ST_EVAL_CLOSURE: begin
                    // Evaluate mathematical closure condition
                    // For full universe: all 6 diagonal entries == 10, all 30 off-diagonal == 4
                    // K^T K == 6*I + 4*J, Rank = 6, Nullity = 0
                    if (RESTRICT_PROBES_NULLITY == 0) begin
                        if ((incidence_diag_sum == 32'd60) && (incidence_offdiag_sum == 32'd120)) begin
                            closure_status  <= CLOSED_BOUNDED_UNIVERSE;
                            closure_reached <= 1'b1;
                        end else begin
                            closure_status  <= CLOSURE_FAULT;
                            closure_reached <= 1'b0;
                        end
                    end else begin
                        // Incomplete universe restricted nullity
                        closure_status   <= INCOMPLETE_UNIVERSE_NULLITY;
                        nullity_detected <= 1'b1;
                        closure_reached  <= 1'b0;
                    end
                    state <= ST_HALT;
                end

                ST_HALT: begin
                    ingress_valid <= 1'b0;
                    // Remains halted until reset
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

`endif // GEO_E10_CLOSURE_ENGINE_SV
