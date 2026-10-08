// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_single_uow
// P0.2 Autonomous Single-UoW Execution Testbench without Host Intervention

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_single_uow;

    parameter int WORK_CELL_COUNT = 4;
    parameter int DATA_WIDTH      = 32;
    parameter int FRAC_BITS       = 16;
    parameter int STATE_WORDS     = 256;

    localparam logic signed [DATA_WIDTH-1:0] ONE = (1 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] TWO = (2 << FRAC_BITS);

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

    initial begin
        #20000;
        $display("[WATCHDOG TIMEOUT] Simulation reached 20,000ns!");
        $display("cell[0] state=%0d, active_cells=%b, boot_complete=%b, ingress_ready=%b",
            dut.u_work_fabric.gen_cells[0].u_cell.cell_state,
            active_cells, boot_complete, ingress_ready);
        $finish;
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

    logic [63:0] initial_evidence_root;
    cl20_mv_t state_before_test;

    initial begin
        clk           = 0;
        reset_n       = 0;
        boot_trigger  = 0;
        ingress_valid = 0;
        ingress_desc  = '0;
        egress_ready  = 1;

        #20 reset_n = 1;
        #10;
        $monitor("t=%0t rst=%b trig=%b fsm=%0d done=%b", $time, reset_n, boot_trigger, dut.boot_fsm, boot_complete);
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        // Wait for autonomous boot completion
        while (!boot_complete) @(posedge clk);
        $display("[BOOT] Autonomous boot completed successfully. Internal capabilities enumerated.");

        initial_evidence_root = evidence_root;

        // Pre-populate state memory addresses 1 and 2 for the UoW input operands
        // Addr 1: A = 1*e1
        // Addr 2: B = 1*e2
        dut.u_state_memory.mem_e1[1] = ONE;
        dut.u_state_memory.mem_e2[2] = ONE;

        // --- Step 2: Ingress 1 complete UoW ---
        // UoW 101: CL20 product of State[1] and State[2] -> Destination State[3]
        // Expected outcome: e1 * e2 = 1*e12
        @(negedge clk);
        ingress_valid               = 1'b1;
        ingress_desc.uow_id         = 32'd101;
        ingress_desc.opcode         = OP_CL20_PRODUCT;
        ingress_desc.src_a_addr     = 8'd1;
        ingress_desc.src_b_addr     = 8'd2;
        ingress_desc.dest_addr      = 8'd3;
        ingress_desc.dep_mask       = 16'd0; // No dependencies
        ingress_desc.pre_state_hash = 32'd0;
        ingress_desc.auth_token     = 32'hFFFFFFFF; // Full authority
        ingress_desc.use_immediate  = 1'b0;

        @(posedge clk);
        while (!ingress_ready) @(posedge clk);
        @(negedge clk);
        ingress_valid = 1'b0;

        $display("[INGRESS] Loaded UoW 101 into fabric. Withdrawing host interaction.");

        // --- Step 3: Fabric executes autonomously without host participation ---
        // We simply observe egress!
        while (!egress_valid) @(posedge clk);

        $display("[EGRESS] Received autonomous egress signal: UoW=%0d, status=%0d", egress_uow_id, egress_status);

        if (egress_uow_id !== 32'd101) $fatal(1, "Egress UoW ID mismatch: %0d != 101", egress_uow_id);
        if (egress_status !== OUTCOME_COMMIT) $fatal(1, "Egress status was not COMMIT: %0d", egress_status);
        if (egress_result.e12 !== ONE || egress_result.s !== 0 || egress_result.e1 !== 0 || egress_result.e2 !== 0)
            $fatal(1, "Egress computation incorrect: e12=%0d (expected %0d)", egress_result.e12, ONE);

        // Verify Authoritative state memory was committed
        if (dut.u_state_memory.mem_e12[3] !== ONE)
            $fatal(1, "Authoritative memory state[3] was not committed correctly");

        // Verify Evidence Engine chained root was updated
        if (evidence_root === initial_evidence_root)
            $fatal(1, "Evidence root was not updated upon commit");

        if (telemetry.uow_committed !== 32'd1)
            $fatal(1, "Telemetry uow_committed mismatch: %0d != 1", telemetry.uow_committed);

        $display("[EVIDENCE] Chained root updated: 0x%016h -> 0x%016h", initial_evidence_root, evidence_root);

        // --- Step 4: Zero-Mutation Guarantee Verification on Unauthorized Work ---
        // Save current memory state at addr 4
        dut.u_state_memory.mem_s[4]   = 32'h12345678;
        dut.u_state_memory.mem_e1[4]  = 32'hAABBCCDD;
        dut.u_state_memory.mem_e2[4]  = 32'h00112233;
        dut.u_state_memory.mem_e12[4] = 32'h44556677;

        state_before_test.s   = dut.u_state_memory.mem_s[4];
        state_before_test.e1  = dut.u_state_memory.mem_e1[4];
        state_before_test.e2  = dut.u_state_memory.mem_e2[4];
        state_before_test.e12 = dut.u_state_memory.mem_e12[4];

        // Ingress UoW 102 with unauthorized token targeting state[4]
        @(negedge clk);
        ingress_valid               = 1'b1;
        ingress_desc.uow_id         = 32'd102;
        ingress_desc.opcode         = OP_ADD;
        ingress_desc.src_a_addr     = 8'd1;
        ingress_desc.src_b_addr     = 8'd2;
        ingress_desc.dest_addr      = 8'd4;
        ingress_desc.dep_mask       = 16'd0;
        ingress_desc.pre_state_hash = 32'd0;
        ingress_desc.auth_token     = 32'h00000000; // ZERO capability! Authority check MUST fail!
        ingress_desc.use_immediate  = 1'b0;

        @(posedge clk);
        while (!ingress_ready) @(posedge clk);
        @(negedge clk);
        ingress_valid = 1'b0;

        // Wait for autonomous evaluation
        while (!egress_valid) @(posedge clk);

        $display("[AUTH CHECK] Received egress for unauthorized UoW 102: status=%0d", egress_status);

        if (egress_status === OUTCOME_COMMIT)
            $fatal(1, "SECURITY VIOLATION: Unauthorized work was committed!");

        // Assert ZERO-MUTATION GUARANTEE (Section 9.3: Delta S = 0)
        if (dut.u_state_memory.mem_s[4]   !== state_before_test.s   ||
            dut.u_state_memory.mem_e1[4]  !== state_before_test.e1  ||
            dut.u_state_memory.mem_e2[4]  !== state_before_test.e2  ||
            dut.u_state_memory.mem_e12[4] !== state_before_test.e12)
            $fatal(1, "ZERO-MUTATION GUARANTEE VIOLATED: Authoritative state mutated after reject!");

        $display("[AUTH CHECK] Zero-mutation guarantee confirmed: Delta S == 0.");

        $display("=== P0.2: PASS AUTONOMOUS SINGLE-UoW EXECUTION QUALIFICATION ===");
        $finish;
    end

endmodule
