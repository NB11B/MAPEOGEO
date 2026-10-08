// SPDX-License-Identifier: MIT
// PDI-135M-v0.1: Deterministic Host Streaming Ingress
// Module: pdi_ingress
// Reassembles 16-word 32-bit streaming frames, validates framing & CRC-32

`ifndef PDI_INGRESS_SV
`define PDI_INGRESS_SV

`timescale 1ns/1ps

module pdi_ingress #(
    parameter logic [31:0] PDI_MAGIC = 32'h50444930, // "PDI0"
    parameter int PACKET_WORDS       = 16
) (
    input  logic              clk,
    input  logic              reset_n,

    // Host 32-bit Streaming Logical Interface
    input  logic              pdi_rx_valid,
    output logic              pdi_rx_ready,
    input  logic [31:0]       pdi_rx_data,
    input  logic              pdi_rx_last,

    // Reassembled Packet to Validator
    output logic              pkt_assembled_valid,
    input  logic              pkt_consumed_ack,
    output logic [PACKET_WORDS*32-1:0] pkt_raw_data,
    output logic              pkt_framing_error,
    output logic              pkt_crc_error
);

    typedef enum logic [2:0] {
        ST_IDLE      = 3'd0,
        ST_RECEIVE   = 3'd1,
        ST_CHECK_CRC = 3'd2,
        ST_READY     = 3'd3,
        ST_DISCARD   = 3'd4
    } rx_state_t;

    rx_state_t state;
    logic [3:0]  word_count;
    logic [31:0] packet_buf [0:PACKET_WORDS-1];
    logic [31:0] crc_accum;
    logic        framing_err_r;
    logic        crc_err_r;

    // Standard IEEE 802.3 32-bit Parallel CRC calculation for 32-bit word
    function automatic logic [31:0] crc32_word(input logic [31:0] current_crc, input logic [31:0] data_in);
        logic [31:0] c;
        logic [31:0] d;
        begin
            c = current_crc;
            d = data_in;
            // 32-bit parallel step of standard Ethernet polynomial 0xEDB88320 (reflected)
            for (int i = 0; i < 32; i++) begin
                if ((c[0] ^ d[i]) == 1'b1)
                    c = {1'b0, c[31:1]} ^ 32'hEDB88320;
                else
                    c = {1'b0, c[31:1]};
            end
            crc32_word = c;
        end
    endfunction

    assign pdi_rx_ready        = (state == ST_IDLE) || (state == ST_RECEIVE) || (state == ST_DISCARD);
    assign pkt_assembled_valid = (state == ST_READY);
    assign pkt_framing_error   = framing_err_r;
    assign pkt_crc_error       = crc_err_r;

    // Pack array into flat output bus
    always_comb begin
        for (int i = 0; i < PACKET_WORDS; i++) begin
            pkt_raw_data[i*32 +: 32] = packet_buf[i];
        end
    end

    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state          <= ST_IDLE;
            word_count     <= 4'd0;
            crc_accum      <= 32'hFFFFFFFF;
            framing_err_r  <= 1'b0;
            crc_err_r      <= 1'b0;
            for (int i = 0; i < PACKET_WORDS; i++) begin
                packet_buf[i] <= 32'd0;
            end
        end else begin
            case (state)
                ST_IDLE: begin
                    framing_err_r <= 1'b0;
                    crc_err_r     <= 1'b0;
                    if (pdi_rx_valid) begin
                        if (pdi_rx_data == PDI_MAGIC) begin
                            packet_buf[0] <= pdi_rx_data;
                            crc_accum     <= crc32_word(32'hFFFFFFFF, pdi_rx_data);
                            word_count    <= 4'd1;
                            state         <= ST_RECEIVE;
                        end else begin
                            framing_err_r <= 1'b1;
                            state         <= ST_DISCARD;
                        end
                    end
                end

                ST_RECEIVE: begin
                    if (pdi_rx_valid) begin
                        if (pdi_rx_data == PDI_MAGIC) begin
                            // Premature magic: prior packet was truncated. Resynchronize immediately on new frame!
                            packet_buf[0] <= PDI_MAGIC;
                            crc_accum     <= crc32_word(32'hFFFFFFFF, PDI_MAGIC);
                            word_count    <= 4'd1;
                            framing_err_r <= 1'b0;
                            crc_err_r     <= 1'b0;
                        end else begin
                            packet_buf[word_count] <= pdi_rx_data;

                            if (word_count < (PACKET_WORDS - 1)) begin
                                crc_accum <= crc32_word(crc_accum, pdi_rx_data);
                            end

                            if (word_count == (PACKET_WORDS - 1)) begin
                                // Last expected word: check framing and CRC
                                if (!pdi_rx_last) begin
                                    framing_err_r <= 1'b1;
                                end
                                state <= ST_CHECK_CRC;
                            end else if (pdi_rx_last) begin
                                // Premature last word
                                framing_err_r <= 1'b1;
                                state         <= ST_IDLE;
                            end else begin
                                word_count <= word_count + 4'd1;
                            end
                        end
                    end
                end

                ST_CHECK_CRC: begin
                    if ((crc_accum ^ 32'hFFFFFFFF) != packet_buf[PACKET_WORDS - 1]) begin
                        crc_err_r <= 1'b1;
                    end
                    state <= ST_READY;
                end

                ST_READY: begin
                    if (pkt_consumed_ack) begin
                        state <= ST_IDLE;
                    end
                end

                ST_DISCARD: begin
                    if (pdi_rx_valid && pdi_rx_last) begin
                        state <= ST_IDLE;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end

endmodule

`endif // PDI_INGRESS_SV
