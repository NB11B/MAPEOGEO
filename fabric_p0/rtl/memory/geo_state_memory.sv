// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_state_memory
// Parameterized Multi-Bank Authoritative State Memory with Hardware Commit Gating and Version Tracking (P0.6D)

`ifndef GEO_STATE_MEMORY_SV
`define GEO_STATE_MEMORY_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_state_memory #(
    parameter int ADDR_WIDTH        = 8,
    parameter int WORDS             = 256,
    parameter int MEMORY_BANKS      = 1,
    parameter int AUTHORITY_ENGINES = 1
) (
    input  logic                                clk,
    input  logic                                reset_n,

    // Read Port A (Work Cell Operand A per bank)
    input  logic [MEMORY_BANKS*ADDR_WIDTH-1:0]  rd_a_addr,
    output logic [MEMORY_BANKS*128-1:0]         rd_a_data,
    output logic [MEMORY_BANKS*16-1:0]          rd_a_version,

    // Read Port B (Work Cell Operand B per bank)
    input  logic [MEMORY_BANKS*ADDR_WIDTH-1:0]  rd_b_addr,
    output logic [MEMORY_BANKS*128-1:0]         rd_b_data,
    output logic [MEMORY_BANKS*16-1:0]          rd_b_version,

    // Authority Version Inspection Port (Atomic CAS verification)
    input  logic [AUTHORITY_ENGINES*ADDR_WIDTH-1:0] auth_check_addr = '0,
    output logic [AUTHORITY_ENGINES*16-1:0]         auth_current_version,

    // Authority Commit Port (STRICTLY GATED by commit_en per bank)
    input  logic [MEMORY_BANKS-1:0]             commit_en,
    input  logic [MEMORY_BANKS*ADDR_WIDTH-1:0]  commit_addr,
    input  logic [MEMORY_BANKS*128-1:0]         commit_data,
    output logic [MEMORY_BANKS*16-1:0]          post_commit_version,

    // Diagnostic/Hash Port
    input  logic [ADDR_WIDTH-1:0]               diag_addr,
    output cl20_mv_t                            diag_data,

    // Telemetry
    output logic [31:0]                         mem_reads,
    output logic [31:0]                         mem_writes
);

    // Authoritative State Memory Array
    // Exposed as mem_s, mem_e1, mem_e2, mem_e12 for simulation peek/poke parity across all testbenches
    logic signed [31:0] mem_s   [0:WORDS-1];
    logic signed [31:0] mem_e1  [0:WORDS-1];
    logic signed [31:0] mem_e2  [0:WORDS-1];
    logic signed [31:0] mem_e12 [0:WORDS-1];
    logic [15:0]        versions[0:WORDS-1];

    genvar b;
    generate
        for (b = 0; b < MEMORY_BANKS; b = b + 1) begin : gen_bank_rd
            wire [ADDR_WIDTH-1:0] b_rd_a_addr = rd_a_addr[b*ADDR_WIDTH +: ADDR_WIDTH];
            wire [ADDR_WIDTH-1:0] b_rd_b_addr = rd_b_addr[b*ADDR_WIDTH +: ADDR_WIDTH];

            assign rd_a_data[b*128 +: 128]    = {mem_s[b_rd_a_addr], mem_e1[b_rd_a_addr], mem_e2[b_rd_a_addr], mem_e12[b_rd_a_addr]};
            assign rd_a_version[b*16 +: 16]   = versions[b_rd_a_addr];

            assign rd_b_data[b*128 +: 128]    = {mem_s[b_rd_b_addr], mem_e1[b_rd_b_addr], mem_e2[b_rd_b_addr], mem_e12[b_rd_b_addr]};
            assign rd_b_version[b*16 +: 16]   = versions[b_rd_b_addr];
        end
    endgenerate

    // Authority version lookup with Write-Bypass Forwarding
    genvar a_ver;
    generate
        for (a_ver = 0; a_ver < AUTHORITY_ENGINES; a_ver = a_ver + 1) begin : gen_auth_ver
            wire [ADDR_WIDTH-1:0] a_addr = auth_check_addr[a_ver*ADDR_WIDTH +: ADDR_WIDTH];
            logic pending_commit_match;
            always_comb begin
                int b;
                pending_commit_match = 1'b0;
                for (b = 0; b < MEMORY_BANKS; b = b + 1) begin
                    if (commit_en[b] && (commit_addr[b*ADDR_WIDTH +: ADDR_WIDTH] == a_addr)) begin
                        pending_commit_match = 1'b1;
                    end
                end
            end
            assign auth_current_version[a_ver*16 +: 16] = pending_commit_match ?
                                                          (versions[a_addr] + 16'd1) : versions[a_addr];
        end
    endgenerate

    // Diagnostic read
    assign diag_data = {mem_s[diag_addr], mem_e1[diag_addr], mem_e2[diag_addr], mem_e12[diag_addr]};

    // Synchronous Commit Write and Version Tracking
    integer w_init;
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            post_commit_version <= '0;
            mem_reads           <= '0;
            mem_writes          <= '0;
            for (w_init = 0; w_init < WORDS; w_init = w_init + 1) begin
                mem_s[w_init]    <= 32'sd0;
                mem_e1[w_init]   <= 32'sd0;
                mem_e2[w_init]   <= 32'sd0;
                mem_e12[w_init]  <= 32'sd0;
                versions[w_init] <= 16'd0;
            end
        end else begin
            int b_wr;
            if (|commit_en) begin
                mem_writes <= mem_writes + 1'b1;
            end
            for (b_wr = 0; b_wr < MEMORY_BANKS; b_wr = b_wr + 1) begin
                if (commit_en[b_wr]) begin
                    logic [ADDR_WIDTH-1:0] b_addr;
                    cl20_mv_t              b_data;
                    b_addr = commit_addr[b_wr*ADDR_WIDTH +: ADDR_WIDTH];
                    b_data = commit_data[b_wr*128 +: 128];
                    mem_s[b_addr]                      <= b_data.s;
                    mem_e1[b_addr]                     <= b_data.e1;
                    mem_e2[b_addr]                     <= b_data.e2;
                    mem_e12[b_addr]                    <= b_data.e12;
                    versions[b_addr]                   <= versions[b_addr] + 1'b1;
                    post_commit_version[b_wr*16 +: 16] <= versions[b_addr] + 1'b1;
                end
            end
        end
    end

endmodule

`endif // GEO_STATE_MEMORY_SV
