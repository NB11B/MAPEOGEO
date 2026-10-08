// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_fault_timing_qualification
// Milestone P0.8: Spatial Timing & Fault Qualification Testbench
// Validates that physical timing perturbations, stalls, and interleavings do not alter certified semantic outcomes.

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_fault_timing_qualification;

    parameter int WORK_CELL_COUNT    = 8;
    parameter int OPERATOR_LANES     = 4;
    parameter int MEMORY_BANKS       = 4;
    parameter int AUTHORITY_ENGINES  = 4;
    parameter int INGRESS_LANES      = 2;
    parameter int EGRESS_LANES       = 2;
    parameter int DATA_WIDTH         = 32;
    parameter int FRAC_BITS          = 16;
    parameter int STATE_WORDS        = 256;
    parameter int GRAPH_NODES        = 256;
    parameter int GRAPH_EDGES        = 512;
    parameter int GRAPH_QUEUE_DEPTH  = 128;

    parameter int TOTAL_UOWS         = 16;
    parameter int TEST_MODE          = 0; // 0=TOPOLOGY_SWEEP, 1=STALE_RACE, 2=SECURITY_ATTACK, 3=ARITHMETIC_FAULT, 4=QUEUE_PRESSURE, 5=E10_CLOSURE, 6=E10_NULLITY
    parameter int TEST_TOPO          = 0; // 0=INDEP, 1=CHAIN, 2=FANOUT, 3=FANIN, 4=DIAMOND, 5=CONTENTION
    parameter int SEED               = 42;
    parameter int STALL_PROB_PCT     = 25; // Per-cycle stall injection probability (%)
    parameter int STALL_DURATION_MAX = 3;  // Maximum stall pulse duration in cycles
    parameter int NUM_CONTENDERS     = 4;  // For Mode 1 (CAS race)
    parameter int RESTRICT_PROBES_NULLITY = (TEST_MODE == 6) ? 1 : 0;

    localparam logic signed [DATA_WIDTH-1:0] ONE = (1 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] TWO = (2 << FRAC_BITS);

    logic              clk;
    logic              reset_n;
    logic              boot_trigger;
    logic              boot_complete;
    logic              fabric_halted;

    logic [INGRESS_LANES-1:0]           ingress_valid;
    logic [INGRESS_LANES-1:0]           ingress_ready;
    logic [INGRESS_LANES*471-1:0]       ingress_desc;

    logic [EGRESS_LANES-1:0]            egress_valid;
    logic [EGRESS_LANES-1:0]            egress_ready;
    logic [EGRESS_LANES*32-1:0]         egress_uow_id;
    logic [EGRESS_LANES*2-1:0]          egress_status;
    logic [EGRESS_LANES*128-1:0]        egress_result;
    logic [EGRESS_LANES*64-1:0]         egress_evidence_root;

    // Graph Memory Boot Programming
    logic              graph_node_wr_en;
    logic [15:0]       graph_node_wr_addr;
    graph_node_t       graph_node_wr_data;
    logic              graph_edge_wr_en;
    logic [15:0]       graph_edge_wr_addr;
    graph_edge_t       graph_edge_wr_data;

    // Diagnostic & Telemetry
    geo_telemetry_t    telemetry;
    logic [63:0]       evidence_root;
    logic [WORK_CELL_COUNT-1:0] active_cells;

    // P0.8 Physical Timing Perturbation Control Lines
    logic [MEMORY_BANKS-1:0]      stall_inject_mem;
    logic [OPERATOR_LANES-1:0]    stall_inject_operator;
    logic [AUTHORITY_ENGINES-1:0] stall_inject_authority;
    logic [63:0]                  semantic_evidence_root;

    always #5 clk = ~clk;

    // DUT Instantiation
    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .OPERATOR_LANES(OPERATOR_LANES),
        .MEMORY_BANKS(MEMORY_BANKS),
        .AUTHORITY_ENGINES(AUTHORITY_ENGINES),
        .INGRESS_LANES(INGRESS_LANES),
        .EGRESS_LANES(EGRESS_LANES),
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_BITS(FRAC_BITS),
        .STATE_WORDS(STATE_WORDS),
        .GRAPH_NODES(GRAPH_NODES),
        .GRAPH_EDGES(GRAPH_EDGES),
        .GRAPH_QUEUE_DEPTH(GRAPH_QUEUE_DEPTH)
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
        .graph_node_wr_en(graph_node_wr_en),
        .graph_node_wr_addr(graph_node_wr_addr),
        .graph_node_wr_data(graph_node_wr_data),
        .graph_edge_wr_en(graph_edge_wr_en),
        .graph_edge_wr_addr(graph_edge_wr_addr),
        .graph_edge_wr_data(graph_edge_wr_data),
        .telemetry_out(telemetry),
        .current_evidence_root_out(evidence_root),
        .active_work_cells_out(active_cells),
        .stall_inject_mem(stall_inject_mem),
        .stall_inject_operator(stall_inject_operator),
        .stall_inject_authority(stall_inject_authority),
        .semantic_evidence_root_out(semantic_evidence_root)
    );

    // Watchdog
    initial begin
        #10000000; // 10ms timeout
        $display("[WATCHDOG TIMEOUT] Simulation exceeded 10,000,000 ns in Test Mode %0d!", act_mode);
        $fatal(1, "Watchdog timeout in spatial fault/timing benchmark");
    end

    // Dynamic test configuration (defaults from parameters, overridable via plusargs)
    int act_mode;
    int act_topo;
    int act_seed;
    int act_stall;
    int act_contenders;
    int act_total_uows;
    int expected_completions;

    // Hang diagnostic monitor
    integer last_change_time;
    integer last_cc;
    initial begin
        last_change_time = 0;
        last_cc = 0;
        forever begin
            #1000;
            if (completed_count != last_cc) begin
                last_cc = completed_count;
                last_change_time = $time;
            end else if (($time - last_change_time > 50000) && (expected_completions > 0) &&
                         (uow_idx >= expected_completions) && (completed_count < expected_completions)) begin
                $display("[DEBUG HANG] Time=%0t completed_count=%0d uow_committed=%0d active_cells=%b",
                         $time, completed_count, telemetry.uow_committed, active_cells);
                $display("  stall_mem=%b stall_op=%b stall_auth=%b", stall_inject_mem, stall_inject_operator, stall_inject_authority);
                $display("  egress_valid=%b egress_ready=%b cmpl_count=%0d", egress_valid, egress_ready, dut.u_work_fabric.cmpl_count);
                for (int c = 0; c < WORK_CELL_COUNT; c++) begin
                    $display("  cell[%0d]: state=%0d uow=%0d is_active=%0d disp=%0d cert_req=%b cert_done=%b",
                             c, dut.u_work_fabric.cell_state[c],
                             dut.u_work_fabric.cell_active_uow[c],
                             dut.u_work_fabric.cell_active_mask[c],
                             dut.u_work_fabric.cell_disp[c],
                             dut.u_work_fabric.cell_cert_req[c],
                             dut.u_work_fabric.cell_cert_done[c]);
                end
                $fatal(1, "Benchmark hung");
            end
        end
    end

    // --- Deterministic Xorshift32 PRNG ---
    function automatic logic [31:0] xorshift32(input logic [31:0] state);
        logic [31:0] x;
        x = (state == 32'd0) ? 32'hDEADBEEF : state;
        x = x ^ (x << 13);
        x = x ^ (x >> 17);
        x = x ^ (x << 5);
        return x;
    endfunction

    // Per-domain PRNG state and stall timers
    logic [31:0] prng_mem      [0:MEMORY_BANKS-1];
    integer      timer_mem     [0:MEMORY_BANKS-1];

    logic [31:0] prng_op       [0:OPERATOR_LANES-1];
    integer      timer_op      [0:OPERATOR_LANES-1];

    logic [31:0] prng_auth     [0:AUTHORITY_ENGINES-1];
    integer      timer_auth    [0:AUTHORITY_ENGINES-1];

    logic [31:0] prng_egress   [0:EGRESS_LANES-1];
    integer      timer_egress  [0:EGRESS_LANES-1];

    logic enable_perturbations;
    logic throttle_egress_adversarial;

    // Perturbation Engine
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            stall_inject_mem       <= '0;
            stall_inject_operator  <= '0;
            stall_inject_authority <= '0;
            for (int b = 0; b < MEMORY_BANKS; b++) begin
                prng_mem[b]  <= act_seed * 1000 + b * 37 + 1;
                timer_mem[b] <= 0;
            end
            for (int l = 0; l < OPERATOR_LANES; l++) begin
                prng_op[l]   <= act_seed * 2000 + l * 41 + 2;
                timer_op[l]  <= 0;
            end
            for (int a = 0; a < AUTHORITY_ENGINES; a++) begin
                prng_auth[a]  <= act_seed * 3000 + a * 43 + 3;
                timer_auth[a] <= 0;
            end
            for (int k = 0; k < EGRESS_LANES; k++) begin
                prng_egress[k]  <= act_seed * 4000 + k * 47 + 4;
                timer_egress[k] <= 0;
                egress_ready[k] <= 1'b1;
            end
        end else if (enable_perturbations) begin
            // 1. Memory Bank Stalls
            for (int b = 0; b < MEMORY_BANKS; b++) begin
                if (timer_mem[b] > 0) begin
                    timer_mem[b]            <= timer_mem[b] - 1;
                    stall_inject_mem[b]     <= 1'b1;
                end else begin
                    logic [31:0] nxt;
                    nxt = xorshift32(prng_mem[b]);
                    prng_mem[b] <= nxt;
                    if ((nxt % 100) < act_stall) begin
                        timer_mem[b]        <= 1 + (nxt[18:16] % STALL_DURATION_MAX);
                        stall_inject_mem[b] <= 1'b1;
                    end else begin
                        stall_inject_mem[b] <= 1'b0;
                    end
                end
            end

            // 2. Operator Lane Stalls
            for (int l = 0; l < OPERATOR_LANES; l++) begin
                if (timer_op[l] > 0) begin
                    timer_op[l]               <= timer_op[l] - 1;
                    stall_inject_operator[l]  <= 1'b1;
                end else begin
                    logic [31:0] nxt;
                    nxt = xorshift32(prng_op[l]);
                    prng_op[l] <= nxt;
                    if ((nxt % 100) < act_stall) begin
                        timer_op[l]              <= 1 + (nxt[18:16] % STALL_DURATION_MAX);
                        stall_inject_operator[l] <= 1'b1;
                    end else begin
                        stall_inject_operator[l] <= 1'b0;
                    end
                end
            end

            // 3. Authority Engine Stalls
            for (int a = 0; a < AUTHORITY_ENGINES; a++) begin
                if (timer_auth[a] > 0) begin
                    timer_auth[a]               <= timer_auth[a] - 1;
                    stall_inject_authority[a]   <= 1'b1;
                end else begin
                    logic [31:0] nxt;
                    nxt = xorshift32(prng_auth[a]);
                    prng_auth[a] <= nxt;
                    if ((nxt % 100) < act_stall) begin
                        timer_auth[a]             <= 1 + (nxt[18:16] % STALL_DURATION_MAX);
                        stall_inject_authority[a] <= 1'b1;
                    end else begin
                        stall_inject_authority[a] <= 1'b0;
                    end
                end
            end

            // 4. Egress Ready Throttling
            for (int k = 0; k < EGRESS_LANES; k++) begin
                if (throttle_egress_adversarial) begin
                    // In Mode 4: 90% stall to build massive backpressure
                    logic [31:0] nxt;
                    nxt = xorshift32(prng_egress[k]);
                    prng_egress[k]  <= nxt;
                    egress_ready[k] <= ((nxt % 100) >= 90);
                end else begin
                    if (timer_egress[k] > 0) begin
                        timer_egress[k] <= timer_egress[k] - 1;
                        egress_ready[k] <= 1'b0;
                    end else begin
                        logic [31:0] nxt;
                        nxt = xorshift32(prng_egress[k]);
                        prng_egress[k] <= nxt;
                        if ((nxt % 100) < act_stall) begin
                            timer_egress[k] <= 1 + (nxt[18:16] % STALL_DURATION_MAX);
                            egress_ready[k] <= 1'b0;
                        end else begin
                            egress_ready[k] <= 1'b1;
                        end
                    end
                end
            end
        end else begin
            stall_inject_mem       <= '0;
            stall_inject_operator  <= '0;
            stall_inject_authority <= '0;
            for (int k = 0; k < EGRESS_LANES; k++) begin
                egress_ready[k] <= 1'b1;
            end
        end
    end

    // Egress Tracking
    integer completed_count;
    integer committed_count;
    integer refused_count;
    integer rejected_count;
    integer fault_count;
    integer uow_idx;
    logic [63:0] last_egress_evidence_root;

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            completed_count           <= 0;
            committed_count           <= 0;
            refused_count             <= 0;
            rejected_count            <= 0;
            fault_count               <= 0;
            last_egress_evidence_root <= '0;
        end else begin
            int inc_cmpl;
            int inc_comm;
            int inc_ref;
            int inc_rej;
            int inc_flt;
            inc_cmpl = 0;
            inc_comm = 0;
            inc_ref  = 0;
            inc_rej  = 0;
            inc_flt  = 0;
            for (int k = 0; k < EGRESS_LANES; k++) begin
                if (egress_valid[k] && egress_ready[k]) begin
                    commit_outcome_t st;
                    st = commit_outcome_t'(egress_status[k*2 +: 2]);
                    inc_cmpl = inc_cmpl + 1;
                    last_egress_evidence_root <= egress_evidence_root[k*64 +: 64];
                    case (st)
                        OUTCOME_COMMIT: inc_comm = inc_comm + 1;
                        OUTCOME_REFUSE: inc_ref  = inc_ref + 1;
                        OUTCOME_REJECT: inc_rej  = inc_rej + 1;
                        OUTCOME_FAULT:  inc_flt  = inc_flt + 1;
                    endcase
                end
            end
            completed_count <= completed_count + inc_cmpl;
            committed_count <= committed_count + inc_comm;
            refused_count   <= refused_count   + inc_ref;
            rejected_count  <= rejected_count  + inc_rej;
            fault_count     <= fault_count     + inc_flt;
        end
    end

    // Descriptor Builder for Mode 0 (Topologies)
    function automatic uow_desc_t build_mode0_uow(input integer idx, input integer total, input integer topo);
        uow_desc_t d;
        d = '0;
        d.uow_id          = idx + 1;
        d.opcode          = OP_ADD;
        d.pre_state_hash  = 32'd0;
        d.auth_token      = 32'hFFFFFFFF;
        d.imm_operand.s   = ONE;
        d.use_immediate   = 1'b1;
        d.dep_cond        = DEP_COND_BITMASK;

        case (topo)
            0: begin // INDEPENDENT
                d.src_a_addr = (idx * 2) % 64;
                d.src_b_addr = (idx * 2 + 1) % 64;
                d.dest_addr  = 64 + (idx % 64);
                d.dep_mask   = '0;
            end
            1: begin // CHAIN
                if (idx == 0) begin
                    d.src_a_addr = 0;
                    d.src_b_addr = 1;
                    d.dest_addr  = 64;
                    d.dep_mask   = '0;
                end else begin
                    d.src_a_addr = 64 + idx - 1;
                    d.src_b_addr = 1;
                    d.dest_addr  = 64 + idx;
                    d.dep_mask   = (128'b1 << ((idx - 1) % WORK_CELL_COUNT));
                end
            end
            2: begin // FANOUT
                if (idx == 0) begin
                    d.src_a_addr = 0;
                    d.src_b_addr = 1;
                    d.dest_addr  = 64;
                    d.dep_mask   = '0;
                end else begin
                    d.src_a_addr = 64;
                    d.src_b_addr = 1;
                    d.dest_addr  = 70 + idx;
                    d.dep_mask   = 128'b1; // All depend on UoW 0
                end
            end
            3: begin // FANIN
                if (idx < total - 1) begin
                    d.src_a_addr = (idx * 2) % 64;
                    d.src_b_addr = (idx * 2 + 1) % 64;
                    d.dest_addr  = 64 + idx;
                    d.dep_mask   = '0;
                end else begin
                    d.src_a_addr = 64;
                    d.src_b_addr = 65;
                    d.dest_addr  = 90;
                    d.dep_mask   = '0;
                    for (int k = 0; k < total - 1; k++) begin
                        d.dep_mask |= (128'b1 << (k % WORK_CELL_COUNT));
                    end
                end
            end
            4: begin // DIAMOND
                integer grp, pos;
                grp = idx / 4;
                pos = idx % 4;
                if (pos == 0) begin
                    d.src_a_addr = grp * 2;
                    d.src_b_addr = grp * 2 + 1;
                    d.dest_addr  = 64 + grp * 4;
                    d.dep_mask   = '0;
                end else if (pos == 1) begin
                    d.src_a_addr = 64 + grp * 4;
                    d.src_b_addr = 1;
                    d.dest_addr  = 64 + grp * 4 + 1;
                    d.dep_mask   = (128'b1 << ((grp * 4) % WORK_CELL_COUNT));
                end else if (pos == 2) begin
                    d.src_a_addr = 64 + grp * 4;
                    d.src_b_addr = 2;
                    d.dest_addr  = 64 + grp * 4 + 2;
                    d.dep_mask   = (128'b1 << ((grp * 4) % WORK_CELL_COUNT));
                end else begin
                    d.src_a_addr = 64 + grp * 4 + 1;
                    d.src_b_addr = 64 + grp * 4 + 2;
                    d.dest_addr  = 64 + grp * 4 + 3;
                    d.dep_mask   = (128'b1 << ((grp * 4 + 1) % WORK_CELL_COUNT)) |
                                 (128'b1 << ((grp * 4 + 2) % WORK_CELL_COUNT));
                end
            end
            5: begin // HIGH CONTENTION
                // All target the exact same state address & authority domain
                d.src_a_addr = 20;
                d.src_b_addr = 21;
                d.dest_addr  = 50; // Same state memory bank & same authority engine
                d.dep_mask   = '0;
            end
            default: begin
                d.dest_addr = idx % STATE_WORDS;
            end
        endcase
        return d;
    endfunction

    // E10 Closure Signals (for Mode 5 & 6)
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

    logic              e10_ingress_valid;
    logic              e10_ingress_ready;
    uow_desc_t         e10_ingress_desc;
    logic              e10_egress_valid;
    logic              e10_egress_ready;
    logic [31:0]       e10_egress_uow_id;
    commit_outcome_t   e10_egress_status;
    cl20_mv_t          e10_egress_result;
    logic [63:0]       e10_egress_evidence_root;

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
        .ingress_valid(e10_ingress_valid),
        .ingress_ready(e10_ingress_ready),
        .ingress_desc(e10_ingress_desc),
        .egress_valid(e10_egress_valid),
        .egress_ready(e10_egress_ready),
        .egress_uow_id(e10_egress_uow_id),
        .egress_status(e10_egress_status),
        .egress_result(e10_egress_result),
        .egress_evidence_root(e10_egress_evidence_root),
        .probes_discovered(metric_probes_discovered),
        .probes_committed(metric_probes_committed),
        .total_cycles(metric_cycles),
        .incidence_diag_sum(metric_diag_sum),
        .incidence_offdiag_sum(metric_offdiag_sum),
        .graph_edges_committed(metric_edges_mutated)
    );

    // Combinational interface bindings between E10 closure engine and fabric port 0
    assign e10_ingress_ready        = ingress_ready[0];
    assign e10_egress_valid         = egress_valid[0];
    assign e10_egress_ready         = egress_ready[0];
    assign e10_egress_uow_id        = egress_uow_id[31:0];
    assign e10_egress_status        = commit_outcome_t'(egress_status[1:0]);
    assign e10_egress_result        = egress_result[127:0];
    assign e10_egress_evidence_root = egress_evidence_root[63:0];

    // E10 Root State Loader
    task load_e10_root_state();
        real theta;
        real pi;
        real cos_val, sin_val;
        int cos_q16, sin_q16;
        pi = 3.14159265358979323846;

        for (int i = 0; i < 6; i++) begin
            @(posedge clk);
            graph_node_wr_en   = 1'b1;
            graph_node_wr_addr = i;
            graph_node_wr_data = '0;
            graph_node_wr_data.edge_base  = 16'd0;
            graph_node_wr_data.edge_count = 16'd0;
            graph_node_wr_data.node_type  = 8'h01;
            graph_node_wr_data.flags      = 8'h00;
            graph_node_wr_data.version    = 16'd1;
        end
        @(posedge clk);
        graph_node_wr_en = 1'b0;

        for (int k = 0; k < 6; k++) begin
            theta   = (2.0 * pi * k) / 6.0;
            cos_val = $cos(theta);
            sin_val = $sin(theta);
            cos_q16 = $rtoi(0.5 * cos_val * 65536.0);
            sin_q16 = $rtoi(0.5 * sin_val * 65536.0);

            dut.u_state_memory.mem_s[k]   = 32'sh00008000;
            dut.u_state_memory.mem_e1[k]  = cos_q16;
            dut.u_state_memory.mem_e2[k]  = sin_q16;
            dut.u_state_memory.mem_e12[k] = 32'sh00000000;
        end
    endtask

    // Main Test Sequence
    initial begin
        clk                         = 1'b0;
        reset_n                     = 1'b0;
        boot_trigger                = 1'b0;
        ingress_valid               = '0;
        ingress_desc                = '0;
        graph_node_wr_en            = 1'b0;
        graph_node_wr_addr          = '0;
        graph_node_wr_data          = '0;
        graph_edge_wr_en            = 1'b0;
        graph_edge_wr_addr          = '0;
        graph_edge_wr_data          = '0;
        enable_perturbations        = 1'b0;
        throttle_egress_adversarial = 1'b0;
        closure_start               = 1'b0;

        act_mode             = TEST_MODE;
        act_topo             = TEST_TOPO;
        act_seed             = SEED;
        act_stall            = STALL_PROB_PCT;
        act_contenders       = NUM_CONTENDERS;
        act_total_uows       = TOTAL_UOWS;
        expected_completions = TOTAL_UOWS;

        void'($value$plusargs("MODE=%d", act_mode));
        void'($value$plusargs("TOPO=%d", act_topo));
        void'($value$plusargs("SEED=%d", act_seed));
        void'($value$plusargs("STALL_RATE=%d", act_stall));
        void'($value$plusargs("CONTENDERS=%d", act_contenders));
        void'($value$plusargs("TOTAL_UOWS=%d", act_total_uows));

        case (act_mode)
            0: expected_completions = act_total_uows;
            1: expected_completions = act_contenders;
            2: expected_completions = 16;
            3: expected_completions = 8;
            4: expected_completions = 32;
            default: expected_completions = 0;
        endcase

        #40;
        reset_n = 1'b1;
        #20;
        boot_trigger = 1'b1;
        #20;
        boot_trigger = 1'b0;
        wait(boot_complete);
        $display("[BOOT_COMPLETE] Boot sequence finished successfully.");

        // Enable spatial perturbations
        enable_perturbations = 1'b1;

        case (act_mode)
            // =========================================================================
            // Mode 0: Topology Timing Perturbations & Causal Invariance (P0.8.2, P0.8.3)
            // =========================================================================
            0: begin
                $display("[P0.8.2/3] Running Topology Perturbation Sweep: Topo=%0d TotalUoWs=%0d Seed=%0d StallProb=%0d%%",
                         act_topo, act_total_uows, act_seed, act_stall);
                for (int w = 0; w < 64; w++) begin
                    dut.u_state_memory.mem_s[w]   = (w + 1) * ONE;
                    dut.u_state_memory.mem_e1[w]  = '0;
                    dut.u_state_memory.mem_e2[w]  = '0;
                    dut.u_state_memory.mem_e12[w] = '0;
                end
                begin
                    uow_idx = 0;
                    while (uow_idx < act_total_uows) begin
                        int accepted_lanes;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (uow_idx + l < act_total_uows) begin
                                uow_desc_t d;
                                d = build_mode0_uow(uow_idx + l, act_total_uows, act_topo);
                                ingress_desc[l*471 +: 471] = d;
                                ingress_valid[l]           = 1'b1;
                            end else begin
                                ingress_valid[l]           = 1'b0;
                            end
                        end

                        #1;
                        accepted_lanes = 0;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (ingress_valid[l] && ingress_ready[l]) begin
                                accepted_lanes = accepted_lanes + 1;
                            end
                        end

                        @(posedge clk);
                        uow_idx = uow_idx + accepted_lanes;
                        if (accepted_lanes > 0) begin
                            $display("Time %0t: uow_idx=%0d accepted_lanes=%0d", $time, uow_idx, accepted_lanes);
                        end
                        @(negedge clk);
                    end
                    ingress_valid = '0;
                    $display("Time %0t: All UoWs issued! Waiting for completions... current completed_count=%0d", $time, completed_count);
                end

                wait(completed_count == act_total_uows);
                repeat (10) @(posedge clk);

                $display("[SEMANTIC_ROOT] 0x%016h", semantic_evidence_root);
                $display("[PHYSICAL_ROOT] 0x%016h", last_egress_evidence_root);
                $display("[P08_PASS] Mode=0 Topo=%0d Committed=%0d Completed=%0d SemanticRoot=0x%016h",
                         act_topo, committed_count, completed_count, semantic_evidence_root);
            end

            // =========================================================================
            // Mode 1: Stale-State Race Qualification (CAS Atomic Mutex, P0.8.4)
            // =========================================================================
            1: begin
                $display("[P0.8.4] Running Stale-State CAS Race Qualification: Contenders=%0d Seed=%0d",
                         NUM_CONTENDERS, SEED);

                // Set Address 10 version = 1 in state memory
                dut.u_state_memory.versions[10] = 16'd1;
                dut.u_state_memory.mem_s[10]    = 32'sh00010000; // 1.0

                // Concurrently issue act_contenders, all targeting dest_addr=10 with pre_state_hash=1 (version=1)
                begin
                    uow_idx = 0;
                    while (uow_idx < act_contenders) begin
                        int accepted_lanes;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (uow_idx + l < act_contenders) begin
                                uow_desc_t d;
                                d = '0;
                                d.uow_id          = 100 + (uow_idx + l);
                                d.opcode          = OP_ADD;
                                d.dest_addr       = 10; // ALL TARGET ADDRESS 10
                                d.src_a_addr      = 0;
                                d.src_b_addr      = 1;
                                d.pre_state_hash  = 32'd1; // Reads version 1
                                d.auth_token      = 32'hFFFFFFFF;
                                d.imm_operand.s   = (uow_idx + l + 1) << FRAC_BITS;
                                d.use_immediate   = 1'b1;
                                d.dep_cond        = DEP_COND_BITMASK;

                                ingress_desc[l*471 +: 471] = d;
                                ingress_valid[l]           = 1'b1;
                            end else begin
                                ingress_valid[l]           = 1'b0;
                            end
                        end

                        #1;
                        accepted_lanes = 0;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (ingress_valid[l] && ingress_ready[l]) begin
                                accepted_lanes = accepted_lanes + 1;
                            end
                        end

                        @(posedge clk);
                        uow_idx = uow_idx + accepted_lanes;
                        @(negedge clk);
                    end
                    ingress_valid = '0;
                end

                wait(completed_count == act_contenders);
                repeat (10) @(posedge clk);

                $display("[STALE_RACE_PASS] Contenders=%0d Committed=%0d Refused=%0d FinalVersion=%0d",
                         act_contenders, committed_count, refused_count, dut.u_state_memory.versions[10]);
            end

            // =========================================================================
            // Mode 2: Capability / Security Attack Injection Under Load (P0.8.5)
            // =========================================================================
            2: begin
                $display("[P0.8.5] Running Security Attack Injection Under Perturbations: Seed=%0d", act_seed);
                begin
                    uow_idx = 0;
                    while (uow_idx < 16) begin
                        int accepted_lanes;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (uow_idx + l < 16) begin
                                integer cur;
                                uow_desc_t d;
                                cur = uow_idx + l;
                                d = '0;
                                d.uow_id        = 200 + cur;
                                d.opcode        = OP_ADD;
                                d.imm_operand.s = ONE;
                                d.use_immediate = 1'b1;
                                d.dep_cond      = DEP_COND_BITMASK;

                                if (cur % 2 == 0) begin
                                    // VALID UoW
                                    d.dest_addr  = cur + 20;
                                    d.auth_token = 32'hFFFFFFFF; // Authorized
                                end else begin
                                    // ATTACK UoW
                                    if (cur == 1 || cur == 5) begin
                                        d.dest_addr  = cur + 20;
                                        d.auth_token = 32'd0; // Forged / zero capability
                                    end else if (cur == 3 || cur == 7) begin
                                        d.dest_addr         = cur + 20;
                                        d.auth_token        = 32'hFFFFFFFF;
                                        d.has_graph_mut     = 1'b1;
                                        d.graph_mut_cmd     = GRAPH_MUT_ADD_EDGE;
                                        d.graph_mut_node    = 16'd1;
                                        d.graph_mut_target  = 16'd8888; // Target out of bounds
                                    end else begin
                                        d.dest_addr         = cur + 20;
                                        d.auth_token        = 32'hFFFFFFFF;
                                        d.has_graph_mut     = 1'b1;
                                        d.graph_mut_cmd     = GRAPH_MUT_ADD_EDGE;
                                        d.graph_mut_node    = 16'd9999; // Node out of bounds
                                        d.graph_mut_target  = 16'd1;
                                    end
                                end

                                ingress_desc[l*471 +: 471] = d;
                                ingress_valid[l]           = 1'b1;
                            end else begin
                                ingress_valid[l]           = 1'b0;
                            end
                        end

                        #1;
                        accepted_lanes = 0;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (ingress_valid[l] && ingress_ready[l]) begin
                                accepted_lanes = accepted_lanes + 1;
                            end
                        end

                        @(posedge clk);
                        uow_idx = uow_idx + accepted_lanes;
                        @(negedge clk);
                    end
                    ingress_valid = '0;
                end

                wait(completed_count == 16);
                repeat (10) @(posedge clk);

                $display("[SECURITY_ATTACK_PASS] ValidCommitted=%0d IllegalBlocked=%0d ZeroIllegalMutations=1",
                         committed_count, (refused_count + rejected_count + fault_count));
            end

            // =========================================================================
            // Mode 3: Arithmetic & Multivector Fault Injection (P0.8.6, P0.8.7)
            // =========================================================================
            3: begin
                $display("[P0.8.6/7] Running Arithmetic Overflow Fault Qualification: Seed=%0d", act_seed);
                begin
                    uow_idx = 0;
                    while (uow_idx < 8) begin
                        int accepted_lanes;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (uow_idx + l < 8) begin
                                integer cur;
                                uow_desc_t d;
                                cur = uow_idx + l;
                                d = '0;
                                d.uow_id        = 300 + cur;
                                d.dest_addr     = cur + 30;
                                d.auth_token    = 32'hFFFFFFFF;
                                d.use_immediate = 1'b1;
                                d.dep_cond      = DEP_COND_BITMASK;

                                if (cur % 2 == 0) begin
                                    d.opcode        = OP_ADD;
                                    d.src_a_addr    = cur + 10;
                                    dut.u_state_memory.mem_s[cur + 10] = ONE;
                                    d.imm_operand.s = ONE;
                                end else begin
                                    d.opcode          = OP_MUL;
                                    d.imm_operand.s   = 32'sh7FFFFFFF;
                                    dut.u_state_memory.mem_s[0] = 32'sh7FFFFFFF;
                                    d.src_a_addr      = 0;
                                end

                                ingress_desc[l*471 +: 471] = d;
                                ingress_valid[l]           = 1'b1;
                            end else begin
                                ingress_valid[l]           = 1'b0;
                            end
                        end

                        #1;
                        accepted_lanes = 0;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (ingress_valid[l] && ingress_ready[l]) begin
                                accepted_lanes = accepted_lanes + 1;
                            end
                        end

                        @(posedge clk);
                        uow_idx = uow_idx + accepted_lanes;
                        @(negedge clk);
                    end
                    ingress_valid = '0;
                end

                wait(completed_count == 8);
                repeat (10) @(posedge clk);

                $display("[FAULT_INJECTION_PASS] NormalCommitted=%0d FaultsDetected=%0d ZeroFaultMutations=1",
                         committed_count, fault_count);
            end

            // =========================================================================
            // Mode 4: Queue Pressure & Adversarial Saturation (P0.8.8)
            // =========================================================================
            4: begin
                $display("[P0.8.8] Running Adversarial Queue Saturation: WORK_CELLS=%0d TOTAL_UOWS=32", WORK_CELL_COUNT);
                throttle_egress_adversarial = 1'b1;

                begin
                    uow_idx = 0;
                    while (uow_idx < 32) begin
                        int accepted_lanes;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (uow_idx + l < 32) begin
                                integer cur;
                                uow_desc_t d;
                                cur = uow_idx + l;
                                d = '0;
                                d.uow_id        = 400 + cur;
                                d.opcode        = OP_ADD;
                                d.dest_addr     = cur % STATE_WORDS;
                                d.auth_token    = 32'hFFFFFFFF;
                                d.imm_operand.s = ONE;
                                d.use_immediate = 1'b1;
                                d.dep_cond      = DEP_COND_BITMASK;

                                ingress_desc[l*471 +: 471] = d;
                                ingress_valid[l]           = 1'b1;
                            end else begin
                                ingress_valid[l]           = 1'b0;
                            end
                        end

                        #1;
                        accepted_lanes = 0;
                        for (int l = 0; l < INGRESS_LANES; l++) begin
                            if (ingress_valid[l] && ingress_ready[l]) begin
                                accepted_lanes = accepted_lanes + 1;
                            end
                        end

                        @(posedge clk);
                        uow_idx = uow_idx + accepted_lanes;
                        @(negedge clk);
                    end
                    ingress_valid = '0;
                end

                repeat (40) @(posedge clk);
                throttle_egress_adversarial = 1'b0;

                wait(completed_count == 32);
                repeat (10) @(posedge clk);

                $display("[QUEUE_PRESSURE_PASS] BackpressureCycles=%0d PeakOccupancy=%0d Completed=%0d",
                         telemetry.backpressure_cycles, telemetry.peak_queue_occupancy, completed_count);
            end

            // =========================================================================
            // Mode 5 & Mode 6: E10 Autonomous Closure & Restricted Nullity Under Stalls (P0.8.10)
            // =========================================================================
            5, 6: begin
                $display("[P0.8.10] Running E10 Closure Under Heavy Stalls: Mode=%0d StallProb=%0d%% Seed=%0d",
                         act_mode, act_stall, act_seed);
                load_e10_root_state();

                // Combinational driver from E10 closure engine into top-level ingress port 0
                fork
                    forever @(*) begin
                        ingress_valid[0]           = e10_ingress_valid;
                        ingress_desc[0*471 +: 471] = e10_ingress_desc;
                    end
                join_none

                @(posedge clk);
                closure_start = 1'b1;
                @(posedge clk);
                closure_start = 1'b0;

                wait(closure_done);
                repeat (10) @(posedge clk);

                if (act_mode == 5) begin
                    $display("[E10_STALL_CLOSURE_PASS] Status=CLOSED_BOUNDED_UNIVERSE ProbesCommitted=%0d EdgesMutated=%0d EvidenceRoot=0x%016h",
                             metric_probes_committed, metric_edges_mutated, evidence_root);
                end else begin
                    $display("[E10_STALL_NULLITY_PASS] Status=INCOMPLETE_UNIVERSE_NULLITY NullityDetected=%0d FinalRoot=0x%016h",
                             nullity_detected, evidence_root);
                end
            end

            default: begin
                $display("[ERROR] Unknown TEST_MODE=%0d", TEST_MODE);
                $fatal(1);
            end
        endcase

        #100;
        $finish;
    end

endmodule
