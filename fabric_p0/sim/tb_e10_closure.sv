// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_e10_closure
// P0.7 Autonomous E10 Bounded Universe Closure Qualification:
// RESET -> load E10 root state -> discover ready work -> execute -> certify -> commit -> generate successor work -> CLOSED_BOUNDED_UNIVERSE -> HALT

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_e10_closure;

`ifdef CFG_RESTRICT_NULLITY
    parameter int RESTRICT_PROBES_NULLITY = 1;
`else
    parameter int RESTRICT_PROBES_NULLITY = 0;
`endif

    parameter int WORK_CELL_COUNT = 4;
    parameter int DATA_WIDTH      = 32;
    parameter int FRAC_BITS       = 16;
    parameter int STATE_WORDS     = 256;
    parameter int GRAPH_NODES     = 256;
    parameter int GRAPH_EDGES     = 512;

    logic              clk;
    logic              reset_n;
    logic              boot_trigger;
    logic              boot_complete;
    logic              fabric_halted;

    // Work Ingress / Egress
    logic              ingress_valid;
    logic              ingress_ready;
    uow_desc_t         ingress_desc;

    logic              egress_valid;
    logic              egress_ready;
    logic [31:0]       egress_uow_id;
    commit_outcome_t   egress_status;
    cl20_mv_t          egress_result;
    logic [63:0]       egress_evidence_root;

    // Graph Boot Programming Ports
    logic              graph_node_wr_en;
    logic [15:0]       graph_node_wr_addr;
    graph_node_t       graph_node_wr_data;
    logic              graph_edge_wr_en;
    logic [15:0]       graph_edge_wr_addr;
    graph_edge_t       graph_edge_wr_data;

    // Telemetry
    geo_telemetry_t    telemetry;
    logic [63:0]       evidence_root;
    logic [WORK_CELL_COUNT-1:0] active_cells;

    // Closure Engine Signals
    logic              closure_start;
    logic              closure_done;
    closure_status_t   closure_status;
    logic              closure_reached;
    logic              nullity_detected;
    logic [31:0]       metric_probes_discovered;
    logic [31:0]       metric_probes_committed;
    logic [31:0]       metric_cycles;
    logic [31:0]       metric_diag_sum;
    logic [31:0]       metric_offdiag_sum;
    logic [31:0]       metric_edges_mutated;

    always #5 clk = ~clk;

    // Watchdog
    initial begin
        #5000000; // 5ms timeout
        $display("[WATCHDOG TIMEOUT] E10 Closure simulation exceeded time limit!");
        $finish;
    end

    // Instantiate Top-Level Fabric
    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_BITS(FRAC_BITS),
        .STATE_WORDS(STATE_WORDS),
        .GRAPH_NODES(GRAPH_NODES),
        .GRAPH_EDGES(GRAPH_EDGES)
    ) u_fabric (
        .clk(clk),
        .reset_n(reset_n),
        .boot_trigger(boot_trigger),
        .boot_complete(boot_complete),
        .fabric_halted(fabric_halted),
        .ingress_valid(ingress_valid),
        .ingress_ready(ingress_ready),
        .ingress_desc(ingress_desc),
        .egress_valid(egress_valid),
        .egress_ready(egress_ready),
        .egress_uow_id(egress_uow_id),
        .egress_status(egress_status),
        .egress_result(egress_result),
        .egress_evidence_root(egress_evidence_root),
        .graph_node_wr_en(graph_node_wr_en),
        .graph_node_wr_addr(graph_node_wr_addr),
        .graph_node_wr_data(graph_node_wr_data),
        .graph_edge_wr_en(graph_edge_wr_en),
        .graph_edge_wr_addr(graph_edge_wr_addr),
        .graph_edge_wr_data(graph_edge_wr_data),
        .telemetry_out(telemetry),
        .current_evidence_root_out(evidence_root),
        .active_work_cells_out(active_cells)
    );

    // Instantiate E10 Autonomous Closure Engine
    geo_e10_closure_engine #(
        .UNIVERSE_POINTS(6),
        .TOTAL_PROBES(20),
        .BASE_PROBE_STATE_ADDR(16),
        .BASE_SCRATCH_ADDR(48),
        .GRAPH_PROBE_REL(8'hE0),
        .RESTRICT_PROBES_NULLITY(RESTRICT_PROBES_NULLITY)
    ) u_closure_engine (
        .clk(clk),
        .reset_n(reset_n),
        .start(closure_start),
        .done(closure_done),
        .closure_status(closure_status),
        .closure_reached(closure_reached),
        .nullity_detected(nullity_detected),
        .ingress_valid(ingress_valid),
        .ingress_ready(ingress_ready),
        .ingress_desc(ingress_desc),
        .egress_valid(egress_valid),
        .egress_ready(egress_ready),
        .egress_uow_id(egress_uow_id),
        .egress_status(egress_status),
        .egress_result(egress_result),
        .egress_evidence_root(egress_evidence_root),
        .probes_discovered(metric_probes_discovered),
        .probes_committed(metric_probes_committed),
        .total_cycles(metric_cycles),
        .incidence_diag_sum(metric_diag_sum),
        .incidence_offdiag_sum(metric_offdiag_sum),
        .graph_edges_committed(metric_edges_mutated)
    );

    // Task: Load E10 Root State Image into Graph & State Memory
    task load_e10_root_state();
        real theta;
        real pi;
        real cos_val, sin_val;
        int cos_q16, sin_q16;
        pi = 3.14159265358979323846;

        $display("[E10 ROOT LOAD] Initializing 6 universe points {0..5} in Graph & State Memory...");

        // 1. Load 6 universe nodes into Graph Memory
        for (int i = 0; i < 6; i++) begin
            @(posedge clk);
            graph_node_wr_en   = 1'b1;
            graph_node_wr_addr = i;
            graph_node_wr_data = '0;
            graph_node_wr_data.edge_base  = 16'd0;
            graph_node_wr_data.edge_count = 16'd0;
            graph_node_wr_data.node_type  = 8'h01; // Base Universe Element
            graph_node_wr_data.flags      = 8'h00;
            graph_node_wr_data.version    = 16'd1;
        end
        @(posedge clk);
        graph_node_wr_en = 1'b0;

        // 2. Load 6 idempotent geometric states into State Memory State[0..5]
        for (int k = 0; k < 6; k++) begin
            theta   = (2.0 * pi * k) / 6.0;
            cos_val = $cos(theta);
            sin_val = $sin(theta);
            cos_q16 = $rtoi(0.5 * cos_val * 65536.0);
            sin_q16 = $rtoi(0.5 * sin_val * 65536.0);

            // P_k = 0.5 + 0.5*cos(theta)*e1 + 0.5*sin(theta)*e2
            u_fabric.u_state_memory.mem_s[k]   = 32'sh00008000;
            u_fabric.u_state_memory.mem_e1[k]  = cos_q16;
            u_fabric.u_state_memory.mem_e2[k]  = sin_q16;
            u_fabric.u_state_memory.mem_e12[k] = 32'sh00000000;
        end

        $display("[E10 ROOT LOAD] Root state initialized: 6 universe nodes, 6 idempotent geometric states.");
    endtask

    initial begin
        clk                = 0;
        reset_n            = 0;
        boot_trigger       = 0;
        closure_start      = 0;
        egress_ready       = 1;
        graph_node_wr_en   = 0;
        graph_node_wr_addr = 0;
        graph_node_wr_data = '0;
        graph_edge_wr_en   = 0;
        graph_edge_wr_addr = 0;
        graph_edge_wr_data = '0;

        // 1. Power-on reset
        #30 reset_n = 1;
        #20;

        // 2. Trigger autonomous boot
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        while (!boot_complete) @(posedge clk);
        $display("[BOOT] Autonomous boot completed.");

        // 3. Load E10 Root State Image
        load_e10_root_state();

        #50;

        // 4. Start Autonomous E10 Bounded Closure
        $display("[E10 RUN] Launching Autonomous Bounded Closure Subsystem...");
        @(negedge clk);
        closure_start = 1;
        @(negedge clk);
        closure_start = 0;

        // 5. Await autonomous closure and termination
        while (!closure_done) @(posedge clk);

        #100; // Pipeline settle

        $display("=================================================================");
        $display("P0.7 AUTONOMOUS E10 BOUNDED CLOSURE QUALIFICATION REPORT");
        $display("=================================================================");
        $display("Closure Disposition          : %s", (closure_status == CLOSED_BOUNDED_UNIVERSE) ? "CLOSED_BOUNDED_UNIVERSE" : "INCOMPLETE / FAULT");
        $display("Closure Reached Flag         : %0b", closure_reached);
        $display("Total Elapsed Cycles         : %0d", metric_cycles);
        $display("Probes Discovered            : %0d", metric_probes_discovered);
        $display("Probes Committed             : %0d", metric_probes_committed);
        $display("Graph Edges Mutated          : %0d", metric_edges_mutated);
        $display("Incidence Matrix Diag Sum    : %0d (Expected: 60 = 6 * 10)", metric_diag_sum);
        $display("Incidence Matrix Offdiag Sum : %0d (Expected: 120 = 30 * 4)", metric_offdiag_sum);
        $display("Telemetry UoW Admitted       : %0d", telemetry.uow_admitted);
        $display("Telemetry UoW Committed      : %0d", telemetry.uow_committed);
        $display("Telemetry UoW Rejected       : %0d", telemetry.uow_rejected);
        $display("Evidence Records Chained     : %0d", telemetry.evidence_records);
        $display("Final Evidence Chained Root  : 0x%016h", evidence_root);
        $display("=================================================================");

        // Acceptance Validations
        if (RESTRICT_PROBES_NULLITY == 0) begin
            assert(closure_status == CLOSED_BOUNDED_UNIVERSE)
                else $fatal(1, "Expected CLOSED_BOUNDED_UNIVERSE disposition!");
            assert(closure_reached == 1'b1)
                else $fatal(1, "Closure flag not asserted!");
            assert(metric_probes_committed == 20)
                else $fatal(1, "Expected exactly 20 committed probes!");
            assert(metric_edges_mutated == 20)
                else $fatal(1, "Expected exactly 20 committed graph edge mutations!");
            assert(metric_diag_sum == 60)
                else $fatal(1, "Euler-Radon incidence diagonal sum mismatch!");
            assert(metric_offdiag_sum == 120)
                else $fatal(1, "Euler-Radon incidence off-diagonal sum mismatch!");
            assert(telemetry.uow_rejected == 0)
                else $fatal(1, "Unexpected rejected UoWs in valid closure!");
            assert(evidence_root != 64'd0)
                else $fatal(1, "Cryptographic evidence root null!");

            // Graph Mutation Memory Verification: Inspect that node 0 acquired mutated edges
            $display("[GRAPH INSPECTION] Node 0 edge count in hardware: %0d", u_fabric.u_graph_memory.node_edge_count[0]);
            assert(u_fabric.u_graph_memory.node_edge_count[0] > 0)
                else $fatal(1, "Graph memory mutation not reflected in Node 0 edge count!");

            $display("PASS P0.7 AUTONOMOUS E10 BOUNDED CLOSURE QUALIFICATION");
        end else begin
            assert(closure_status == INCOMPLETE_UNIVERSE_NULLITY)
                else $fatal(1, "Expected INCOMPLETE_UNIVERSE_NULLITY disposition!");
            assert(nullity_detected == 1'b1)
                else $fatal(1, "Nullity flag not asserted!");
            assert(closure_reached == 1'b0)
                else $fatal(1, "Incomplete universe falsely reported closure!");
            assert(metric_probes_committed == 10)
                else $fatal(1, "Expected exactly 10 committed probes!");
            $display("PASS P0.7 E10 RESTRICTED NULLITY DETECTION (EXPLICIT NULL SPACE)");
        end
        $finish;
    end

endmodule
