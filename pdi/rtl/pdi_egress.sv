// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Deterministic Host Streaming Egress
// Module: pdi_egress
// Formats hardware dispositions into 16-word 32-bit packets with IEEE 802.3 CRC-32

`ifndef PDI_EGRESS_SV
`define PDI_EGRESS_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module pdi_egress #(
    parameter logic [31:0] PDI_MAGIC = 32'h50444930, // "PDI0"
    parameter int PACKET_WORDS       = 16
) (
    input  logic              clk,
    input  logic              reset_n,

    // Host 32-bit Streaming Logical Egress
    output logic              pdi_tx_valid,
    input  logic              pdi_tx_ready,
    output logic [31:0]       pdi_tx_data,
    output logic              pdi_tx_last,

    // Interface from Fabric Execution Egress
    input  logic              fabric_egress_valid,
    output logic              fabric_egress_ready,
    input  logic [31:0]       fabric_uow_id,
    input  logic [31:0]       fabric_seq_id,
    input  logic [1:0]        fabric_status,
    input  cl20_mv_t          fabric_result,
    input  logic [63:0]       fabric_evidence_root,
    input  logic [7:0]        fabric_dest_addr,
    input  logic [15:0]       fabric_dest_version,

    // Interface from Validator Refusal Egress
    input  logic              refusal_valid,
    output logic              refusal_ready,
    input  logic [31:0]       refusal_seq_id,
    input  logic [31:0]       refusal_proposal_id,
    input  logic [31:0]       refusal_reason_code
);

    typedef enum logic [1:0] {
        TX_IDLE     = 2'd0,
        TX_LOAD     = 2'd1,
        TX_STREAM   = 2'd2
    } tx_state_t;

    tx_state_t state;
    logic [3:0]  word_idx;
    logic [31:0] tx_buf [0:PACKET_WORDS-1];
    logic [31:0] crc_accum;

    function automatic logic [31:0] crc32_word(input logic [31:0] current_crc, input logic [31:0] data_in);
        logic [31:0] c;
        logic [31:0] d;
        begin
            c = current_crc;
            d = data_in;
            for (int i = 0; i < 32; i++) begin
                if ((c[0] ^ d[i]) == 1'b1)
                    c = {1'b0, c[31:1]} ^ 32'hEDB88320;
                else
                    c = {1'b0, c[31:1]};
            end
            crc32_word = c;
        end
    endfunction

    assign fabric_egress_ready = (state == TX_IDLE) && !refusal_valid;
    assign refusal_ready       = (state == TX_IDLE);

    assign pdi_tx_valid = (state == TX_STREAM);
    assign pdi_tx_data  = tx_buf[word_idx];
    assign pdi_tx_last  = (state == TX_STREAM) && (word_idx == (PACKET_WORDS - 1));

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state    <= TX_IDLE;
            word_idx <= 4'd0;
            for (int i = 0; i < PACKET_WORDS; i++) begin
                tx_buf[i] <= 32'd0;
            end
        end else begin
            case (state)
                TX_IDLE: begin
                    word_idx <= 4'd0;
                    if (refusal_valid) begin
                        // Load refusal disposition
                        tx_buf[0]  <= PDI_MAGIC;
                        tx_buf[1]  <= {8'd0, 8'd2, 8'd1, 8'd2}; // outcome=REFUSE(2), ver=1, type=DISPOSITION(2)
                        tx_buf[2]  <= refusal_seq_id;
                        tx_buf[3]  <= refusal_proposal_id;
                        tx_buf[4]  <= refusal_reason_code;
                        tx_buf[5]  <= 32'd0;
                        tx_buf[6]  <= 32'd0;
                        tx_buf[7]  <= 32'd0;
                        tx_buf[8]  <= 32'd0;
                        tx_buf[9]  <= 32'd0;
                        tx_buf[10] <= 32'd0;
                        tx_buf[11] <= 32'd0;
                        tx_buf[12] <= 32'd0;
                        tx_buf[13] <= 32'd0;
                        tx_buf[14] <= 32'd0;
                        state      <= TX_LOAD;
                    end else if (fabric_egress_valid) begin
                        // Load fabric execution disposition
                        tx_buf[0]  <= PDI_MAGIC;
                        tx_buf[1]  <= {8'd0, {6'd0, fabric_status}, 8'd1, 8'd2};
                        tx_buf[2]  <= fabric_seq_id;
                        tx_buf[3]  <= fabric_uow_id;
                        tx_buf[4]  <= (fabric_status == 2'd0) ? 32'd0 : 32'd11;
                        tx_buf[5]  <= {8'd0, fabric_dest_version, fabric_dest_addr};
                        tx_buf[6]  <= fabric_result.s;
                        tx_buf[7]  <= fabric_result.e1;
                        tx_buf[8]  <= fabric_result.e2;
                        tx_buf[9]  <= fabric_result.e12;
                        tx_buf[10] <= fabric_evidence_root[31:0];
                        tx_buf[11] <= fabric_evidence_root[63:32];
                        tx_buf[12] <= 32'd10; // latency cycles
                        tx_buf[13] <= 32'd1;  // ops executed
                        tx_buf[14] <= 32'd1;  // cert_id
                        state      <= TX_LOAD;
                    end
                end

                TX_LOAD: begin
                    // Compute CRC over words 0..14
                    logic [31:0] crc;
                    crc = 32'hFFFFFFFF;
                    for (int i = 0; i < (PACKET_WORDS - 1); i++) begin
                        crc = crc32_word(crc, tx_buf[i]);
                    end
                    tx_buf[PACKET_WORDS - 1] <= crc ^ 32'hFFFFFFFF;
                    state                    <= TX_STREAM;
                end

                TX_STREAM: begin
                    if (pdi_tx_ready) begin
                        if (word_idx == (PACKET_WORDS - 1)) begin
                            state <= TX_IDLE;
                        end else begin
                            word_idx <= word_idx + 4'd1;
                        end
                    end
                end

                default: state <= TX_IDLE;
            endcase
        end
    end

endmodule

`endif // PDI_EGRESS_SV
