// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_graph_memory
// Deterministic CSR hardware graph subsystem with semantic query interface

`ifndef GEO_GRAPH_MEMORY_SV
`define GEO_GRAPH_MEMORY_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_graph_memory #(
    parameter int MAX_NODES   = 256,
    parameter int MAX_EDGES   = 1024,
    parameter int QUEUE_DEPTH = 128
) (
    input  logic                   clk,
    input  logic                   reset_n,

    // Pre-initialization / Graph Image Load Interface (Boot-time)
    input  logic                   node_wr_en,
    input  logic [15:0]            node_wr_addr,
    input  graph_node_t            node_wr_data,

    input  logic                   edge_wr_en,
    input  logic [15:0]            edge_wr_addr,
    input  graph_edge_t            edge_wr_data,

    // Authoritative Runtime Graph Mutation Port (Section 7.4 & P0.7)
    input  logic                   commit_graph_en,
    input  graph_mut_cmd_t         commit_graph_cmd,
    input  logic [15:0]            commit_graph_node,
    input  logic [15:0]            commit_graph_target,
    input  logic [7:0]             commit_graph_rel,
    input  logic [7:0]             commit_graph_flags,

    // Hardware Semantic Query Interface
    input  logic                   query_start,
    input  graph_cmd_t             cmd,
    input  graph_query_t           query,
    input  logic [15:0]            direct_edge_idx,
    input  logic                   neighbor_ack,

    output logic                   busy,
    output logic                   done,
    output logic                   error_bounds,
    output logic                   error_malformed,
    output graph_node_t            out_node,
    output graph_edge_t            out_edge,
    output logic [15:0]            hit_count,
    output logic [15:0]            current_neighbor,
    output logic [1:0]             current_distance,
    output logic                   neighbor_valid
);

    // --- Hardware CSR Component Storage Arrays (BRAM-Inferable) ---
    // Node Table: (edge_base, edge_count, node_type, flags, version)
    logic [15:0] node_edge_base   [0:MAX_NODES-1];
    logic [15:0] node_edge_count  [0:MAX_NODES-1];
    logic [7:0]  node_type_tbl    [0:MAX_NODES-1];
    logic [7:0]  node_flags_tbl   [0:MAX_NODES-1];
    logic [15:0] node_version_tbl [0:MAX_NODES-1];

    // Edge Table: (target_node, relation_type, flags)
    logic [15:0] edge_target_tbl  [0:MAX_EDGES-1];
    logic [7:0]  edge_rel_tbl     [0:MAX_EDGES-1];
    logic [7:0]  edge_flags_tbl   [0:MAX_EDGES-1];

    logic [15:0] edge_alloc_ptr;

    // Synchronous write ports for boot image loading and runtime certified mutations
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            edge_alloc_ptr <= 16'd0;
        end else begin
            // Boot-time static loading
            if (node_wr_en && node_wr_addr < MAX_NODES) begin
                node_edge_base[node_wr_addr]   <= node_wr_data.edge_base;
                node_edge_count[node_wr_addr]  <= node_wr_data.edge_count;
                node_type_tbl[node_wr_addr]    <= node_wr_data.node_type;
                node_flags_tbl[node_wr_addr]   <= node_wr_data.flags;
                node_version_tbl[node_wr_addr] <= node_wr_data.version;
            end
            if (edge_wr_en && edge_wr_addr < MAX_EDGES) begin
                edge_target_tbl[edge_wr_addr]  <= edge_wr_data.target_node;
                edge_rel_tbl[edge_wr_addr]     <= edge_wr_data.relation_type;
                edge_flags_tbl[edge_wr_addr]   <= edge_wr_data.flags;
                if (edge_wr_addr >= edge_alloc_ptr) begin
                    edge_alloc_ptr <= edge_wr_addr + 1'b1;
                end
            end

            // Runtime Authoritative Mutations (Certified commit)
            if (commit_graph_en) begin
                case (commit_graph_cmd)
                    GRAPH_MUT_ADD_EDGE: begin
                        if (edge_alloc_ptr < MAX_EDGES && commit_graph_node < MAX_NODES) begin
                            edge_target_tbl[edge_alloc_ptr] <= commit_graph_target;
                            edge_rel_tbl[edge_alloc_ptr]    <= commit_graph_rel;
                            edge_flags_tbl[edge_alloc_ptr]  <= commit_graph_flags;
                            if (node_edge_count[commit_graph_node] == 16'd0) begin
                                node_edge_base[commit_graph_node] <= edge_alloc_ptr;
                            end
                            node_edge_count[commit_graph_node]  <= node_edge_count[commit_graph_node] + 1'b1;
                            node_version_tbl[commit_graph_node] <= node_version_tbl[commit_graph_node] + 1'b1;
                            edge_alloc_ptr                      <= edge_alloc_ptr + 1'b1;
                        end
                    end
                    GRAPH_MUT_ADD_NODE: begin
                        if (commit_graph_node < MAX_NODES) begin
                            node_edge_base[commit_graph_node]   <= edge_alloc_ptr;
                            node_edge_count[commit_graph_node]  <= 16'd0;
                            node_type_tbl[commit_graph_node]    <= commit_graph_flags;
                            node_flags_tbl[commit_graph_node]   <= 8'd0;
                            node_version_tbl[commit_graph_node] <= 16'd1;
                        end
                    end
                    GRAPH_MUT_UPDATE_NODE: begin
                        if (commit_graph_node < MAX_NODES) begin
                            node_flags_tbl[commit_graph_node]   <= commit_graph_flags;
                            node_version_tbl[commit_graph_node] <= node_version_tbl[commit_graph_node] + 1'b1;
                        end
                    end
                    default: ;
                endcase
            end
        end
    end

    // --- Traversal State Machine ---
    typedef enum logic [3:0] {
        ST_IDLE             = 4'd0,
        ST_FOLLOW_LOOKUP    = 4'd1,
        ST_FOLLOW_FETCH     = 4'd2,
        ST_REL_SCAN_INIT    = 4'd3,
        ST_REL_SCAN_EVAL    = 4'd4,
        ST_NB_INIT          = 4'd5,
        ST_NB_DEQUEUE       = 4'd6,
        ST_NB_NODE_FETCH    = 4'd7,
        ST_NB_EDGE_READ     = 4'd8,
        ST_NB_EDGE_EVAL     = 4'd9,
        ST_NB_EMIT_WAIT     = 4'd10,
        ST_DONE             = 4'd11
    } graph_state_t;

    graph_state_t state;

    // Traversal FIFO queue: elements store (node_id[15:0], distance[1:0])
    logic [15:0] queue_node [0:QUEUE_DEPTH-1];
    logic [1:0]  queue_dist [0:QUEUE_DEPTH-1];
    logic [7:0]  q_head, q_tail;
    logic [MAX_NODES-1:0] visited;

    // Registers for active query
    graph_query_t q_reg;
    graph_node_t  curr_node_rec;
    logic [15:0]  curr_q_node;
    logic [1:0]   curr_q_dist;
    logic [15:0]  edge_cursor;
    logic [15:0]  edge_end;

    logic [15:0]  eval_target;
    logic         eval_rel_match;
    assign eval_target    = out_edge.target_node;
    assign eval_rel_match = (q_reg.relation_filter == 8'd0) ||
                            (out_edge.relation_type == q_reg.relation_filter);

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state            <= ST_IDLE;
            busy             <= 1'b0;
            done             <= 1'b0;
            error_bounds     <= 1'b0;
            error_malformed  <= 1'b0;
            out_node         <= '0;
            out_edge         <= '0;
            hit_count        <= '0;
            current_neighbor <= '0;
            current_distance <= '0;
            neighbor_valid   <= 1'b0;
            q_head           <= '0;
            q_tail           <= '0;
            visited          <= '0;
            q_reg            <= '0;
            curr_node_rec    <= '0;
            curr_q_node      <= '0;
            curr_q_dist      <= '0;
            edge_cursor      <= '0;
            edge_end         <= '0;
        end else begin
            case (state)
                ST_IDLE: begin
                    done            <= 1'b0;
                    error_bounds    <= 1'b0;
                    error_malformed <= 1'b0;
                    neighbor_valid  <= 1'b0;

                    if (query_start) begin
                        busy  <= 1'b1;
                        q_reg <= query;

                        case (cmd)
                            GRAPH_CMD_NODE_LOOKUP: begin
                                if (query.start_node >= MAX_NODES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    out_node.edge_base  <= node_edge_base[query.start_node];
                                    out_node.edge_count <= node_edge_count[query.start_node];
                                    out_node.node_type  <= node_type_tbl[query.start_node];
                                    out_node.flags      <= node_flags_tbl[query.start_node];
                                    out_node.version    <= node_version_tbl[query.start_node];
                                    state               <= ST_DONE;
                                end
                            end

                            GRAPH_CMD_EDGE_FETCH: begin
                                if (direct_edge_idx >= MAX_EDGES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    out_edge.target_node   <= edge_target_tbl[direct_edge_idx];
                                    out_edge.relation_type <= edge_rel_tbl[direct_edge_idx];
                                    out_edge.flags         <= edge_flags_tbl[direct_edge_idx];
                                    state                  <= ST_DONE;
                                end
                            end

                            GRAPH_CMD_FOLLOW: begin
                                if (query.start_node >= MAX_NODES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    curr_node_rec.edge_base  <= node_edge_base[query.start_node];
                                    curr_node_rec.edge_count <= node_edge_count[query.start_node];
                                    curr_node_rec.node_type  <= node_type_tbl[query.start_node];
                                    curr_node_rec.flags      <= node_flags_tbl[query.start_node];
                                    curr_node_rec.version    <= node_version_tbl[query.start_node];
                                    state                    <= ST_FOLLOW_LOOKUP;
                                end
                            end

                            GRAPH_CMD_RELATION_MATCH: begin
                                if (query.start_node >= MAX_NODES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    curr_node_rec.edge_base  <= node_edge_base[query.start_node];
                                    curr_node_rec.edge_count <= node_edge_count[query.start_node];
                                    curr_node_rec.node_type  <= node_type_tbl[query.start_node];
                                    curr_node_rec.flags      <= node_flags_tbl[query.start_node];
                                    curr_node_rec.version    <= node_version_tbl[query.start_node];
                                    hit_count                <= '0;
                                    state                    <= ST_REL_SCAN_INIT;
                                end
                            end

                            GRAPH_CMD_NODE_TYPE_MATCH: begin
                                if (query.start_node >= MAX_NODES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    out_node.edge_base  <= node_edge_base[query.start_node];
                                    out_node.edge_count <= node_edge_count[query.start_node];
                                    out_node.node_type  <= node_type_tbl[query.start_node];
                                    out_node.flags      <= node_flags_tbl[query.start_node];
                                    out_node.version    <= node_version_tbl[query.start_node];
                                    hit_count           <= (node_type_tbl[query.start_node] == query.target_type_filter) ? 16'd1 : 16'd0;
                                    state               <= ST_DONE;
                                end
                            end

                            GRAPH_CMD_NEIGHBORHOOD_BEGIN: begin
                                if (query.start_node >= MAX_NODES) begin
                                    error_bounds <= 1'b1;
                                    state        <= ST_DONE;
                                end else begin
                                    visited          <= ({{(MAX_NODES-1){1'b0}}, 1'b1} << query.start_node);
                                    hit_count        <= '0;
                                    q_head           <= '0;
                                    q_tail           <= '0;
                                    // Seed initial node at distance 0
                                    queue_node[0]    <= query.start_node;
                                    queue_dist[0]    <= 2'd0;
                                    q_tail           <= 8'd1;
                                    state            <= ST_NB_DEQUEUE;
                                end
                            end

                            default: begin
                                state <= ST_DONE;
                            end
                        endcase
                    end
                end

                // --- FOLLOW execution ---
                ST_FOLLOW_LOOKUP: begin
                    if (curr_node_rec.edge_count == 16'd0) begin
                        hit_count <= '0;
                        state     <= ST_DONE;
                    end else begin
                        if (curr_node_rec.edge_base >= MAX_EDGES) begin
                            error_malformed <= 1'b1;
                            state           <= ST_DONE;
                        end else begin
                            out_edge.target_node   <= edge_target_tbl[curr_node_rec.edge_base];
                            out_edge.relation_type <= edge_rel_tbl[curr_node_rec.edge_base];
                            out_edge.flags         <= edge_flags_tbl[curr_node_rec.edge_base];
                            state                  <= ST_FOLLOW_FETCH;
                        end
                    end
                end

                ST_FOLLOW_FETCH: begin
                    if (out_edge.target_node >= MAX_NODES) begin
                        error_malformed <= 1'b1;
                    end else begin
                        out_node.edge_base  <= node_edge_base[out_edge.target_node];
                        out_node.edge_count <= node_edge_count[out_edge.target_node];
                        out_node.node_type  <= node_type_tbl[out_edge.target_node];
                        out_node.flags      <= node_flags_tbl[out_edge.target_node];
                        out_node.version    <= node_version_tbl[out_edge.target_node];
                        hit_count           <= 16'd1;
                    end
                    state <= ST_DONE;
                end

                // --- RELATION_MATCH execution ---
                ST_REL_SCAN_INIT: begin
                    edge_cursor <= curr_node_rec.edge_base;
                    edge_end    <= curr_node_rec.edge_base + curr_node_rec.edge_count;
                    if (curr_node_rec.edge_count == 16'd0) begin
                        state <= ST_DONE;
                    end else begin
                        state <= ST_REL_SCAN_EVAL;
                    end
                end

                ST_REL_SCAN_EVAL: begin
                    if (edge_cursor >= edge_end || edge_cursor >= MAX_EDGES) begin
                        if (edge_cursor >= MAX_EDGES && edge_cursor < edge_end) begin
                            error_bounds <= 1'b1;
                        end
                        state <= ST_DONE;
                    end else begin
                        if (q_reg.relation_filter == 8'd0 ||
                            edge_rel_tbl[edge_cursor] == q_reg.relation_filter) begin
                            hit_count              <= hit_count + 1'b1;
                            out_edge.target_node   <= edge_target_tbl[edge_cursor];
                            out_edge.relation_type <= edge_rel_tbl[edge_cursor];
                            out_edge.flags         <= edge_flags_tbl[edge_cursor];
                        end
                        edge_cursor <= edge_cursor + 1'b1;
                    end
                end

                // --- NEIGHBORHOOD multi-hop BFS traversal ---
                ST_NB_DEQUEUE: begin
                    if (q_head == q_tail) begin
                        state <= ST_DONE;
                    end else begin
                        curr_q_node <= queue_node[q_head];
                        curr_q_dist <= queue_dist[q_head];
                        q_head      <= q_head + 1'b1;
                        state       <= ST_NB_NODE_FETCH;
                    end
                end

                ST_NB_NODE_FETCH: begin
                    if (curr_q_node >= MAX_NODES) begin
                        error_malformed <= 1'b1;
                        state           <= ST_NB_DEQUEUE;
                    end else begin
                        curr_node_rec.edge_base  <= node_edge_base[curr_q_node];
                        curr_node_rec.edge_count <= node_edge_count[curr_q_node];
                        curr_node_rec.node_type  <= node_type_tbl[curr_q_node];
                        curr_node_rec.flags      <= node_flags_tbl[curr_q_node];
                        curr_node_rec.version    <= node_version_tbl[curr_q_node];

                        edge_cursor <= node_edge_base[curr_q_node];
                        edge_end    <= node_edge_base[curr_q_node] + node_edge_count[curr_q_node];

                        if (node_edge_count[curr_q_node] == 16'd0 || curr_q_dist >= q_reg.radius) begin
                            state <= ST_NB_DEQUEUE;
                        end else begin
                            state <= ST_NB_EDGE_READ;
                        end
                    end
                end

                ST_NB_EDGE_READ: begin
                    if (edge_cursor >= edge_end) begin
                        state <= ST_NB_DEQUEUE;
                    end else if (edge_cursor >= MAX_EDGES) begin
                        error_malformed <= 1'b1;
                        state           <= ST_NB_DEQUEUE;
                    end else begin
                        out_edge.target_node   <= edge_target_tbl[edge_cursor];
                        out_edge.relation_type <= edge_rel_tbl[edge_cursor];
                        out_edge.flags         <= edge_flags_tbl[edge_cursor];
                        state                  <= ST_NB_EDGE_EVAL;
                    end
                end

                ST_NB_EDGE_EVAL: begin
                    if (eval_target >= MAX_NODES) begin
                        // Malformed target node index in edge table
                        error_malformed <= 1'b1;
                        edge_cursor     <= edge_cursor + 1'b1;
                        state           <= ST_NB_EDGE_READ;
                    end else if (eval_rel_match && !((visited >> eval_target) & 1'b1)) begin
                        // Discovered a new unvisited neighbor
                        visited               <= visited | ({{(MAX_NODES-1){1'b0}}, 1'b1} << eval_target);
                        current_neighbor      <= eval_target;
                        current_distance      <= curr_q_dist + 1'b1;
                        neighbor_valid        <= 1'b1;
                        hit_count             <= hit_count + 1'b1;

                        // Enqueue if distance allows further expansion
                        if ((curr_q_dist + 1'b1) < q_reg.radius) begin
                            if (q_tail < QUEUE_DEPTH) begin
                                queue_node[q_tail] <= eval_target;
                                queue_dist[q_tail] <= curr_q_dist + 1'b1;
                                q_tail             <= q_tail + 1'b1;
                            end
                        end

                        edge_cursor <= edge_cursor + 1'b1;
                        state       <= ST_NB_EMIT_WAIT;
                    end else begin
                        // Either visited or relation filter did not match
                        edge_cursor <= edge_cursor + 1'b1;
                        state       <= ST_NB_EDGE_READ;
                    end
                end

                ST_NB_EMIT_WAIT: begin
                    // Stream out neighbor; advance when neighbor_ack asserted or single-cycle pulse
                    if (neighbor_ack) begin
                        neighbor_valid <= 1'b0;
                        state          <= ST_NB_EDGE_READ;
                    end
                end

                ST_DONE: begin
                    busy           <= 1'b0;
                    done           <= 1'b1;
                    neighbor_valid <= 1'b0;
                    state          <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

`endif // GEO_GRAPH_MEMORY_SV
