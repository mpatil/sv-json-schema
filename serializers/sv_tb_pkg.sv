`ifndef SV_TB_PKG_SV
`define SV_TB_PKG_SV

package sv_tb_pkg;
`include "uvm_macros.svh"
`include "sv_json_macros.svh"
`include "json_macros.svh"

  import uvm_pkg::*;

`ifdef JSON_PKG
  import json_pkg::JSONValue;
`endif

`include "config_m.sv"

endpackage
`endif
