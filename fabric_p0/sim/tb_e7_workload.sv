// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_e7_workload
// P0.6 E7 Hardware Workload Qualification: Autonomous 15-bit hardware triple generation,
// dual composition (R1 = Pu * Pv, R2 = R1 * Pw), throughput telemetry,
// and kappa-only collision vs oriented separation verification.

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_e7_workload;

`ifdef CFG_WORK_CELL_COUNT
    parameter int WORK_CELL_COUNT = `CFG_WORK_CELL_COUNT;
`else
    parameter int WORK_CELL_COUNT = 4;
`endif

`ifdef CFG_TOTAL_TRIPLES
    parameter int TOTAL_TRIPLES = `CFG_TOTAL_TRIPLES;
`else
    parameter int TOTAL_TRIPLES = 64; // Parameterized: 64, 512, 4096, 32768
`endif
    localparam int DATA_WIDTH     = 32;
    localparam int FRAC_BITS      = 16;
    localparam int STATE_WORDS    = 256;

    logic              clk;
    logic              reset_n;
    logic              boot_trigger;
    logic              boot_complete;
    logic              fabric_halted;

    logic              gen_start;
    logic              gen_done;

    logic              ingress_valid;
    logic              ingress_ready;
    uow_desc_t         ingress_desc;

    logic              egress_valid;
    logic              egress_ready;
    logic [31:0]       egress_uow_id;
    commit_outcome_t   egress_status;
    cl20_mv_t          egress_result;
    logic [63:0]       egress_evidence_root;

    geo_telemetry_t    telemetry;
    logic [63:0]       evidence_root;
    logic [WORK_CELL_COUNT-1:0] active_cells;

    logic [31:0]       metric_triples;
    logic [31:0]       metric_cycles;
    logic [31:0]       metric_kappa_colls;
    logic [31:0]       metric_oriented_seps;

    always #5 clk = ~clk;

    initial begin
        #(TOTAL_TRIPLES * 300 + 2000000); // Dynamic timeout: 300ns per triple + 2ms boot/settle
        $display("[WATCHDOG TIMEOUT] E7 Simulation exceeded time limit!");
        $finish;
    end

    // Instantiate Fabric
    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_BITS(FRAC_BITS),
        .STATE_WORDS(STATE_WORDS)
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
        .graph_node_wr_en(1'b0),
        .graph_node_wr_addr(16'd0),
        .graph_node_wr_data('0),
        .graph_edge_wr_en(1'b0),
        .graph_edge_wr_addr(16'd0),
        .graph_edge_wr_data('0),
        .telemetry_out(telemetry),
        .current_evidence_root_out(evidence_root),
        .active_work_cells_out(active_cells)
    );

    // Instantiate E7 Hardware Workload Generator
    geo_e7_work_generator #(
        .TOTAL_TRIPLES(TOTAL_TRIPLES),
        .BASE_PROJECTOR_ADDR(0),
        .BASE_SCRATCH_ADDR(32)
    ) u_generator (
        .clk(clk),
        .reset_n(reset_n),
        .start(gen_start),
        .done(gen_done),
        .ingress_valid(ingress_valid),
        .ingress_ready(ingress_ready),
        .ingress_desc(ingress_desc),
        .egress_valid(egress_valid),
        .egress_ready(egress_ready),
        .egress_uow_id(egress_uow_id),
        .egress_status(egress_status),
        .egress_result(egress_result),
        .egress_evidence_root(egress_evidence_root),
        .total_triples_completed(metric_triples),
        .total_cycles(metric_cycles),
        .kappa_collisions_detected(metric_kappa_colls),
        .oriented_separations_detected(metric_oriented_seps)
    );

    // Egress debug monitor
    always_ff @(posedge clk) begin
        if (egress_valid && egress_ready) begin
            if (egress_status != OUTCOME_COMMIT) begin
                $display("[REJECT] UoW=%0d (step=%0d, triple=%0d), status=%0d, failed_checks=0x%02h",
                    egress_uow_id, egress_uow_id[31:16], egress_uow_id[15:0], egress_status,
                    u_fabric.u_work_fabric.auth_failed_checks[0]);
            end
        end
    end

    // Task to initialize 32 Projectors P_0 .. P_31
    task init_projectors();
        real theta;
        real pi;
        real cos_val, sin_val;
        int cos_q16, sin_q16;
        pi = 3.14159265358979323846;

        for (int k = 0; k < 32; k++) begin
            theta   = (2.0 * pi * k) / 32.0;
            cos_val = $cos(theta);
            sin_val = $sin(theta);
            cos_q16 = $rtoi(0.5 * cos_val * 65536.0);
            sin_q16 = $rtoi(0.5 * sin_val * 65536.0);

            // P_k = 0.5 + 0.5*cos(theta)*e1 + 0.5*sin(theta)*e2
            u_fabric.u_state_memory.mem_s[k]   = 32'sh00008000; // 0.5 in Q16.16
            u_fabric.u_state_memory.mem_e1[k]  = cos_q16;
            u_fabric.u_state_memory.mem_e2[k]  = sin_q16;
            u_fabric.u_state_memory.mem_e12[k] = 32'sh00000000;
        end
        $display("[E7 INIT] 32 idempotent projectors initialized in State[0..31].");
    endtask

    initial begin
        clk          = 0;
        reset_n      = 0;
        boot_trigger = 0;
        gen_start    = 0;
        egress_ready = 1;

        #20 reset_n = 1;
        #10;
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        while (!boot_complete) @(posedge clk);
        $display("[BOOT] Autonomous boot completed.");

        // Initialize 32 idempotent projectors
        init_projectors();

        // Trigger autonomous hardware workload generator
        @(negedge clk);
        gen_start = 1;
        @(negedge clk);
        gen_start = 0;

        // Await autonomous execution and termination
        while (!gen_done) @(posedge clk);

        #100; // Settle pipeline

        $display("=================================================================");
        $display("P0.6 E7 HARDWARE WORKLOAD QUALIFICATION REPORT");
        $display("=================================================================");
        $display("Triples Completed            : %0d", metric_triples);
        $display("Total Elapsed Cycles         : %0d", metric_cycles);
        $display("Cycles Per Triple            : %0f", (metric_cycles * 1.0) / metric_triples);
        $display("Effective Multiplier Ops     : %0d", telemetry.ops_executed);
        $display("Telemetry UoW Admitted       : %0d", telemetry.uow_admitted);
        $display("Telemetry UoW Committed      : %0d", telemetry.uow_committed);
        $display("Telemetry UoW Rejected       : %0d", telemetry.uow_rejected);
        $display("Evidence Records Chained     : %0d", telemetry.evidence_records);
        $display("Final Evidence Chained Root  : 0x%016h", evidence_root);
        $display("Oriented Separations Seen    : %0d", metric_oriented_seps);
        $display("Kappa Collisions Detected    : %0d", metric_kappa_colls);
        $display("=================================================================");

        assert(metric_triples == TOTAL_TRIPLES)
            else $fatal(1, "Mismatch in completed triples count!");
        assert(metric_oriented_seps > 0)
            else $fatal(1, "Expected oriented bivector separations, got 0!");
        assert(evidence_root != 64'd0)
            else $fatal(1, "Evidence root null!");

        $display("PASS P0.6 E7 HARDWARE WORKLOAD QUALIFICATION");
        $finish;
    end

endmodule
