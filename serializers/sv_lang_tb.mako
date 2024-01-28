import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::*;

program top();

% for ty in params['classes']:
  initial begin
      automatic JSONValue jv = new();
      automatic JSONStatus js = jv.loadFromFile("data/${ty}.json");

      $display("JSONSTatus(${ty}): %0d", js);

      for (int i = 0; i < jv.getArraySize(); i++) begin
        automatic JSONValue jv_out = new();
        automatic config_m v = new();
        $display("${ty}[i]: %0d", i);
        v.m_${ty} = new();
        void'(v.m_${ty}.randomize());
        if (js == 0)
          v.m_${ty}.fromJSON(jv.getArrayElement(i));
        v.m_${ty}.print(uvm_default_table_printer);
        v.m_${ty}.toJSON(jv_out);
        void'(jv_out.dumpToFile($sformatf("${ty}%0d.json", i)));
        end
  end

% endfor

endprogram

