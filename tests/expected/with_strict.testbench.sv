import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

  initial begin
      automatic Val_ jv = pJSON("examples/data/Strict.json");

      if (jv == null) begin
        $display("JSON parse failed: Strict");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Strict[i]: %0d", i);
          v.m_Strict = new();
          void'(v.m_Strict.randomize());
          v.m_Strict.fromJSON(jv.getByIndex(i));
          v.m_Strict.print(uvm_default_table_printer);
          jv_out = v.m_Strict.toJSON();
          fh = $fopen($sformatf("Strict%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

  initial begin
      automatic Val_ jv = pJSON("examples/data/Loose.json");

      if (jv == null) begin
        $display("JSON parse failed: Loose");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Loose[i]: %0d", i);
          v.m_Loose = new();
          void'(v.m_Loose.randomize());
          v.m_Loose.fromJSON(jv.getByIndex(i));
          v.m_Loose.print(uvm_default_table_printer);
          jv_out = v.m_Loose.toJSON();
          fh = $fopen($sformatf("Loose%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end


endprogram
