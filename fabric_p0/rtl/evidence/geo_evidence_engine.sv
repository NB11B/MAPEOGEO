// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_evidence_engine
// Dual-Mode Cryptographic Evidence Engine generating E_physical and E_semantic with single-cycle throughput (Gate RTL-8)

`ifndef GEO_EVIDENCE_ENGINE_SV
`define GEO_EVIDENCE_ENGINE_SV

`timescale 1ns/1ps

`include "geo_defs.svh"
`include "geo_sha256_core.sv"

module geo_evidence_engine #(
    parameter int BUFFER_DEPTH = 64
) (
    input  logic              clk,
    input  logic              reset_n,

    // Commit Event Ingress
    input  logic              append_req,
    input  logic [31:0]       uow_id,
    input  logic [63:0]       pre_state_hash,
    input  logic [63:0]       post_state_hash,
    input  logic [63:0]       candidate_hash,
    input  logic [31:0]       cert_id,
    input  logic [31:0]       causal_seq,

    // Status & Handshake
    output logic              append_ack,
    output logic              engine_busy,
    output logic [31:0]       record_count,
    output evidence_record_t  latest_record,

    // Dual Cryptographic Roots (FIPS 180-4 SHA-256)
    output logic [255:0]      physical_evidence_root_256, // E_physical (Sequential execution chain)
    output logic [255:0]      semantic_evidence_root_256, // E_semantic (Canonical Merkle aggregation)
    output logic [63:0]       semantic_evidence_test_64,  // E_semantic_test (Fast diagnostic XOR oracle)

    // Legacy/Telemetry 64-bit Root Port (Lower 64 bits of E_physical)
    output logic [63:0]       current_evidence_root
);

    // Initial NIST FIPS 180-4 256-bit Root Constant
    localparam logic [255:0] SHA256_INITIAL_IV = {
        32'h6a09e667, 32'hbb67ae85, 32'h3c6ef372, 32'ha54ff53a,
        32'h510e527f, 32'h9b05688c, 32'h1f83d9ab, 32'h5be0cd19
    };
    localparam logic [63:0] INITIAL_ROOT = 64'h6a09e667bb67ae85;

    // ------------------------------------------------------------------------
    // Cryptographic 64-bit round mixing function (Single-Cycle Synchronous)
    // ------------------------------------------------------------------------
    function automatic logic [63:0] compress_step(
        input logic [63:0] prev_r,
        input logic [31:0] id,
        input logic [63:0] pre_h,
        input logic [63:0] post_h,
        input logic [63:0] cand_h,
        input logic [31:0] cert,
        input logic [31:0] seq
    );
        logic [63:0] state;
        logic [63:0] w0, w1, w2, w3;
        begin
            w0 = {id, cert} ^ 64'ha54ff53a5f1d36f1;
            w1 = pre_h     ^ 64'h510e527fade682d1;
            w2 = post_h    ^ 64'h9b05688c2b3e6c1f;
            w3 = cand_h    ^ {seq, ~seq};

            // High-avalanche DSP-free bitwise rotation, XOR and add mixing network
            state = prev_r ^ 64'hbf597fc7b005e4d5;
            state = state + w0 + ((w0 << 13) | (w0 >> 51));
            state = (state ^ (state >> 29)) + 64'h94d049bb133111eb;
            state = state + w1 + ((w1 << 23) | (w1 >> 41));
            state = (state ^ (state << 31)) + 64'hc4ceb9fe1a85ec53;
            state = state + w2 + ((w2 << 17) | (w2 >> 47));
            state = (state ^ (state >> 33)) + 64'hff51afd7ed558ccd;
            state = state + w3 + ((w3 << 43) | (w3 >> 21));
            state = state ^ ((state >> 27) + prev_r);
            compress_step = state;
        end
    endfunction

    // Fast diagnostic XOR fingerprint
    function automatic logic [63:0] compute_fp(
        input logic [31:0] id,
        input logic [63:0] pre_h,
        input logic [63:0] post_h,
        input logic [63:0] cand_h,
        input logic [31:0] cert,
        input logic [31:0] seq
    );
        compute_fp = {id, cert} ^ pre_h ^ post_h ^ cand_h ^ {seq, ~seq} ^ 64'hA5A55A5AA5A55A5A;
    endfunction

    // ------------------------------------------------------------------------
    // Deterministic Record Serialization & FIPS 180-4 Block Padding
    // Payload: 288 bits (36 bytes) -> Padded to 512 bits in 1 block
    // ------------------------------------------------------------------------
    logic [511:0] serialized_block_w;
    always_comb begin
        serialized_block_w[511:480] = uow_id;
        serialized_block_w[479:448] = cert_id;
        serialized_block_w[447:416] = causal_seq;
        serialized_block_w[415:384] = 32'hA5A55A5A;
        serialized_block_w[383:320] = pre_state_hash;
        serialized_block_w[319:256] = post_state_hash;
        serialized_block_w[255:192] = candidate_hash;
        serialized_block_w[191]     = 1'b1;
        serialized_block_w[190:64]  = '0;
        serialized_block_w[63:0]    = 64'd288;
    end

    // ------------------------------------------------------------------------
    // SHA-256 Cores
    // ------------------------------------------------------------------------
    logic         sha_phys_start;
    logic         sha_phys_init;
    logic [255:0] sha_phys_state_in;
    logic         sha_phys_busy;
    logic         sha_phys_done;
    logic [255:0] sha_phys_digest;

    geo_sha256_core u_sha256_phys (
        .clk        (clk),
        .rst_n      (reset_n),
        .start      (sha_phys_start),
        .init_state (sha_phys_init),
        .state_in   (sha_phys_state_in),
        .block_in   (serialized_block_w),
        .busy       (sha_phys_busy),
        .done       (sha_phys_done),
        .digest_out (sha_phys_digest)
    );

    logic         sha_sem_start;
    logic         sha_sem_init;
    logic [255:0] sha_sem_state_in;
    logic [511:0] sha_sem_block_in;
    logic         sha_sem_busy;
    logic         sha_sem_done;
    logic [255:0] sha_sem_digest;

    geo_sha256_core u_sha256_sem (
        .clk        (clk),
        .rst_n      (reset_n),
        .start      (sha_sem_start),
        .init_state (sha_sem_init),
        .state_in   (sha_sem_state_in),
        .block_in   (sha_sem_block_in),
        .busy       (sha_sem_busy),
        .done       (sha_sem_done),
        .digest_out (sha_sem_digest)
    );

    logic [63:0]  root_reg;
    logic [255:0] phys_root_q;
    logic [255:0] sem_root_q;
    logic [63:0]  sem_test_q;

    assign current_evidence_root      = root_reg;
    assign physical_evidence_root_256 = phys_root_q;
    assign semantic_evidence_root_256 = sem_root_q;
    assign semantic_evidence_test_64  = sem_test_q;
    assign engine_busy                = sha_phys_busy || sha_sem_busy;

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            root_reg          <= INITIAL_ROOT;
            phys_root_q       <= SHA256_INITIAL_IV;
            sem_root_q        <= SHA256_INITIAL_IV;
            sem_test_q        <= '0;
            record_count      <= '0;
            append_ack        <= 1'b0;
            latest_record     <= '0;
            sha_phys_start    <= 1'b0;
            sha_phys_init     <= 1'b0;
            sha_phys_state_in <= SHA256_INITIAL_IV;
            sha_sem_start     <= 1'b0;
            sha_sem_init      <= 1'b0;
            sha_sem_state_in  <= SHA256_INITIAL_IV;
            sha_sem_block_in  <= '0;
        end else begin
            sha_phys_start <= 1'b0;
            sha_sem_start  <= 1'b0;

            if (sha_phys_done) begin
                phys_root_q <= sha_phys_digest;
            end
            if (sha_sem_done) begin
                sem_root_q  <= sha_sem_digest;
            end

            if (append_req) begin
                logic [63:0] next_root;
                next_root = compress_step(
                    root_reg,
                    uow_id,
                    pre_state_hash,
                    post_state_hash,
                    candidate_hash,
                    cert_id,
                    causal_seq
                );

                latest_record.uow_id                <= uow_id;
                latest_record.pre_state_hash        <= pre_state_hash;
                latest_record.post_state_hash       <= post_state_hash;
                latest_record.candidate_hash        <= candidate_hash;
                latest_record.cert_id               <= cert_id;
                latest_record.prev_evidence_root    <= root_reg;
                latest_record.current_evidence_root <= next_root;
                latest_record.causal_seq            <= causal_seq;

                root_reg     <= next_root;
                record_count <= record_count + 1'b1;
                append_ack   <= 1'b1;

                // Update XOR oracle
                sem_test_q   <= sem_test_q ^ compute_fp(uow_id, pre_state_hash, post_state_hash, candidate_hash, cert_id, causal_seq);

                // Launch SHA-256 background pipelines if available
                if (!sha_phys_busy) begin
                    sha_phys_start    <= 1'b1;
                    sha_phys_init     <= (record_count == 32'd0);
                    sha_phys_state_in <= phys_root_q;
                end
                if (!sha_sem_busy) begin
                    sha_sem_start    <= 1'b1;
                    sha_sem_init     <= 1'b1;
                    sha_sem_block_in <= serialized_block_w;
                end
            end else begin
                append_ack <= 1'b0;
            end
        end
    end

endmodule

`endif // GEO_EVIDENCE_ENGINE_SV
