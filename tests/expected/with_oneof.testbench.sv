import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

  initial begin
      automatic Val_ jv = pJSON("examples/data/AddrMap.json");

      if (jv == null) begin
        $display("JSON parse failed: AddrMap");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("AddrMap[i]: %0d", i);
          v.m_AddrMap = new();
          void'(v.m_AddrMap.randomize());
          v.m_AddrMap.fromJSON(jv.getByIndex(i));
          v.m_AddrMap.print(uvm_default_table_printer);
          jv_out = v.m_AddrMap.toJSON();
          fh = $fopen($sformatf("AddrMap%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

  initial begin
      automatic Val_ jv = pJSON("examples/data/RegMap.json");

      if (jv == null) begin
        $display("JSON parse failed: RegMap");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("RegMap[i]: %0d", i);
          v.m_RegMap = new();
          void'(v.m_RegMap.randomize());
          v.m_RegMap.fromJSON(jv.getByIndex(i));
          v.m_RegMap.print(uvm_default_table_printer);
          jv_out = v.m_RegMap.toJSON();
          fh = $fopen($sformatf("RegMap%0d.json", i), "w");
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
