// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Testbench: tb_synth_memory (Gate RTL-9 Post-Synthesis Equivalence)

`timescale 1ns/1ps
`include "geo_defs.svh"

module tb_synth_memory;

    localparam int ADDR_WIDTH = 8;
    localparam int WORDS = 256;
    localparam int MEMORY_BANKS = 4;
    localparam int AUTHORITY_ENGINES = 4;

    logic clk;
    logic reset_n;

    logic [MEMORY_BANKS*8-1:0]   rd_a_addr;
    logic [MEMORY_BANKS*128-1:0] rd_a_data;
    logic [MEMORY_BANKS*16-1:0]  rd_a_version;

    logic [MEMORY_BANKS*8-1:0]   rd_b_addr;
    logic [MEMORY_BANKS*128-1:0] rd_b_data;
    logic [MEMORY_BANKS*16-1:0]  rd_b_version;

    logic [AUTHORITY_ENGINES*8-1:0]  auth_check_addr;
    logic [AUTHORITY_ENGINES*16-1:0] auth_current_version;

    logic [MEMORY_BANKS-1:0]     commit_en;
    logic [MEMORY_BANKS*8-1:0]   commit_addr;
    logic [MEMORY_BANKS*128-1:0] commit_data;
    logic [MEMORY_BANKS*16-1:0]  post_commit_version;

    always #5 clk = ~clk;

    geo_state_memory dut (
        .clk(clk),
        .reset_n(reset_n),
        .rd_a_addr(rd_a_addr),
        .rd_a_data(rd_a_data),
        .rd_a_version(rd_a_version),
        .rd_b_addr(rd_b_addr),
        .rd_b_data(rd_b_data),
        .rd_b_version(rd_b_version),
        .auth_check_addr(auth_check_addr),
        .auth_current_version(auth_current_version),
        .commit_en(commit_en),
        .commit_addr(commit_addr),
        .commit_data(commit_data),
        .post_commit_version(post_commit_version),
        .boot_wr_en(1'b0),
        .boot_wr_addr(8'd0),
        .boot_wr_data(128'd0),
        .diag_addr(8'd0),
        .diag_data(),
        .mem_reads(),
        .mem_writes()
    );

    initial begin
        clk = 0;
        reset_n = 0;
        rd_a_addr = 0;
        rd_b_addr = 0;
        auth_check_addr = 0;
        commit_en = 0;
        commit_addr = 0;
        commit_data = 0;

        #20 reset_n = 1;
        #10;

        // Verify initial state version = 0 for address 10 (Bank 2)
        @(posedge clk);
        auth_check_addr[0*8 +: 8] <= 8'd10;
        #1;
        assert(auth_current_version[0*16 +: 16] == 16'd0) else $fatal(1, "Initial version not 0");

        // Commit new data to address 10 (Bank 2)
        @(posedge clk);
        commit_en[2] <= 1'b1;
        commit_addr[2*8 +: 8] <= 8'd10;
        commit_data[2*128 +: 128] <= {32'h1111, 32'h2222, 32'h3333, 32'h4444};
        @(posedge clk);
        commit_en[2] <= 1'b0;

        // Inspect version increment to 1
        @(posedge clk);
        auth_check_addr[0*8 +: 8] <= 8'd10;
        #1;
        $display("[DEBUG MEM] auth_current_version=%0d", auth_current_version[0*16 +: 16]);
        assert(auth_current_version[0*16 +: 16] == 16'd1) else $fatal(1, "Post commit version not 1");

        // Read through port A
        @(posedge clk);
        rd_a_addr[2*8 +: 8] <= 8'd10;
        #1;
        $display("[DEBUG MEM] got data = %h (expected %h)", rd_a_data[2*128 +: 128], {32'h1111, 32'h2222, 32'h3333, 32'h4444});
        assert(rd_a_data[2*128 +: 128] == {32'h1111, 32'h2222, 32'h3333, 32'h4444}) else $fatal(1, "Read data mismatch");
        assert(rd_a_version[2*16 +: 16] == 16'd1) else $fatal(1, "Read version mismatch");

        $display("PASS POST_SYNTHESIS_MEMORY_EQUIVALENCE");
        $finish;
    end

endmodule
