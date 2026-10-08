// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_concurrent_uow
// P0.3 Concurrent UoW Execution & Physical Reordering Invariance Testbench

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_concurrent_uow;

    parameter int WORK_CELL_COUNT = 4;
    parameter int DATA_WIDTH      = 32;
    parameter int FRAC_BITS       = 16;
    parameter int STATE_WORDS     = 256;

    localparam logic signed [DATA_WIDTH-1:0] ONE  = (1 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] TWO  = (2 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] THREE= (3 << FRAC_BITS);

    logic              clk;
    logic              reset_n;
    logic              boot_trigger;
    logic              boot_complete;
    logic              fabric_halted;

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

    always #5 clk = ~clk;

    always @(posedge clk) begin
        if (egress_valid) begin
            $display("[EGRESS DEBUG] t=%0t uow_id=%0d status=%0d result_s=%0d",
                $time, egress_uow_id, egress_status, egress_result.s >> FRAC_BITS);
        end
    end

    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_BITS(FRAC_BITS),
        .STATE_WORDS(STATE_WORDS)
    ) dut (
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
        .telemetry_out(telemetry),
        .current_evidence_root_out(evidence_root),
        .active_work_cells_out(active_cells)
    );

    // Watchdog
    initial begin
        #50000;
        $display("[WATCHDOG TIMEOUT] Simulation reached 50,000ns!");
        $fatal(1, "Watchdog timeout");
    end

    // Storage for Run 1 vs Run 2 comparison
    cl20_mv_t run1_state_10, run1_state_11, run1_state_12;
    cl20_mv_t run2_state_10, run2_state_11, run2_state_12;
    logic [63:0] run1_evidence_root, run2_evidence_root;

    task boot_fabric;
    begin
        reset_n = 0;
        boot_trigger = 0;
        ingress_valid = 0;
        ingress_desc = '0;
        egress_ready = 1;
        #20 reset_n = 1;
        #10;
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;
        while (!boot_complete) @(posedge clk);
    end
    endtask

    task send_uow(
        input logic [31:0] uow_id,
        input geo_opcode_t opcode,
        input logic [7:0]  src_a,
        input logic [7:0]  src_b,
        input logic [7:0]  dest,
        input logic [15:0] dep_mask
    );
    begin
        @(negedge clk);
        ingress_valid               = 1'b1;
        ingress_desc.uow_id         = uow_id;
        ingress_desc.opcode         = opcode;
        ingress_desc.src_a_addr     = src_a;
        ingress_desc.src_b_addr     = src_b;
        ingress_desc.dest_addr      = dest;
        ingress_desc.dep_mask       = dep_mask;
        ingress_desc.pre_state_hash = 32'd0;
        ingress_desc.auth_token     = 32'hFFFFFFFF;
        ingress_desc.use_immediate  = 1'b0;

        @(posedge clk);
        while (!ingress_ready) @(posedge clk);
        @(negedge clk);
        ingress_valid = 1'b0;
    end
    endtask

    initial begin
        clk = 0;

        $display("=== P0.3: BEGIN CONCURRENT UoW EXECUTION QUALIFICATION ===");

        // ==========================================
        // RUN 1: Ingress order: UoW 201 -> UoW 202 -> UoW 203 (dependent)
        $display("[RUN 1] Starting Run 1 with standard dispatch order...");
        boot_fabric();

        // Initialize state operands
        dut.u_state_memory.mem_s[1] = ONE;   // State[1] = 1
        dut.u_state_memory.mem_s[2] = TWO;   // State[2] = 2
        dut.u_state_memory.mem_s[3] = THREE; // State[3] = 3
        dut.u_state_memory.mem_s[4] = TWO;   // State[4] = 2

        // UoW 201: state[1] + state[2] -> state[10] (cell 0, no deps)
        send_uow(32'd201, OP_ADD, 8'd1, 8'd2, 8'd10, 16'd0);

        // UoW 202: state[3] - state[4] -> state[11] (cell 1, no deps)
        send_uow(32'd202, OP_SUB, 8'd3, 8'd4, 8'd11, 16'd0);

        // UoW 203: state[10] + state[11] -> state[12] (cell 2, depends on cell 0 and cell 1)
        send_uow(32'd203, OP_ADD, 8'd10, 8'd11, 8'd12, 16'b0000000000000011);

        // Wait until all 3 UoWs commit autonomously
        while (telemetry.uow_committed < 3) @(posedge clk);

        // Record terminal state
        run1_state_10.s   = dut.u_state_memory.mem_s[10];
        run1_state_11.s   = dut.u_state_memory.mem_s[11];
        run1_state_12.s   = dut.u_state_memory.mem_s[12];
        run1_evidence_root = evidence_root;

        $display("[RUN 1] Complete. state[10]=%0d, state[11]=%0d, state[12]=%0d, root=0x%016h",
            run1_state_10.s >> FRAC_BITS,
            run1_state_11.s >> FRAC_BITS,
            run1_state_12.s >> FRAC_BITS,
            run1_evidence_root);

        // Verify correct arithmetic
        // state[10] = 1 + 2 = 3
        // state[11] = 3 - 2 = 1
        // state[12] = 3 + 1 = 4
        if (run1_state_10.s !== (3 << FRAC_BITS)) $fatal(1, "Run 1 state[10] mismatch: %0d != 3", run1_state_10.s >> FRAC_BITS);
        if (run1_state_11.s !== (1 << FRAC_BITS)) $fatal(1, "Run 1 state[11] mismatch: %0d != 1", run1_state_11.s >> FRAC_BITS);
        if (run1_state_12.s !== (4 << FRAC_BITS)) $fatal(1, "Run 1 state[12] mismatch: %0d != 4", run1_state_12.s >> FRAC_BITS);

        #50;

        // ==========================================
        // RUN 2: Reordered independent ingress: UoW 202 -> UoW 201 -> UoW 203
        // ==========================================
        $display("[RUN 2] Starting Run 2 with permuted independent order...");
        boot_fabric();

        // Re-initialize identical state operands
        dut.u_state_memory.mem_s[1] = ONE;   // State[1] = 1
        dut.u_state_memory.mem_s[2] = TWO;   // State[2] = 2
        dut.u_state_memory.mem_s[3] = THREE; // State[3] = 3
        dut.u_state_memory.mem_s[4] = TWO;   // State[4] = 2

        // UoW 202 ingress FIRST: cell 0 gets UoW 202
        send_uow(32'd202, OP_SUB, 8'd3, 8'd4, 8'd11, 16'd0);

        // UoW 201 ingress SECOND: cell 1 gets UoW 201
        send_uow(32'd201, OP_ADD, 8'd1, 8'd2, 8'd10, 16'd0);

        // UoW 203: cell 2 depends on cell 0 and cell 1
        send_uow(32'd203, OP_ADD, 8'd10, 8'd11, 8'd12, 16'b0000000000000011);

        // Wait until all 3 UoWs commit autonomously
        while (telemetry.uow_committed < 3) @(posedge clk);

        // Record terminal state
        run2_state_10.s   = dut.u_state_memory.mem_s[10];
        run2_state_11.s   = dut.u_state_memory.mem_s[11];
        run2_state_12.s   = dut.u_state_memory.mem_s[12];
        run2_evidence_root = evidence_root;

        $display("[RUN 2] Complete. state[10]=%0d, state[11]=%0d, state[12]=%0d, root=0x%016h",
            run2_state_10.s >> FRAC_BITS,
            run2_state_11.s >> FRAC_BITS,
            run2_state_12.s >> FRAC_BITS,
            run2_evidence_root);

        // ==========================================
        // Equivalence Check (Section 12.4 & 16.3 / 16.4)
        // ==========================================
        if (run1_state_10.s !== run2_state_10.s ||
            run1_state_11.s !== run2_state_11.s ||
            run1_state_12.s !== run2_state_12.s) begin
            $fatal(1, "CONCURRENCY INVARIANCE VIOLATION: Terminal state differs across execution orders!");
        end

        $display("[CONCURRENCY INVARIANCE] Terminal states match exactly: S_f^(1) == S_f^(2).");
        $display("=== P0.3: PASS CONCURRENT UoW EXECUTION QUALIFICATION ===");
        $finish;
    end

endmodule
