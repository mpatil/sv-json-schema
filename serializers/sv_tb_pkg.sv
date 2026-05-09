`ifndef SV_TB_PKG_SV
`define SV_TB_PKG_SV

package sv_tb_pkg;
`include "uvm_macros.svh"
`include "sv_json_macros.svh"

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
  import json_pkg::pJSON;
  import json_pkg::psJSON;

  function automatic Val_ _mkInt(longint x);
    IntVal_ v = new(x);
    return v;
  endfunction

  function automatic Val_ _mkReal(real x);
    RealVal_ v = new(x);
    return v;
  endfunction

  function automatic Val_ _mkStr(string x);
    StringVal_ v = new(x);
    return v;
  endfunction

  function automatic Val_ _mkBool(bit x);
    BoolVal_ v = new(x);
    return v;
  endfunction
`endif

`include "config_m.sv"

endpackage
`endif
