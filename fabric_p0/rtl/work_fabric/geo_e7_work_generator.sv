// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Module: geo_e7_work_generator
// Standalone Hardware Workload Generator for E7 32,768 Projector Triples Qualification

`ifndef GEO_E7_WORK_GENERATOR_SV
`define GEO_E7_WORK_GENERATOR_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

module geo_e7_work_generator #(
    parameter int TOTAL_TRIPLES       = 32768, // 32^3 = 2^15
    parameter int BASE_PROJECTOR_ADDR = 0,     // State[0..31] store projectors
    parameter int BASE_SCRATCH_ADDR   = 32     // State[32..63] scratch for R1, R2
) (
    input  logic                   clk,
    input  logic                   reset_n,
    input  logic                   start,
    output logic                   done,

    // Ingress Interface to Work Fabric
    output logic                   ingress_valid,
    input  logic                   ingress_ready,
    output uow_desc_t              ingress_desc,

    // Egress Monitoring Interface from Work Fabric
    input  logic                   egress_valid,
    input  logic                   egress_ready,
    input  logic [31:0]            egress_uow_id,
    input  commit_outcome_t        egress_status,
    input  cl20_mv_t               egress_result,
    input  logic [63:0]            egress_evidence_root,

    // Architectural Qualification Telemetry
    output logic [31:0]            total_triples_completed,
    output logic [31:0]            total_cycles,
    output logic [31:0]            kappa_collisions_detected,
    output logic [31:0]            oriented_separations_detected
);

    typedef enum logic [2:0] {
        ST_GEN_IDLE       = 3'd0,
        ST_GEN_STEP1_EMIT = 3'd1,
        ST_GEN_STEP1_WAIT = 3'd2,
        ST_GEN_STEP2_EMIT = 3'd3,
        ST_GEN_STEP2_WAIT = 3'd4,
        ST_GEN_ADVANCE    = 3'd5,
        ST_GEN_DONE       = 3'd6
    } gen_state_t;

    gen_state_t state;

    // 15-bit triple counter [u : v : w]
    logic [15:0] triple_counter;
    logic [4:0]  u_idx;
    logic [4:0]  v_idx;
    logic [4:0]  w_idx;

    assign u_idx = triple_counter[14:10];
    assign v_idx = triple_counter[9:5];
    assign w_idx = triple_counter[4:0];

    // Scratch address slot (cycles through 8 scratch pairs)
    logic [2:0] slot_idx;
    assign slot_idx = triple_counter[2:0];

    logic [7:0] r1_addr;
    logic [7:0] r2_addr;
    assign r1_addr = BASE_SCRATCH_ADDR + (slot_idx * 2);
    assign r2_addr = BASE_SCRATCH_ADDR + (slot_idx * 2) + 1;

    logic [31:0] completed_count;
    logic [31:0] cycle_cnt;
    logic [31:0] kappa_collisions;
    logic [31:0] oriented_seps;

    assign total_triples_completed       = completed_count;
    assign total_cycles                  = cycle_cnt;
    assign kappa_collisions_detected     = kappa_collisions;
    assign oriented_separations_detected = oriented_seps;
    assign done                          = (state == ST_GEN_DONE);

    // History buffer for detecting kappa-only collisions vs oriented geometric separation
    localparam int HIST_LEN = 32;
    logic signed [31:0] hist_kappa    [0:HIST_LEN-1];
    logic signed [31:0] hist_bivector [0:HIST_LEN-1];
    logic [4:0]         hist_ptr;
    logic [5:0]         hist_valid_count;

    always_ff @(posedge clk or negedge reset_n) begin
        int h;
        if (!reset_n) begin
            completed_count  <= '0;
            kappa_collisions <= '0;
            oriented_seps    <= '0;
            hist_ptr         <= '0;
            hist_valid_count <= '0;
            for (h = 0; h < HIST_LEN; h = h + 1) begin
                hist_kappa[h]    <= '0;
                hist_bivector[h] <= '0;
            end
        end else begin
            if (egress_valid && egress_ready && (egress_status == OUTCOME_COMMIT)) begin
                // Check if this is a Step 2 egress
                if (egress_uow_id[31:16] == 16'h0002) begin
                    completed_count <= completed_count + 1'b1;

                    // Oriented classification: check non-zero bivector orientation
                    if (egress_result.e12 != 32'sd0) begin
                        oriented_seps <= oriented_seps + 1'b1;
                    end

                    // Check for kappa-only collision against history
                    for (h = 0; h < HIST_LEN; h = h + 1) begin
                        if (h < hist_valid_count) begin
                            if (egress_result.s == hist_kappa[h] && egress_result.e12 != hist_bivector[h]) begin
                                kappa_collisions <= kappa_collisions + 1'b1;
                            end
                        end
                    end

                    // Record to history buffer
                    hist_kappa[hist_ptr]    <= egress_result.s;
                    hist_bivector[hist_ptr] <= egress_result.e12;
                    hist_ptr                <= hist_ptr + 1'b1;
                    if (hist_valid_count < HIST_LEN) begin
                        hist_valid_count <= hist_valid_count + 1'b1;
                    end
                end
            end
        end
    end

    // Cycle counter
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            cycle_cnt <= '0;
        end else if (state != ST_GEN_IDLE && state != ST_GEN_DONE) begin
            cycle_cnt <= cycle_cnt + 1'b1;
        end
    end

    // Ingress Work Generation FSM
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            state          <= ST_GEN_IDLE;
            triple_counter <= '0;
            ingress_valid  <= 1'b0;
            ingress_desc   <= '0;
        end else begin
            case (state)
                ST_GEN_IDLE: begin
                    ingress_valid  <= 1'b0;
                    triple_counter <= '0;
                    if (start) begin
                        state <= ST_GEN_STEP1_EMIT;
                    end
                end

                ST_GEN_STEP1_EMIT: begin
                    // Emit Step 1: R1 = Pu * Pv -> r1_addr
                    ingress_valid               <= 1'b1;
                    ingress_desc.uow_id         <= {16'h0001, triple_counter};
                    ingress_desc.opcode         <= OP_CL20_PRODUCT;
                    ingress_desc.src_a_addr     <= BASE_PROJECTOR_ADDR + u_idx;
                    ingress_desc.src_b_addr     <= BASE_PROJECTOR_ADDR + v_idx;
                    ingress_desc.dest_addr      <= r1_addr;
                    ingress_desc.dep_mask       <= 16'd0;
                    ingress_desc.dep_cond       <= DEP_COND_BITMASK;
                    ingress_desc.graph_query    <= '0;
                    ingress_desc.pre_state_hash <= 32'd0;
                    ingress_desc.auth_token     <= 32'hFFFFFFFF;
                    ingress_desc.imm_operand    <= '0;
                    ingress_desc.use_immediate  <= 1'b0;

                    if (ingress_ready && ingress_valid) begin
                        ingress_valid <= 1'b0;
                        state         <= ST_GEN_STEP1_WAIT;
                    end
                end

                ST_GEN_STEP1_WAIT: begin
                    ingress_valid <= 1'b0;
                    // Await Step 1 commit to state memory
                    if (egress_valid && egress_ready && (egress_uow_id == {16'h0001, triple_counter})) begin
                        state <= ST_GEN_STEP2_EMIT;
                    end
                end

                ST_GEN_STEP2_EMIT: begin
                    // Emit Step 2: R2 = R1 * Pw -> r2_addr
                    ingress_valid               <= 1'b1;
                    ingress_desc.uow_id         <= {16'h0002, triple_counter};
                    ingress_desc.opcode         <= OP_CL20_PRODUCT;
                    ingress_desc.src_a_addr     <= r1_addr;
                    ingress_desc.src_b_addr     <= BASE_PROJECTOR_ADDR + w_idx;
                    ingress_desc.dest_addr      <= r2_addr;
                    ingress_desc.dep_mask       <= 16'd0; // R1 committed in state memory
                    ingress_desc.dep_cond       <= DEP_COND_BITMASK;
                    ingress_desc.graph_query    <= '0;
                    ingress_desc.pre_state_hash <= 32'd0;
                    ingress_desc.auth_token     <= 32'hFFFFFFFF;
                    ingress_desc.imm_operand    <= '0;
                    ingress_desc.use_immediate  <= 1'b0;

                    if (ingress_ready && ingress_valid) begin
                        ingress_valid <= 1'b0;
                        state         <= ST_GEN_STEP2_WAIT;
                    end
                end

                ST_GEN_STEP2_WAIT: begin
                    ingress_valid <= 1'b0;
                    // Await Step 2 commit
                    if (egress_valid && egress_ready && (egress_uow_id == {16'h0002, triple_counter})) begin
                        state <= ST_GEN_ADVANCE;
                    end
                end

                ST_GEN_ADVANCE: begin
                    ingress_valid <= 1'b0;
                    if (triple_counter >= TOTAL_TRIPLES - 1) begin
                        state <= ST_GEN_DONE;
                    end else begin
                        triple_counter <= triple_counter + 1'b1;
                        state          <= ST_GEN_STEP1_EMIT;
                    end
                end

                ST_GEN_DONE: begin
                    ingress_valid <= 1'b0;
                end

                default: state <= ST_GEN_IDLE;
            endcase
        end
    end

endmodule

`endif // GEO_E7_WORK_GENERATOR_SV
