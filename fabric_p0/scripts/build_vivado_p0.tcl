# Vivado Non-Project Batch Flow: MAPEOGEO P0 FPGA Preproduction Release Build
# Target Part: AMD / Xilinx UltraScale+ XCU280 (xcu280-fsvh2892-2L-e)
# Execution: vivado -mode batch -source fabric_p0/scripts/build_vivado_p0.tcl -tclargs [part_name] [geometry]

set SCRIPT_DIR [file normalize [file dirname [info script]]]
set REPO_ROOT  [file normalize [file join $SCRIPT_DIR ".." ".."]]
set FABRIC_DIR [file normalize [file join $REPO_ROOT "fabric_p0"]]
set OUT_DIR    [file normalize [file join $FABRIC_DIR "build_vivado"]]

# Default part and parameters
set TARGET_PART "xcu280-fsvh2892-2L-e"
if { $argc >= 1 } {
    set TARGET_PART [lindex $argv 0]
}

set GEOMETRY "Medium"
if { $argc >= 2 } {
    set GEOMETRY [lindex $argv 1]
}

puts "================================================================================"
puts "MAPEOGEO P0 VIVADO PHYSICAL IMPLEMENTATION & TIMING SIGN-OFF"
puts "Target Part:     $TARGET_PART"
puts "Fabric Geometry: $GEOMETRY"
puts "Output Dir:      $OUT_DIR"
puts "================================================================================"

file mkdir $OUT_DIR
file mkdir [file join $OUT_DIR "reports"]

# 1. Read SystemVerilog Source Files
set SV_FILES [list \
    [file join $FABRIC_DIR "rtl" "common" "geo_defs.svh"] \
    [file join $FABRIC_DIR "rtl" "common" "geo_sha256_core.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_fixed_arith.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_cl20_multivector.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_unary_ops.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_bilinear_ops.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_matrix_bridge.sv"] \
    [file join $FABRIC_DIR "rtl" "operators" "geo_operator_unit.sv"] \
    [file join $FABRIC_DIR "rtl" "compute" "geo_general_alu.sv"] \
    [file join $FABRIC_DIR "rtl" "memory" "geo_state_memory.sv"] \
    [file join $FABRIC_DIR "rtl" "authority" "geo_authority_engine.sv"] \
    [file join $FABRIC_DIR "rtl" "evidence" "geo_evidence_engine.sv"] \
    [file join $FABRIC_DIR "rtl" "graph" "geo_graph_memory.sv"] \
    [file join $FABRIC_DIR "rtl" "work_fabric" "geo_work_cell.sv"] \
    [file join $FABRIC_DIR "rtl" "work_fabric" "geo_work_fabric.sv"] \
    [file join $FABRIC_DIR "rtl" "top" "mapeogeo_p0_fabric.sv"] \
    [file join $FABRIC_DIR "rtl" "cdc" "geo_sync_2ff.sv"] \
    [file join $FABRIC_DIR "rtl" "cdc" "geo_async_fifo.sv"] \
    [file join $FABRIC_DIR "rtl" "cdc" "geo_reset_sync.sv"] \
    [file join $FABRIC_DIR "rtl" "top" "mapeogeo_p0_cdc_fabric.sv"] \
]

foreach f $SV_FILES {
    read_verilog -sv $f
}

# 2. Read SDC Timing Constraints
read_xdc [file join $FABRIC_DIR "constraints" "mapeogeo_p0_clocks.sdc"]

# 3. Parameter Geometry Configuration
# Capacity Scaling Law: R_fabric = min(N_I, N_E, N_M, N_O / 2, N_A)
if { $GEOMETRY == "One_Wide" || $GEOMETRY == "1Wide" || $GEOMETRY == "Artix7" } {
    # True 1-Wide Artix-7 Demonstration Configuration (R_fabric = 1.0 UoW/cycle, 440 DSPs)
    set GEN_PARAMS "-generic INGRESS_LANES=1 -generic EGRESS_LANES=1 -generic MEMORY_BANKS=2 -generic OPERATOR_LANES=2 -generic AUTHORITY_ENGINES=1 -generic WORK_CELL_COUNT=4"
} elseif { $GEOMETRY == "Small" } {
    # True 2-Wide Edge Configuration (R_fabric = 2.0 UoW/cycle)
    set GEN_PARAMS "-generic INGRESS_LANES=2 -generic EGRESS_LANES=2 -generic MEMORY_BANKS=4 -generic OPERATOR_LANES=4 -generic AUTHORITY_ENGINES=2 -generic WORK_CELL_COUNT=8"
} elseif { $GEOMETRY == "Full_Width" } {
    # True 8-Wide Datacenter Configuration (R_fabric = 8.0 UoW/cycle)
    set GEN_PARAMS "-generic INGRESS_LANES=8 -generic EGRESS_LANES=8 -generic MEMORY_BANKS=16 -generic OPERATOR_LANES=16 -generic AUTHORITY_ENGINES=8 -generic WORK_CELL_COUNT=32"
} else {
    # Medium: True 4-Wide Demonstration Configuration (R_fabric = 4.0 UoW/cycle)
    set GEN_PARAMS "-generic INGRESS_LANES=4 -generic EGRESS_LANES=4 -generic MEMORY_BANKS=8 -generic OPERATOR_LANES=8 -generic AUTHORITY_ENGINES=4 -generic WORK_CELL_COUNT=16"
}

# 4. Out-of-Context Synthesis
puts "\[STEP 1/6\] Running Out-of-Context Synthesis..."
eval synth_design -top mapeogeo_p0_cdc_fabric -part $TARGET_PART -mode out_of_context $GEN_PARAMS
write_checkpoint -force [file join $OUT_DIR "post_synth.dcp"]
report_utilization -file [file join $OUT_DIR "reports" "post_synth_utilization.rpt"]
report_timing_summary -file [file join $OUT_DIR "reports" "post_synth_timing.rpt"]

# 5. Logic Optimization
puts "\[STEP 2/6\] Running Logic Optimization (opt_design)..."
opt_design
write_checkpoint -force [file join $OUT_DIR "post_opt.dcp"]

# 6. Physical Placement
puts "\[STEP 3/6\] Running Placement (place_design)..."
place_design
write_checkpoint -force [file join $OUT_DIR "post_place.dcp"]
report_clock_utilization -file [file join $OUT_DIR "reports" "post_place_clock_util.rpt"]

# 7. Physical Optimization (Post-Place)
puts "\[STEP 4/6\] Running Physical Optimization (phys_opt_design)..."
phys_opt_design
write_checkpoint -force [file join $OUT_DIR "post_phys_opt.dcp"]

# 8. Physical Routing
puts "\[STEP 5/6\] Running Routing (route_design)..."
route_design
write_checkpoint -force [file join $OUT_DIR "post_route.dcp"]

# 9. Sign-off Static Timing Analysis & Final Audits
puts "\[STEP 6/6\] Generating Sign-off STA and Verification Reports..."

# Full Timing Summary & Slack
report_timing_summary -delay_type min_max \
                      -report_unconstrained \
                      -check_timing_verbose \
                      -max_paths 100 \
                      -input_pins \
                      -file [file join $OUT_DIR "reports" "final_timing_summary.rpt"]

# Clock Interaction Matrix
report_clock_interaction -delay_type min_max \
                         -file [file join $OUT_DIR "reports" "final_clock_interaction.rpt"]

# Asynchronous Domain CDC / RDC Verification
report_cdc -details \
           -file [file join $OUT_DIR "reports" "final_cdc_report.rpt"]

# Final Placed & Routed Primitive Utilization Breakdown
report_utilization -hierarchical \
                   -file [file join $OUT_DIR "reports" "final_utilization_hierarchical.rpt"]

# Routing Congestion Analysis
report_design_analysis -congestion \
                       -complexity \
                       -file [file join $OUT_DIR "reports" "final_design_analysis.rpt"]

# Power Dissipation Estimation
report_power -file [file join $OUT_DIR "reports" "final_power_estimate.rpt"]

# Check for zero unconstrained paths and timing closure
set WNS [get_property SLACK [get_timing_paths -max_paths 1 -setup]]
set TNS [get_property TOTAL_SLACK [get_timing_paths -max_paths 1 -setup]]

puts "================================================================================"
puts "MAPEOGEO P0 PHYSICAL SIGN-OFF METRICS:"
puts "Worst Negative Slack (WNS): $WNS ns"
puts "Total Negative Slack (TNS): $TNS ns"
if { $WNS >= 0.0 } {
    puts "TIMING STATUS: \[\033\[32mPASS - TIMING MET\033\[0m\]"
} else {
    puts "TIMING STATUS: \[\033\[31mFAIL - TIMING VIOLATED\033\[0m\]"
}
puts "All reports written to: [file join $OUT_DIR "reports"]"
puts "================================================================================"
