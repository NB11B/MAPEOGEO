// SPDX-License-Identifier: MIT
// MAPEOGEO Preproduction Fabric P0
// Package: geo_pkg
// Vendor-neutral SystemVerilog definitions for standalone computational substrate

`ifndef GEO_PKG_SV
`define GEO_PKG_SV

`timescale 1ns/1ps

`include "geo_defs.svh"

package geo_pkg;
    parameter int DEFAULT_DATA_WIDTH   = 32;
    parameter int DEFAULT_FRAC_BITS    = 16;
    parameter int DEFAULT_ACCUM_WIDTH  = 36;
    parameter int DEFAULT_WORK_CELLS   = 4;
    parameter int STATE_MEM_WORDS      = 256;
    parameter int EVIDENCE_DEPTH       = 64;
endpackage

`endif // GEO_PKG_SV
