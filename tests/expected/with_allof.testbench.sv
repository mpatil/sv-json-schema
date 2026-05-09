import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

  initial begin
      automatic Val_ jv = pJSON("examples/data/Identifiable.json");

      if (jv == null) begin
        $display("JSON parse failed: Identifiable");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Identifiable[i]: %0d", i);
          v.m_Identifiable = new();
          void'(v.m_Identifiable.randomize());
          v.m_Identifiable.fromJSON(jv.getByIndex(i));
          v.m_Identifiable.print(uvm_default_table_printer);
          jv_out = v.m_Identifiable.toJSON();
          fh = $fopen($sformatf("Identifiable%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

  initial begin
      automatic Val_ jv = pJSON("examples/data/Cfg.json");

      if (jv == null) begin
        $display("JSON parse failed: Cfg");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Cfg[i]: %0d", i);
          v.m_Cfg = new();
          void'(v.m_Cfg.randomize());
          v.m_Cfg.fromJSON(jv.getByIndex(i));
          v.m_Cfg.print(uvm_default_table_printer);
          jv_out = v.m_Cfg.toJSON();
          fh = $fopen($sformatf("Cfg%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end


endprogram
