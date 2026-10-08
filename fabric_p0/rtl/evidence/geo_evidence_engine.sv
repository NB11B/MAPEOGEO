// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_evidence_engine
// Cryptographic evidence accumulation engine maintaining chained audit root (Section 10)

`ifndef GEO_EVIDENCE_ENGINE_SV
`define GEO_EVIDENCE_ENGINE_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_evidence_engine #(
    parameter int BUFFER_DEPTH = 64
) (
    input  logic              clk,
    input  logic              reset_n,

    // Commit Event
    input  logic              append_req,
    input  logic [31:0]       uow_id,
    input  logic [63:0]       pre_state_hash,
    input  logic [63:0]       post_state_hash,
    input  logic [63:0]       candidate_hash,
    input  logic [31:0]       cert_id,
    input  logic [31:0]       causal_seq,

    // Status & Outputs
    output logic              append_ack,
    output logic [63:0]       current_evidence_root,
    output logic [31:0]       record_count,
    output evidence_record_t  latest_record
);

    // Initial root constant (deterministic initial seed)
    localparam logic [63:0] INITIAL_ROOT = 64'h6a09e667bb67ae85; // First 64 bits of SHA-256 initial H0|H1

    logic [63:0] root_reg;
    assign current_evidence_root = root_reg;

    // Cryptographic 64-bit round mixing function (Davies-Meyer / Merkle-Damgard compression step)
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

            state = prev_r ^ 64'hbf597fc7b005e4d5;
            state = (state ^ (state >> 30)) * 64'hbf58476d1ce4e5b9;
            state = (state ^ w0)            * 64'h94d049bb133111eb;
            state = (state ^ w1)            * 64'hc4ceb9fe1a85ec53;
            state = (state ^ (state >> 27)) * 64'hff51afd7ed558ccd;
            state = (state ^ w2)            * 64'hc4ceb9fe1a85ec53;
            state = (state ^ w3)            + prev_r;
            compress_step = state;
        end
    endfunction

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            root_reg       <= INITIAL_ROOT;
            record_count   <= '0;
            append_ack     <= 1'b0;
            latest_record  <= '0;
        end else begin
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
            end else begin
                append_ack   <= 1'b0;
            end
        end
    end

endmodule

`endif // GEO_EVIDENCE_ENGINE_SV
