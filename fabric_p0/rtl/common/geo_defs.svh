// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Definitions header for synthesis & simulation

`ifndef GEO_DEFS_SVH
`define GEO_DEFS_SVH

    // --- Work-Cell Lifecycle States (Section 4.2) ---
    typedef enum logic [3:0] {
        STATE_EMPTY           = 4'd0,
        STATE_LOADED          = 4'd1,
        STATE_WAIT_DEPENDENCY = 4'd2,
        STATE_READY           = 4'd3,
        STATE_DISPATCHED      = 4'd4,
        STATE_EXECUTING       = 4'd5,
        STATE_RESULT_PENDING  = 4'd6,
        STATE_CERTIFYING      = 4'd7,
        STATE_COMMITTED       = 4'd8,
        STATE_REJECTED        = 4'd9,
        STATE_HALTED          = 4'd10,
        STATE_FAULT           = 4'd11
    } work_state_t;

    // --- Authority / Commit Outcomes (Section 9.2) ---
    typedef enum logic [1:0] {
        OUTCOME_COMMIT  = 2'd0,
        OUTCOME_REJECT  = 2'd1,
        OUTCOME_REFUSE  = 2'd2,
        OUTCOME_FAULT   = 2'd3
    } commit_outcome_t;

    // --- PSMSL / GEO Opcodes (Section 5.2 & 5.3) ---
    typedef enum logic [5:0] {
        // Basic fixed-point
        OP_NOP                 = 6'd0,
        OP_ADD                 = 6'd1,
        OP_SUB                 = 6'd2,
        OP_MUL                 = 6'd3,
        OP_COMPARE             = 6'd4,

        // Cl(2,0) multivector geometric operations
        OP_CL20_PRODUCT        = 6'd5,
        OP_REVERSE             = 6'd6,
        OP_GRADE_INVOLUTION    = 6'd7,
        OP_CLIFFORD_CONJUGATE  = 6'd8,
        OP_VECTOR_DOT          = 6'd9,
        OP_VECTOR_WEDGE        = 6'd10,
        OP_COMMUTATOR          = 6'd11,
        OP_ANTICOMMUTATOR      = 6'd12,
        OP_SCALAR_PROJECTION   = 6'd13,
        OP_VECTOR_PROJECTION   = 6'd14,
        OP_BIVECTOR_PROJECTION = 6'd15,
        OP_NORM_SQUARED        = 6'd16,
        OP_COMPOSE             = 6'd17,

        // Matrix Bridge M2(R) <-> Cl(2,0)
        OP_MATRIX_TO_CL20      = 6'd18,
        OP_CL20_TO_MATRIX      = 6'd19,

        // General ALU Primitives (Section 6)
        OP_ALU_LOAD            = 6'd20,
        OP_ALU_STORE           = 6'd21,
        OP_ALU_MOVE            = 6'd22,
        OP_ALU_SHIFT           = 6'd23,
        OP_ALU_AND             = 6'd24,
        OP_ALU_OR              = 6'd25,
        OP_ALU_XOR             = 6'd26,
        OP_ALU_SELECT          = 6'd27,
        OP_ALU_BRANCH_IF       = 6'd28,
        OP_ALU_EMIT            = 6'd29,
        OP_ALU_HALT            = 6'd30,
        OP_ALU_ADD             = 6'd31,
        OP_ALU_SUB             = 6'd32,
        OP_ALU_MUL             = 6'd33
    } geo_opcode_t;

    // --- Cl(2,0) Multivector Structure ---
    typedef struct packed {
        logic signed [31:0] s;
        logic signed [31:0] e1;
        logic signed [31:0] e2;
        logic signed [31:0] e12;
    } cl20_mv_t;

    // --- 2x2 Real Matrix Structure ---
    typedef struct packed {
        logic signed [31:0] a;
        logic signed [31:0] b;
        logic signed [31:0] c;
        logic signed [31:0] d;
    } mat2_t;

    // --- Graph Subsystem Commands (Section 7) ---
    typedef enum logic [3:0] {
        GRAPH_CMD_NOP               = 4'd0,
        GRAPH_CMD_NODE_LOOKUP       = 4'd1,
        GRAPH_CMD_EDGE_FETCH        = 4'd2,
        GRAPH_CMD_FOLLOW            = 4'd3,
        GRAPH_CMD_RELATION_MATCH    = 4'd4,
        GRAPH_CMD_NODE_TYPE_MATCH   = 4'd5,
        GRAPH_CMD_NEIGHBORHOOD_BEGIN= 4'd6,
        GRAPH_CMD_NEIGHBORHOOD_NEXT = 4'd7
    } graph_cmd_t;

    // --- Hardware Graph Records ---
    typedef struct packed {
        logic [15:0] edge_base;
        logic [15:0] edge_count;
        logic [7:0]  node_type;
        logic [7:0]  flags;
        logic [15:0] version;
    } graph_node_t;

    typedef struct packed {
        logic [15:0] target_node;
        logic [7:0]  relation_type;
        logic [7:0]  flags;
    } graph_edge_t;

    // --- Semantic Query Interface ---
    typedef struct packed {
        logic [15:0] start_node;
        logic [7:0]  relation_filter;     // 0 = match all
        logic [7:0]  target_type_filter;  // 0 = match all
        logic [1:0]  radius;              // 1, 2, or 3
    } graph_query_t;

    // --- UoW Dependency Condition Types (Section 4 & P0.5) ---
    typedef enum logic [2:0] {
        DEP_COND_BITMASK          = 3'd0, // DEPENDENCY_READY: prior cell committed bitmask
        DEP_COND_RELATION_EXISTS  = 3'd1, // RELATION_EXISTS: edge from start_node with rel_filter
        DEP_COND_CAPABILITY_MATCH = 3'd2, // CAPABILITY_MATCH: start_node type/capability flags match
        DEP_COND_RELATION_FILTER  = 3'd3, // RELATION_FILTER: relation filter match
        DEP_COND_NEIGHBOR_EXPAND  = 3'd4  // NEIGHBORHOOD_EXPAND: reachable neighborhood within radius
    } dep_cond_type_t;

    // --- Hardware Graph Mutation Operations (Section 7.4) ---
    typedef enum logic [1:0] {
        GRAPH_MUT_NOP         = 2'd0,
        GRAPH_MUT_ADD_EDGE    = 2'd1,
        GRAPH_MUT_ADD_NODE    = 2'd2,
        GRAPH_MUT_UPDATE_NODE = 2'd3
    } graph_mut_cmd_t;

    // --- Autonomous Bounded Closure Status (Section 22 & P0.7) ---
    typedef enum logic [1:0] {
        CLOSURE_IN_PROGRESS         = 2'd0,
        CLOSED_BOUNDED_UNIVERSE     = 2'd1,
        INCOMPLETE_UNIVERSE_NULLITY = 2'd2,
        CLOSURE_FAULT               = 2'd3
    } closure_status_t;

    // --- Workload Dependency Topology (P0.6C Capacity Envelope) ---
    typedef enum logic [2:0] {
        TOPO_INDEPENDENT     = 3'd0,
        TOPO_CHAIN           = 3'd1,
        TOPO_FANOUT          = 3'd2,
        TOPO_FANIN           = 3'd3,
        TOPO_DIAMOND         = 3'd4,
        TOPO_HIGH_CONTENTION = 3'd5,
        TOPO_MIXED           = 3'd6
    } workload_topo_t;

    // --- UoW Definition Descriptor ---
    typedef struct packed {
        logic [31:0]         uow_id;
        geo_opcode_t         opcode;
        logic [7:0]          dest_addr;
        logic [7:0]          src_a_addr;
        logic [7:0]          src_b_addr;
        logic [127:0]        dep_mask; // Supports up to 128 concurrent work cells
        logic [31:0]         pre_state_hash;
        logic [31:0]         auth_token;
        cl20_mv_t            imm_operand;
        logic                use_immediate;
        dep_cond_type_t      dep_cond;
        graph_query_t        graph_query;
        logic                has_graph_mut;
        graph_mut_cmd_t      graph_mut_cmd;
        logic [15:0]         graph_mut_node;
        logic [15:0]         graph_mut_target;
        logic [7:0]          graph_mut_rel;
        logic [7:0]          graph_mut_flags;
    } uow_desc_t;

    // --- Evidence Record Structure (Section 10.1) ---
    typedef struct packed {
        logic [31:0]         uow_id;
        logic [63:0]         pre_state_hash;
        logic [63:0]         post_state_hash;
        logic [63:0]         candidate_hash;
        logic [31:0]         cert_id;
        logic [63:0]         prev_evidence_root;
        logic [63:0]         current_evidence_root;
        logic [31:0]         causal_seq;
    } evidence_record_t;

    // --- Hardware Telemetry Diagnostic Counters (Section 17 & P0.6C) ---
    typedef struct packed {
        logic [31:0] cycles;
        logic [31:0] uow_admitted;
        logic [31:0] uow_committed;
        logic [31:0] uow_rejected;
        logic [31:0] uow_refused;
        logic [31:0] ops_executed;
        logic [31:0] op_stalls;
        logic [31:0] mem_reads;
        logic [31:0] mem_writes;
        logic [31:0] evidence_records;
        logic [31:0] overflow_events;
        logic [31:0] fault_events;
        // P0.6C Capacity & Bottleneck Profiling Telemetry
        logic [31:0] stall_operator_wait;
        logic [31:0] stall_dep_wait;
        logic [31:0] stall_auth_wait;
        logic [31:0] stall_mem_wait;
        logic [31:0] peak_queue_occupancy;
        logic [31:0] backpressure_cycles;
    } geo_telemetry_t;

`endif // GEO_DEFS_SVH

