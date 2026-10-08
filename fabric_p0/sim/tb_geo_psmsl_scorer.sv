// SPDX-License-Identifier: MIT
// =============================================================================
// Testbench: tb_geo_psmsl_scorer
// Project: MAPEOGEO fabric_p0 / Track PDI-v0.8
// Description:
//   Exhaustive differential testbench verifying bit-exact agreement between
//   the synthesizable geo_psmsl_scorer RTL module and the Python integer reference.
// =============================================================================

`timescale 1ns / 1ps

module tb_geo_psmsl_scorer;

    reg clk;
    reg rst_n;

    reg        start;
    reg  [3:0] cand_id_in;
    reg  [7:0] features_in [0:31];

    wire        busy;
    wire        done;
    wire [3:0]  cand_id_out;
    wire signed [31:0] score_out;

    wire [255:0] features_in_bus;
    genvar g;
    generate
        for (g = 0; g < 32; g = g + 1) begin : gen_feat_pack
            assign features_in_bus[g*8 +: 8] = features_in[g];
        end
    endgenerate

    // Instantiate DUT with explicit path to .mem files
    geo_psmsl_scorer #(
        .MEM_DIR("fabric_p0/rtl/scorer/")
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .cand_id_in(cand_id_in),
        .features_in_bus(features_in_bus),
        .busy(busy),
        .done(done),
        .cand_id_out(cand_id_out),
        .score_out(score_out)
    );

    // 100 MHz Clock Generator (10 ns period)
    always #5 clk = ~clk;

    integer file_fd, scan_ret, i, vec_idx, wait_cycles;
    integer pass_count, fail_count;
    reg [3:0] exp_cid;
    reg [7:0] in_val;
    reg [31:0] exp_score_raw;
    reg signed [31:0] exp_score;

    initial begin
        clk   = 0;
        rst_n = 0;
        start = 0;
        cand_id_in = 0;
        pass_count = 0;
        fail_count = 0;
        for (i = 0; i < 32; i = i + 1) features_in[i] = 8'd0;

        #20;
        rst_n = 1;
        #20;

        file_fd = $fopen("fabric_p0/sim/psmsl_test_vectors.txt", "r");
        if (file_fd == 0) begin
            $display("[FAIL] Could not open fabric_p0/sim/psmsl_test_vectors.txt");
            $finish;
        end

        $display("==================================================================");
        $display("Starting PDI-v0.8 Bit-Exact RTL Differential Simulation");
        $display("==================================================================");

        for (vec_idx = 0; vec_idx < 80; vec_idx = vec_idx + 1) begin
            scan_ret = $fscanf(file_fd, "%d", exp_cid);

            for (i = 0; i < 32; i = i + 1) begin
                scan_ret = $fscanf(file_fd, "%h", in_val);
                features_in[i] = in_val;
            end

            scan_ret = $fscanf(file_fd, "%h", exp_score_raw);
            exp_score = $signed(exp_score_raw);

            // Apply Start Pulse cleanly aligned to clock
            @(negedge clk);
            cand_id_in = exp_cid;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;

            // Wait for Done with watchdog
            wait_cycles = 0;
            while (!done && wait_cycles < 3000) begin
                @(posedge clk);
                wait_cycles = wait_cycles + 1;
            end

            if (wait_cycles >= 3000) begin
                $display("[TIMEOUT] Vector %0d: DUT hung in state=%0d, neuron=%0d, step=%0d, done=%b",
                         vec_idx, dut.state, dut.neuron_idx, dut.input_step, done);
                $finish;
            end

            // Verify Result
            if (score_out === exp_score && cand_id_out === exp_cid) begin
                pass_count = pass_count + 1;
            end else begin
                fail_count = fail_count + 1;
                $display("[MISMATCH] Vector %0d: Expected score=%0d (hex %08h), got score=%0d (hex %08h)",
                         vec_idx, exp_score, exp_score, score_out, score_out);
            end

            @(posedge clk);
        end

        $fclose(file_fd);

        $display("------------------------------------------------------------------");
        $display("PDI-v0.8 Differential Verification Results:");
        $display("  Total Vectors Tested: %0d", vec_idx);
        $display("  Bit-Exact Matches:   %0d", pass_count);
        $display("  Mismatches:          %0d", fail_count);
        $display("==================================================================");

        if (fail_count == 0 && pass_count > 0) begin
            $display("[SUCCESS] All %0d vectors matched bit-exact down to LSB!", pass_count);
        end else begin
            $display("[FAILURE] Verification failed with %0d mismatches!", fail_count);
        end

        $finish;
    end

endmodule
