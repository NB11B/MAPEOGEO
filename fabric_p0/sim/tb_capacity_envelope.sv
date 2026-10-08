// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_capacity_envelope
// P0.6C Multi-Dimensional Capacity & Routing Envelope Qualification Testbench
// Measures: Throughput, Latency, Stall Breakdown, Backpressure, Topology Dynamics

`timescale 1ns/1ps

`include "geo_defs.svh"

module tb_capacity_envelope;

    parameter int WORK_CELL_COUNT   = 16;
    parameter int OPERATOR_LANES    = 1;
    parameter int MEMORY_BANKS      = 1;
    parameter int AUTHORITY_ENGINES = 1;
    parameter int INGRESS_LANES     = 1;
    parameter int EGRESS_LANES      = 1;
    parameter int DATA_WIDTH        = 32;
    parameter int FRAC_BITS         = 16;
    parameter int STATE_WORDS       = 256;
    parameter int TOTAL_UOWS        = 16;
    parameter int TEST_TOPO         = 0; // 0=INDEP, 1=CHAIN, 2=FANOUT, 3=FANIN, 4=DIAMOND, 5=CONTENTION, 6=MIXED
    parameter int INJECT_INTERVAL   = 0; // 0=backpressure/saturated, >0=paced
    parameter int CONTENTION_PCT    = 0; // 0 to 100 (% sharing authority domain)
    parameter int WORKLOAD_MIX      = 0; // 0=LIGHT (ADD/CMP), 1=GEO (CL20), 2=MIXED

    localparam logic signed [DATA_WIDTH-1:0] ONE   = (1 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] TWO   = (2 << FRAC_BITS);
    localparam logic signed [DATA_WIDTH-1:0] THREE = (3 << FRAC_BITS);

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

    geo_telemetry_t    telemetry;
    logic [63:0]       evidence_root;
    logic [WORK_CELL_COUNT-1:0] active_cells;

    // Graph boot programming ports
    logic              graph_node_wr_en;
    logic [15:0]       graph_node_wr_addr;
    graph_node_t       graph_node_wr_data;
    logic              graph_edge_wr_en;
    logic [15:0]       graph_edge_wr_addr;
    graph_edge_t       graph_edge_wr_data;

    always #5 clk = ~clk;

    mapeogeo_p0_fabric #(
        .WORK_CELL_COUNT(WORK_CELL_COUNT),
        .OPERATOR_LANES(OPERATOR_LANES),
        .MEMORY_BANKS(MEMORY_BANKS),
        .AUTHORITY_ENGINES(AUTHORITY_ENGINES),
        .INGRESS_LANES(INGRESS_LANES),
        .EGRESS_LANES(EGRESS_LANES),
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

    // Watchdog
    initial begin
        #500000;
        $display("[CAPACITY WATCHDOG TIMEOUT] Simulation exceeded 500,000 ns!");
        $fatal(1, "Watchdog timeout in capacity benchmark");
    end

    // Timestamp & Latency Tracking
    integer issue_cycle    [0:4095];
    integer complete_cycle [0:4095];
    integer latency        [0:4095];
    integer egress_per_cyc [0:4095];
    integer completed_count;
    integer first_egress_cycle;
    integer last_egress_cycle;
    integer start_benchmark_cycle;
    integer end_benchmark_cycle;

    // Build UoW Descriptors according to selected topology
    function automatic uow_desc_t build_uow(input integer idx, input integer total);
        uow_desc_t d;
        integer k;
        integer is_contended;
        d = '0;
        d.uow_id           = idx + 1;
        d.auth_token       = 32'hA000_0000 | (idx + 1);
        d.dep_cond         = DEP_COND_BITMASK;
        d.dep_mask         = '0;
        
        is_contended = (CONTENTION_PCT > 0) && (((idx * 100) / total) < CONTENTION_PCT);
        if (is_contended) begin
            d.dest_addr  = 8'd50; // Fixed domain contention
            d.src_a_addr = 8'd50;
            d.src_b_addr = 8'd51;
        end else begin
            d.dest_addr  = 8'd10 + (idx % 120); // Disjoint distributed domains
            d.src_a_addr = 8'd10 + (idx % 120);
            d.src_b_addr = 8'd10 + ((idx + 1) % 120);
        end

        // Base Workload Mix (P0.6F)
        case (WORKLOAD_MIX)
            0: begin // W_light: simple ADD / COMPARE
                d.opcode        = (idx % 2 == 0) ? OP_ADD : OP_COMPARE;
                d.use_immediate = 1'b1;
                d.imm_operand.s = idx * ONE;
            end
            1: begin // W_GEO: Cl(2,0) multivector geometric product
                d.opcode         = OP_CL20_PRODUCT;
                d.use_immediate  = 1'b1;
                d.imm_operand.s  = TWO;
                d.imm_operand.e1 = ONE;
            end
            2: begin // W_mixed: heterogeneous mix
                d.use_immediate = 1'b1;
                case (idx % 4)
                    0: begin
                        d.opcode         = OP_CL20_PRODUCT;
                        d.imm_operand.s  = TWO;
                        d.imm_operand.e1 = ONE;
                    end
                    1: begin
                        d.opcode        = OP_ADD;
                        d.imm_operand.s = idx * ONE;
                    end
                    2: begin
                        d.opcode        = OP_MUL;
                        d.imm_operand.s = TWO;
                    end
                    3: begin
                        d.opcode         = OP_COMPOSE;
                        d.imm_operand.s  = THREE;
                        d.imm_operand.e2 = TWO;
                    end
                endcase
            end
            default: begin
                d.opcode        = OP_ADD;
                d.use_immediate = 1'b1;
                d.imm_operand.s = idx * ONE;
            end
        endcase

        // If TEST_TOPO specified != 0, allow topology overrides
        if (TEST_TOPO != 0) begin
            case (TEST_TOPO)
                1: begin // TOPO_CHAIN
                    if (idx > 0) begin
                        d.dep_mask = (128'b1 << (idx - 1));
                        d.src_a_addr = 8'd10 + (idx - 1);
                    end
                end
                2: begin // TOPO_FANOUT
                    if (idx > 0) begin
                        d.dep_mask = 128'b1; // depend on root UoW 0
                        d.src_a_addr = 8'd10;
                    end
                end
                3: begin // TOPO_FANIN
                    if (idx == total - 1) begin
                        for (k = 0; k < total - 1; k = k + 1) begin
                            d.dep_mask = d.dep_mask | (128'b1 << k);
                        end
                    end
                end
                4: begin // TOPO_DIAMOND
                    if (idx == 0) begin
                        d.dep_mask = '0;
                    end else if (idx == total - 1) begin
                        for (k = 1; k < total - 1; k = k + 1) begin
                            d.dep_mask = d.dep_mask | (128'b1 << k);
                        end
                    end else begin
                        d.dep_mask = 128'b1; // depend on UoW 0
                    end
                end
                5: begin // TOPO_HIGH_CONTENTION
                    d.dep_mask  = '0;
                    d.dest_addr = 8'd50;
                    d.opcode    = OP_CL20_PRODUCT;
                    d.imm_operand.s  = TWO;
                    d.imm_operand.e1 = ONE;
                end
                6: begin // TOPO_MIXED
                    d.dep_mask = '0;
                    case (idx % 4)
                        0: begin
                            d.opcode = OP_CL20_PRODUCT;
                            d.imm_operand.s = TWO;
                            d.imm_operand.e1 = ONE;
                        end
                        1: begin
                            d.opcode = OP_ADD;
                            d.imm_operand.s = idx * ONE;
                        end
                        2: begin
                            d.opcode = OP_MUL;
                            d.imm_operand.s = TWO;
                        end
                        3: begin
                            d.opcode = OP_COMPOSE;
                            d.imm_operand.s = THREE;
                            d.imm_operand.e2 = TWO;
                        end
                    endcase
                end
                default: d.dep_mask = '0;
            endcase
        end
        return d;
    endfunction

    // Egress Multi-Lane Collector
    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            completed_count    <= 0;
            first_egress_cycle <= 0;
            last_egress_cycle  <= 0;
        end else begin
            int lanes_retired;
            lanes_retired = 0;
            for (int e = 0; e < EGRESS_LANES; e = e + 1) begin
                if (egress_valid[e] && egress_ready[e]) begin
                    logic [31:0] uid;
                    uid = egress_uow_id[e*32 +: 32];
                    if (uid > 0 && uid <= 4096) begin
                        complete_cycle[uid - 1] = $time / 10;
                        latency[uid - 1] = ($time / 10) - issue_cycle[uid - 1];
                    end
                    if (completed_count == 0 && lanes_retired == 0) begin
                        first_egress_cycle <= $time / 10;
                    end
                    last_egress_cycle <= $time / 10;
                    lanes_retired = lanes_retired + 1;
                end
            end
            completed_count <= completed_count + lanes_retired;
            egress_per_cyc[$time / 10] <= lanes_retired;
        end
    end

    // Latency sorting & reporting helper
    task print_benchmark_metrics;
        integer sum_lat, min_lat, max_lat, p95_lat;
        integer lat_arr[0:4095];
        integer i, j, temp;
        integer sort_limit;
        integer drain_cycles;
        real mean_lat, admit_rate, comp_rate, steady_rate;
        integer total_cycles;
    begin
        total_cycles = end_benchmark_cycle - start_benchmark_cycle;
        if (total_cycles == 0) total_cycles = 1;

        sum_lat = 0;
        min_lat = 999999;
        max_lat = 0;

        for (i = 0; i < TOTAL_UOWS; i = i + 1) begin
            lat_arr[i] = latency[i];
            sum_lat = sum_lat + latency[i];
            if (latency[i] < min_lat) min_lat = latency[i];
            if (latency[i] > max_lat) max_lat = latency[i];
        end

        // Bounded sort lat_arr for p95 up to 256 items to prevent simulator slowdown
        sort_limit = (TOTAL_UOWS < 256) ? TOTAL_UOWS : 256;
        for (i = 0; i < sort_limit - 1; i = i + 1) begin
            for (j = i + 1; j < sort_limit; j = j + 1) begin
                if (lat_arr[i] > lat_arr[j]) begin
                    temp = lat_arr[i];
                    lat_arr[i] = lat_arr[j];
                    lat_arr[j] = temp;
                end
            end
        end

        p95_lat = lat_arr[(sort_limit * 95) / 100];
        mean_lat = real'(sum_lat) / real'(TOTAL_UOWS);
        admit_rate = real'(telemetry.uow_admitted) / real'(total_cycles);
        comp_rate  = real'(telemetry.uow_committed) / real'(total_cycles);

        drain_cycles = (last_egress_cycle >= first_egress_cycle) ? (last_egress_cycle - first_egress_cycle + 1) : 1;
        // P0.6F-R1: Post-warmup steady-state window measurement (eliminates fill/drain burst quantization)
        if (drain_cycles >= 12) begin
            int t0, t1, window_uows, window_cycles;
            t0 = first_egress_cycle + (drain_cycles / 4);
            t1 = first_egress_cycle + (3 * drain_cycles / 4);
            window_cycles = t1 - t0 + 1;
            window_uows = 0;
            for (int t = t0; t <= t1; t = t + 1) begin
                window_uows = window_uows + egress_per_cyc[t];
            end
            if (window_cycles > 0 && window_uows > 0) begin
                steady_rate = real'(window_uows) / real'(window_cycles);
            end else begin
                steady_rate = real'(TOTAL_UOWS) / real'(drain_cycles);
            end
        end else begin
            steady_rate  = real'(TOTAL_UOWS) / real'(drain_cycles);
        end

        $display("================================================================================");
        $display("[CAPACITY BENCHMARK RESULT] N_W=%0d N_O=%0d TOPO=%0d TOTAL_UOWS=%0d INTERVAL=%0d",
            WORK_CELL_COUNT, OPERATOR_LANES, TEST_TOPO, TOTAL_UOWS, INJECT_INTERVAL);
        $display("--------------------------------------------------------------------------------");
        $display("Execution Cycles:        %0d cycles", total_cycles);
        $display("UoWs Admitted:           %0d (Rate: %0.4f UoW/cycle)", telemetry.uow_admitted, admit_rate);
        $display("UoWs Committed:          %0d (Rate: %0.4f UoW/cycle)", telemetry.uow_committed, comp_rate);
        $display("Steady-State Drain:      %0d cycles (first: %0d, last: %0d)", drain_cycles, first_egress_cycle, last_egress_cycle);
        $display("Steady-State Rate:       %0.4f UoW/cycle", steady_rate);
        $display("UoWs Rejected:           %0d", telemetry.uow_rejected);
        $display("Operations Executed:     %0d", telemetry.ops_executed);
        $display("Latency (min/mean/p95/max): %0d / %0.2f / %0d / %0d cycles", min_lat, mean_lat, p95_lat, max_lat);
        $display("Peak Queue Occupancy:    %0d / %0d cells (%0.1f%%)",
            telemetry.peak_queue_occupancy, WORK_CELL_COUNT,
            (real'(telemetry.peak_queue_occupancy) / real'(WORK_CELL_COUNT)) * 100.0);
        $display("--------------------------------------------------------------------------------");
        $display("Pipeline Stage Breakdown (Nominal Unloaded):");
        $display("  T_admit:               2 cycles (Ingress alloc + State mem read)");
        $display("  T_dispatch:            2 cycles (Operator arbitrate + handshake)");
        $display("  T_execute:             2 cycles (Geometric product / ALU)");
        $display("  T_certify:             2 cycles (Authority CAS + SHA state update)");
        $display("  T_egress:              1 cycles (Egress FIFO push + commit emit)");
        $display("  T_nominal_pipeline:    9 cycles total");
        $display("--------------------------------------------------------------------------------");
        $display("Bottleneck & Stall Breakdown:");
        $display("  Operator Wait Stalls:  %0d cycles", telemetry.stall_operator_wait);
        $display("  Dependency Stalls:     %0d cycles", telemetry.stall_dep_wait);
        $display("  Authority Wait Stalls: %0d cycles", telemetry.stall_auth_wait);
        $display("  Memory Read Stalls:    %0d cycles", telemetry.stall_mem_wait);
        $display("  Backpressure Cycles:   %0d cycles", telemetry.backpressure_cycles);
        $display("Final Evidence Root:     0x%016x", evidence_root);
        $display("================================================================================");
    end
    endtask

    // Main Benchmark Driver
    integer uow_idx;
    initial begin
        clk = 0;
        reset_n = 0;
        boot_trigger = 0;
        ingress_valid = '0;
        ingress_desc  = '0;
        egress_ready  = '1;
        graph_node_wr_en = 0;
        graph_edge_wr_en = 0;

        #20 reset_n = 1;
        #10;
        @(negedge clk);
        boot_trigger = 1;
        @(negedge clk);
        boot_trigger = 0;

        wait(boot_complete == 1'b1);
        @(negedge clk);

        start_benchmark_cycle = $time / 10;

        // Ingress multi-lane injection loop (P0.6F)
        for (int z = 0; z < 4096; z = z + 1) begin
            issue_cycle[z]    = 0;
            complete_cycle[z] = 0;
            latency[z]        = 0;
        end

        uow_idx = 0;
        while (uow_idx < TOTAL_UOWS) begin
            int lane_k;
            int accepted_lanes;
            if (INJECT_INTERVAL > 0) begin
                repeat(INJECT_INTERVAL) @(negedge clk);
            end

            for (lane_k = 0; lane_k < INGRESS_LANES; lane_k = lane_k + 1) begin
                if (uow_idx + lane_k < TOTAL_UOWS) begin
                    uow_desc_t d_inj;
                    d_inj = build_uow(uow_idx + lane_k, TOTAL_UOWS);
                    ingress_desc[lane_k*471 +: 471] = d_inj;
                    ingress_valid[lane_k]           = 1'b1;
                    if (issue_cycle[uow_idx + lane_k] == 0) begin
                        issue_cycle[uow_idx + lane_k] = $time / 10;
                    end
                end else begin
                    ingress_valid[lane_k]           = 1'b0;
                end
            end

            #1; // Allow combinational ingress_ready to settle
            accepted_lanes = 0;
            for (lane_k = 0; lane_k < INGRESS_LANES; lane_k = lane_k + 1) begin
                if (ingress_valid[lane_k] && ingress_ready[lane_k]) begin
                    accepted_lanes = accepted_lanes + 1;
                end
            end

            // Advance through posedge where fabric allocates accepted lanes into cells
            @(posedge clk);
            uow_idx = uow_idx + accepted_lanes;

            // Wait for negedge before next injection step
            @(negedge clk);
        end
        ingress_valid = '0;

        // Wait until all UoWs have completed egress
        wait(completed_count == TOTAL_UOWS);
        #20;
        end_benchmark_cycle = $time / 10;

        print_benchmark_metrics();

        // Sanity assertions
        if (telemetry.uow_committed != TOTAL_UOWS) begin
            $fatal(1, "ERROR: Expected %0d committed UoWs, got %0d", TOTAL_UOWS, telemetry.uow_committed);
        end
        if (telemetry.fault_events != 0) begin
            $fatal(1, "ERROR: Unexpected fault events: %0d", telemetry.fault_events);
        end

        $display("PASS CAPACITY ENVELOPE BENCHMARK");
        $finish;
    end

endmodule
