`ifndef SV_TB_PKG_SV
`define SV_TB_PKG_SV

package sv_tb_pkg;
`include "uvm_macros.svh"
`include "json_macros.svh"

  import uvm_pkg::*;

`ifdef JSON_PKG
  import json_pkg::Val_;
  import json_pkg::ObjectVal_;
  import json_pkg::ArrayVal_;
  import json_pkg::IntVal_;
  import json_pkg::RealVal_;
  import json_pkg::StringVal_;
  import json_pkg::BoolVal_;
  import json_pkg::NullVal_;
  import json_pkg::mkInt;
  import json_pkg::mkReal;
  import json_pkg::mkStr;
  import json_pkg::mkBool;
  import json_pkg::pJSON;
  import json_pkg::psJSON;
`endif

`include "config_m.sv"

endpackage
`endif
