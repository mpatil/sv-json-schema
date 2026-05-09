import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

% for ty in params['classes']:
  initial begin
      automatic Val_ jv = pJSON("${params['data_dir']}/${ty}.json");

      if (jv == null) begin
        $display("JSON parse failed: ${ty}");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("${ty}[i]: %0d", i);
          v.m_${ty} = new();
          void'(v.m_${ty}.randomize());
          v.m_${ty}.fromJSON(jv.getByIndex(i));
          v.m_${ty}.print(uvm_default_table_printer);
          jv_out = v.m_${ty}.toJSON();
          fh = $fopen($sformatf("${ty}%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

% endfor

endprogram
