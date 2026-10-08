// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_geo_graph_memory
// Qualification Testbench for P0.4 Native CSR Graph Subsystem

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_geo_graph_memory;

    parameter int MAX_NODES   = 256;
    parameter int MAX_EDGES   = 1024;
    parameter int QUEUE_DEPTH = 128;

    logic              clk;
    logic              reset_n;

    // Image load interface
    logic              node_wr_en;
    logic [15:0]       node_wr_addr;
    graph_node_t       node_wr_data;

    logic              edge_wr_en;
    logic [15:0]       edge_wr_addr;
    graph_edge_t       edge_wr_data;

    // Query interface
    logic              query_start;
    graph_cmd_t        cmd;
    graph_query_t      query;
    logic [15:0]       direct_edge_idx;
    logic              neighbor_ack;

    logic              busy;
    logic              done;
    logic              error_bounds;
    logic              error_malformed;
    graph_node_t       out_node;
    graph_edge_t       out_edge;
    logic [15:0]       hit_count;
    logic [15:0]       current_neighbor;
    logic [1:0]        current_distance;
    logic              neighbor_valid;

    // DUT
    geo_graph_memory #(
        .MAX_NODES(MAX_NODES),
        .MAX_EDGES(MAX_EDGES),
        .QUEUE_DEPTH(QUEUE_DEPTH)
    ) dut (
        .clk(clk),
        .reset_n(reset_n),
        .node_wr_en(node_wr_en),
        .node_wr_addr(node_wr_addr),
        .node_wr_data(node_wr_data),
        .edge_wr_en(edge_wr_en),
        .edge_wr_addr(edge_wr_addr),
        .edge_wr_data(edge_wr_data),
        .query_start(query_start),
        .cmd(cmd),
        .query(query),
        .direct_edge_idx(direct_edge_idx),
        .neighbor_ack(neighbor_ack),
        .busy(busy),
        .done(done),
        .error_bounds(error_bounds),
        .error_malformed(error_malformed),
        .out_node(out_node),
        .out_edge(out_edge),
        .hit_count(hit_count),
        .current_neighbor(current_neighbor),
        .current_distance(current_distance),
        .neighbor_valid(neighbor_valid)
    );

    // 100 MHz Clock (10ns period)
    always #5 clk = ~clk;

    // Tasks for writing node & edge tables during boot
    task write_node(input logic [15:0] id, input logic [15:0] e_base, input logic [15:0] e_count, input logic [7:0] n_type);
        begin
            @(negedge clk);
            node_wr_en   = 1'b1;
            node_wr_addr = id;
            node_wr_data.edge_base  = e_base;
            node_wr_data.edge_count = e_count;
            node_wr_data.node_type  = n_type;
            node_wr_data.flags      = 8'h01;
            node_wr_data.version    = 16'd1;
            @(negedge clk);
            node_wr_en   = 1'b0;
        end
    endtask

    task write_edge(input logic [15:0] idx, input logic [15:0] target, input logic [7:0] rel);
        begin
            @(negedge clk);
            edge_wr_en   = 1'b1;
            edge_wr_addr = idx;
            edge_wr_data.target_node   = target;
            edge_wr_data.relation_type = rel;
            edge_wr_data.flags         = 8'h00;
            @(negedge clk);
            edge_wr_en   = 1'b0;
        end
    endtask

    // Task for executing semantic query
    task exec_query(
        input graph_cmd_t   c,
        input logic [15:0]  start_node,
        input logic [7:0]   rel_filter,
        input logic [7:0]   type_filter,
        input logic [1:0]   rad
    );
        begin
            @(negedge clk);
            cmd                      = c;
            query.start_node         = start_node;
            query.relation_filter    = rel_filter;
            query.target_type_filter = type_filter;
            query.radius             = rad;
            query_start              = 1'b1;
            @(negedge clk);
            query_start              = 1'b0;
            while (!done) @(negedge clk);
        end
    endtask

    // Array to record discovered neighbors during streaming BFS
    logic [15:0] discovered_neighbors [0:63];
    logic [1:0]  discovered_distances [0:63];
    integer      discovered_count;

    task exec_neighborhood_stream(
        input logic [15:0] start_node,
        input logic [1:0]  rad,
        input logic [7:0]  rel_filter
    );
        begin
            discovered_count = 0;
            @(negedge clk);
            cmd                   = GRAPH_CMD_NEIGHBORHOOD_BEGIN;
            query.start_node      = start_node;
            query.radius          = rad;
            query.relation_filter = rel_filter;
            query_start           = 1'b1;
            neighbor_ack          = 1'b0;
            @(negedge clk);
            query_start           = 1'b0;

            while (!done) begin
                if (neighbor_valid) begin
                    discovered_neighbors[discovered_count] = current_neighbor;
                    discovered_distances[discovered_count] = current_distance;
                    discovered_count = discovered_count + 1;
                    neighbor_ack = 1'b1;
                    @(negedge clk);
                    neighbor_ack = 1'b0;
                end else begin
                    @(negedge clk);
                end
            end
        end
    endtask

    localparam logic [7:0] REL_R1 = 8'h10;
    localparam logic [7:0] REL_R2 = 8'h20;
    localparam logic [7:0] REL_R3 = 8'h30;

    initial begin
        clk             = 0;
        reset_n         = 0;
        node_wr_en      = 0;
        edge_wr_en      = 0;
        query_start     = 0;
        neighbor_ack    = 0;
        direct_edge_idx = 0;
        cmd             = GRAPH_CMD_NOP;
        query           = '0;

        #20 reset_n = 1;
        #10;

        $display("=== P0.4: BEGIN NATIVE GRAPH MEMORY QUALIFICATION ===");

        // --- 1. Load Frozen Graph Fixture into CSR Memory ---
        // Node 0: Zero-edge node
        write_node(16'd0, 16'd0, 16'd0, 8'h01);

        // Node 1: One-edge node -> points to Node 2 via REL_R1
        write_node(16'd1, 16'd0, 16'd1, 8'h02);
        write_edge(16'd0, 16'd2, REL_R1);

        // Node 2: Fanout node -> 3 edges (Nodes 3, 4, 5) with REL_R1, REL_R2, REL_R3
        write_node(16'd2, 16'd1, 16'd3, 8'h03);
        write_edge(16'd1, 16'd3, REL_R1);
        write_edge(16'd2, 16'd4, REL_R2);
        write_edge(16'd3, 16'd5, REL_R3);

        // Node 3: Parallel edges with multiple relations -> Node 6 (via R1 and R2)
        write_node(16'd3, 16'd4, 16'd2, 8'h04);
        write_edge(16'd4, 16'd6, REL_R1);
        write_edge(16'd5, 16'd6, REL_R2);

        // Node 4: Linear chain -> Node 7 via REL_R2
        write_node(16'd4, 16'd6, 16'd1, 8'h04);
        write_edge(16'd6, 16'd7, REL_R2);

        // Node 5: Cycle back -> points back to Node 1 via REL_R1
        write_node(16'd5, 16'd7, 16'd1, 8'h04);
        write_edge(16'd7, 16'd1, REL_R1);

        // Node 6: Deep chain -> Node 8 via REL_R1
        write_node(16'd6, 16'd8, 16'd1, 8'h05);
        write_edge(16'd8, 16'd8, REL_R1);

        // Node 7: Deep chain -> Node 9 via REL_R2
        write_node(16'd7, 16'd9, 16'd1, 8'h05);
        write_edge(16'd9, 16'd9, REL_R2);

        // Node 8: Deep chain -> Node 10 via REL_R1
        write_node(16'd8, 16'd10, 16'd1, 8'h06);
        write_edge(16'd10, 16'd10, REL_R1);

        // Node 9 & 10: Sink nodes (0 edges)
        write_node(16'd9, 16'd11, 16'd0, 8'h07);
        write_node(16'd10, 16'd11, 16'd0, 8'h07);

        // Node 11: Malformed target node (points to Node 999 > MAX_NODES)
        write_node(16'd11, 16'd11, 16'd1, 8'h08);
        write_edge(16'd11, 16'd999, REL_R1);

        $display("[FIXTURE] Graph loaded: 12 nodes, 12 edges into CSR hardware tables.");

        // --- 2. Test NODE_LOOKUP ---
        exec_query(GRAPH_CMD_NODE_LOOKUP, 16'd2, 8'd0, 8'd0, 2'd1);
        if (error_bounds || out_node.edge_base !== 16'd1 || out_node.edge_count !== 16'd3 || out_node.node_type !== 8'h03)
            $fatal(1, "NODE_LOOKUP on Node 2 failed");
        $display("[PASS] NODE_LOOKUP: Node 2 record verified.");

        // --- 3. Test EDGE_FETCH ---
        direct_edge_idx = 16'd2;
        exec_query(GRAPH_CMD_EDGE_FETCH, 16'd0, 8'd0, 8'd0, 2'd1);
        if (error_bounds || out_edge.target_node !== 16'd4 || out_edge.relation_type !== REL_R2)
            $fatal(1, "EDGE_FETCH on Edge 2 failed");
        $display("[PASS] EDGE_FETCH: Edge 2 verified (target=4, rel=0x20).");

        // --- 4. Test FOLLOW ---
        exec_query(GRAPH_CMD_FOLLOW, 16'd1, 8'd0, 8'd0, 2'd1);
        if (error_bounds || error_malformed || hit_count !== 16'd1 || out_node.node_type !== 8'h03)
            $fatal(1, "FOLLOW on Node 1 failed");
        $display("[PASS] FOLLOW: Followed Node 1 -> Node 2.");

        // --- 5. Test Zero-Edge Node FOLLOW ---
        exec_query(GRAPH_CMD_FOLLOW, 16'd0, 8'd0, 8'd0, 2'd1);
        if (error_bounds || hit_count !== 16'd0)
            $fatal(1, "FOLLOW on Zero-edge Node 0 failed");
        $display("[PASS] FOLLOW: Zero-edge node returned hit_count=0.");

        // --- 6. Test RELATION_MATCH ---
        // Node 2 has 3 edges: 1x R1, 1x R2, 1x R3
        exec_query(GRAPH_CMD_RELATION_MATCH, 16'd2, REL_R2, 8'd0, 2'd1);
        if (hit_count !== 16'd1 || out_edge.target_node !== 16'd4)
            $fatal(1, "RELATION_MATCH filter R2 on Node 2 failed");

        // Match all relations (filter = 0)
        exec_query(GRAPH_CMD_RELATION_MATCH, 16'd2, 8'd0, 8'd0, 2'd1);
        if (hit_count !== 16'd3)
            $fatal(1, "RELATION_MATCH wildcard on Node 2 failed: expected 3, got %0d", hit_count);
        $display("[PASS] RELATION_MATCH: Specific and wildcard relation filtering verified.");

        // --- 7. Test NODE_TYPE_MATCH ---
        exec_query(GRAPH_CMD_NODE_TYPE_MATCH, 16'd2, 8'd0, 8'h03, 2'd1);
        if (hit_count !== 16'd1) $fatal(1, "NODE_TYPE_MATCH positive failed");

        exec_query(GRAPH_CMD_NODE_TYPE_MATCH, 16'd2, 8'd0, 8'h99, 2'd1);
        if (hit_count !== 16'd0) $fatal(1, "NODE_TYPE_MATCH negative failed");
        $display("[PASS] NODE_TYPE_MATCH: Verified type match.");

        // --- 8. Test NEIGHBORHOOD Expansion: Radii r=1, r=2, r=3 from Node 1 ---
        // Reference Parity Check:
        // r=1 from Node 1: {Node 2} -> 1 hit
        exec_neighborhood_stream(16'd1, 2'd1, 8'd0);
        if (discovered_count !== 1 || discovered_neighbors[0] !== 16'd2 || discovered_distances[0] !== 2'd1)
            $fatal(1, "Neighborhood r=1 failed: count=%0d", discovered_count);
        $display("[PASS] NEIGHBORHOOD r=1: 1 hit (Node 2, dist=1).");

        // r=2 from Node 1: {Node 2, Node 3, Node 4, Node 5} -> 4 hits
        exec_neighborhood_stream(16'd1, 2'd2, 8'd0);
        if (discovered_count !== 4)
            $fatal(1, "Neighborhood r=2 count failed: expected 4, got %0d", discovered_count);
        $display("[PASS] NEIGHBORHOOD r=2: 4 hits (Nodes 2, 3, 4, 5).");

        // r=3 from Node 1: {Node 2, Node 3, Node 4, Node 5, Node 6, Node 7} -> 6 hits
        // (Node 5 points to Node 1, but Node 1 is the visited seed, so cycle is cleanly ignored)
        exec_neighborhood_stream(16'd1, 2'd3, 8'd0);
        if (discovered_count !== 6)
            $fatal(1, "Neighborhood r=3 count failed: expected 6, got %0d", discovered_count);
        $display("[PASS] NEIGHBORHOOD r=3: 6 hits (Cycle handled cleanly without duplication).");

        // --- 9. Test Deterministic Traversal Ordering ---
        // Run neighborhood r=3 a second time and verify sequence is identical
        begin
            logic [15:0] run1_nodes [0:5];
            integer r_idx;
            for (r_idx = 0; r_idx < 6; r_idx = r_idx + 1) begin
                run1_nodes[r_idx] = discovered_neighbors[r_idx];
            end

            exec_neighborhood_stream(16'd1, 2'd3, 8'd0);
            for (r_idx = 0; r_idx < 6; r_idx = r_idx + 1) begin
                if (discovered_neighbors[r_idx] !== run1_nodes[r_idx])
                    $fatal(1, "Deterministic traversal order violated at step %0d", r_idx);
            end
            $display("[PASS] DETERMINISTIC ORDER: Identical traversal order across repeated runs.");
        end

        // --- 10. Test Relation-Filtered Neighborhood Traversal ---
        // From Node 1 with filter = REL_R1 (0x10):
        // r=1: Node 2 (via R1)
        // r=2: Node 2, Node 3 (only R1 edge from Node 2 to Node 3 traversed; Nodes 4 and 5 filtered out)
        // r=3: Node 2, Node 3, Node 6 (R1 edge from Node 3 to Node 6)
        exec_neighborhood_stream(16'd1, 2'd3, REL_R1);
        if (discovered_count !== 3 || discovered_neighbors[2] !== 16'd6)
            $fatal(1, "Relation-filtered neighborhood failed: count=%0d", discovered_count);
        $display("[PASS] RELATION-FILTERED NEIGHBORHOOD: Filtered path 1 -> 2 -> 3 -> 6 (3 hits).");

        // --- 11. Test Error Handling: Out-of-bounds start node ---
        exec_query(GRAPH_CMD_NODE_LOOKUP, 16'd300, 8'd0, 8'd0, 2'd1);
        if (!error_bounds) $fatal(1, "Failed to flag bounds error on start_node=300");
        $display("[PASS] BOUNDS CHECK: Out-of-bounds start_node=300 flagged correctly.");

        // --- 12. Test Error Handling: Out-of-bounds edge fetch ---
        direct_edge_idx = 16'd1500;
        exec_query(GRAPH_CMD_EDGE_FETCH, 16'd0, 8'd0, 8'd0, 2'd1);
        if (!error_bounds) $fatal(1, "Failed to flag bounds error on direct_edge_idx=1500");
        $display("[PASS] BOUNDS CHECK: Out-of-bounds direct_edge_idx=1500 flagged correctly.");

        // --- 13. Test Error Handling: Malformed target node ---
        exec_query(GRAPH_CMD_FOLLOW, 16'd11, 8'd0, 8'd0, 2'd1);
        if (!error_malformed) $fatal(1, "Failed to flag malformed target error on Node 11");
        $display("[PASS] MALFORMED TARGET: Malformed target=999 flagged correctly.");

        $display("=== P0.4: PASS ALL NATIVE GRAPH MEMORY QUALIFICATION TESTS ===");
        $finish;
    end

endmodule
