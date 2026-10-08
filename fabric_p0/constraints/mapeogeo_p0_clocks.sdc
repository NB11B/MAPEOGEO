# ==============================================================================
# SDC 2.1 Timing Constraints: MAPEOGEO P0 6-Domain Asynchronous Spatial Fabric
# Project: MAPEOGEO Preproduction Hardening (Gate RTL-10 SDC Sign-Off)
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. Physical Primary Clocks
# ------------------------------------------------------------------------------
create_clock -name clk_ingress -period 8.000 [get_ports clk_ingress]   ;# 125.00 MHz
create_clock -name clk_auth    -period 10.000 [get_ports clk_auth]      ;# 100.00 MHz
create_clock -name clk_op      -period 6.000  [get_ports clk_op]        ;# 166.67 MHz
create_clock -name clk_mem     -period 5.000  [get_ports clk_mem]       ;# 200.00 MHz
create_clock -name clk_ev      -period 7.500  [get_ports clk_ev]        ;# 133.33 MHz
create_clock -name clk_egress  -period 6.400  [get_ports clk_egress]    ;# 156.25 MHz

# ------------------------------------------------------------------------------
# 2. Clock Uncertainty & Jitter Margins
# ------------------------------------------------------------------------------
set_clock_uncertainty -setup 0.150 [get_clocks clk_ingress]
set_clock_uncertainty -hold  0.050 [get_clocks clk_ingress]

set_clock_uncertainty -setup 0.150 [get_clocks clk_auth]
set_clock_uncertainty -hold  0.050 [get_clocks clk_auth]

set_clock_uncertainty -setup 0.150 [get_clocks clk_op]
set_clock_uncertainty -hold  0.050 [get_clocks clk_op]

set_clock_uncertainty -setup 0.150 [get_clocks clk_mem]
set_clock_uncertainty -hold  0.050 [get_clocks clk_mem]

set_clock_uncertainty -setup 0.150 [get_clocks clk_ev]
set_clock_uncertainty -hold  0.050 [get_clocks clk_ev]

set_clock_uncertainty -setup 0.150 [get_clocks clk_egress]
set_clock_uncertainty -hold  0.050 [get_clocks clk_egress]

# ------------------------------------------------------------------------------
# 3. Clock Domain Relationships (Asynchronous Groups)
# ------------------------------------------------------------------------------
set_clock_groups -asynchronous \
    -group [get_clocks clk_ingress] \
    -group [get_clocks clk_auth] \
    -group [get_clocks clk_op] \
    -group [get_clocks clk_mem] \
    -group [get_clocks clk_ev] \
    -group [get_clocks clk_egress]

# ------------------------------------------------------------------------------
# 4. CDC Max Delay & Skew Constraints on Gray-Pointer Crossings
# ------------------------------------------------------------------------------
# Ingress FIFO (clk_ingress <-> clk_op)
set_max_delay 6.000 -from [get_cells -hierarchical *gen_ingress_cdc*.u_ing_cdc_fifo*wptr_gray*] -to [get_cells -hierarchical *gen_ingress_cdc*.u_ing_cdc_fifo*u_sync_w2r*sync_stage1*] -datapath_only
set_max_delay 8.000 -from [get_cells -hierarchical *gen_ingress_cdc*.u_ing_cdc_fifo*rptr_gray*] -to [get_cells -hierarchical *gen_ingress_cdc*.u_ing_cdc_fifo*u_sync_r2w*sync_stage1*] -datapath_only

# Egress FIFO (clk_op <-> clk_egress)
set_max_delay 6.400 -from [get_cells -hierarchical *gen_egress_cdc*.u_eg_cdc_fifo*wptr_gray*] -to [get_cells -hierarchical *gen_egress_cdc*.u_eg_cdc_fifo*u_sync_w2r*sync_stage1*] -datapath_only
set_max_delay 6.000 -from [get_cells -hierarchical *gen_egress_cdc*.u_eg_cdc_fifo*rptr_gray*] -to [get_cells -hierarchical *gen_egress_cdc*.u_eg_cdc_fifo*u_sync_r2w*sync_stage1*] -datapath_only

# Max skew across individual bits of Gray pointer buses
set_bus_skew 1.500 -from [get_cells -hierarchical *wptr_gray*] -to [get_cells -hierarchical *u_sync_*sync_stage1*]
set_bus_skew 1.500 -from [get_cells -hierarchical *rptr_gray*] -to [get_cells -hierarchical *u_sync_*sync_stage1*]

# ------------------------------------------------------------------------------
# 5. Reset Synchronizer Exceptions
# ------------------------------------------------------------------------------
set_false_path -from [get_ports rst_ingress_async_n] -to [get_cells -hierarchical *u_sync_rst_ing*rst_stage1*]
set_false_path -from [get_ports rst_auth_async_n]    -to [get_cells -hierarchical *u_sync_rst_auth*rst_stage1*]
set_false_path -from [get_ports rst_op_async_n]      -to [get_cells -hierarchical *u_sync_rst_op*rst_stage1*]
set_false_path -from [get_ports rst_mem_async_n]     -to [get_cells -hierarchical *u_sync_rst_mem*rst_stage1*]
set_false_path -from [get_ports rst_ev_async_n]      -to [get_cells -hierarchical *u_sync_rst_ev*rst_stage1*]
set_false_path -from [get_ports rst_egress_async_n]  -to [get_cells -hierarchical *u_sync_rst_eg*rst_stage1*]

# ------------------------------------------------------------------------------
# 6. Primary Input / Output Delay Constraints
# ------------------------------------------------------------------------------
# Ingress Port Group (clk_ingress domain)
set_input_delay  -clock clk_ingress -max 2.000 [get_ports ingress_valid*]
set_input_delay  -clock clk_ingress -min 0.500 [get_ports ingress_valid*]
set_input_delay  -clock clk_ingress -max 2.000 [get_ports ingress_desc*]
set_input_delay  -clock clk_ingress -min 0.500 [get_ports ingress_desc*]
set_output_delay -clock clk_ingress -max 2.000 [get_ports ingress_ready*]
set_output_delay -clock clk_ingress -min 0.500 [get_ports ingress_ready*]

# Egress Port Group (clk_egress domain)
set_output_delay -clock clk_egress  -max 2.000 [get_ports egress_valid*]
set_output_delay -clock clk_egress  -min 0.500 [get_ports egress_valid*]
set_output_delay -clock clk_egress  -max 2.000 [get_ports egress_uow_id*]
set_output_delay -clock clk_egress  -min 0.500 [get_ports egress_uow_id*]
set_output_delay -clock clk_egress  -max 2.000 [get_ports egress_status*]
set_output_delay -clock clk_egress  -min 0.500 [get_ports egress_status*]
set_output_delay -clock clk_egress  -max 2.000 [get_ports egress_result*]
set_output_delay -clock clk_egress  -min 0.500 [get_ports egress_result*]
set_output_delay -clock clk_egress  -max 2.000 [get_ports egress_evidence_root*]
set_output_delay -clock clk_egress  -min 0.500 [get_ports egress_evidence_root*]
set_input_delay  -clock clk_egress  -max 2.000 [get_ports egress_ready*]
set_input_delay  -clock clk_egress  -min 0.500 [get_ports egress_ready*]

# Core Control & Telemetry Group (clk_op domain)
set_input_delay  -clock clk_op      -max 2.000 [get_ports boot_trigger]
set_input_delay  -clock clk_op      -min 0.500 [get_ports boot_trigger]
set_output_delay -clock clk_op      -max 2.000 [get_ports boot_complete]
set_output_delay -clock clk_op      -min 0.500 [get_ports boot_complete]
set_output_delay -clock clk_op      -max 2.000 [get_ports fabric_halted]
set_output_delay -clock clk_op      -min 0.500 [get_ports fabric_halted]
set_output_delay -clock clk_op      -max 2.000 [get_ports telemetry_out*]
set_output_delay -clock clk_op      -min 0.500 [get_ports telemetry_out*]
set_output_delay -clock clk_op      -max 2.000 [get_ports current_evidence_root_out*]
set_output_delay -clock clk_op      -min 0.500 [get_ports current_evidence_root_out*]
set_output_delay -clock clk_op      -max 2.000 [get_ports active_work_cells_out*]
set_output_delay -clock clk_op      -min 0.500 [get_ports active_work_cells_out*]
set_output_delay -clock clk_op      -max 2.000 [get_ports semantic_evidence_root_out*]
set_output_delay -clock clk_op      -min 0.500 [get_ports semantic_evidence_root_out*]
