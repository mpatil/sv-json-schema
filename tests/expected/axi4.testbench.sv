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

  initial begin
      automatic Val_ jv = pJSON("examples/data/MasterCfg.json");

      if (jv == null) begin
        $display("JSON parse failed: MasterCfg");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("MasterCfg[i]: %0d", i);
          v.m_MasterCfg = new();
          void'(v.m_MasterCfg.randomize());
          v.m_MasterCfg.fromJSON(jv.getByIndex(i));
          v.m_MasterCfg.print(uvm_default_table_printer);
          jv_out = v.m_MasterCfg.toJSON();
          fh = $fopen($sformatf("MasterCfg%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

  initial begin
      automatic Val_ jv = pJSON("examples/data/SlaveCfg.json");

      if (jv == null) begin
        $display("JSON parse failed: SlaveCfg");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("SlaveCfg[i]: %0d", i);
          v.m_SlaveCfg = new();
          void'(v.m_SlaveCfg.randomize());
          v.m_SlaveCfg.fromJSON(jv.getByIndex(i));
          v.m_SlaveCfg.print(uvm_default_table_printer);
          jv_out = v.m_SlaveCfg.toJSON();
          fh = $fopen($sformatf("SlaveCfg%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end


endprogram
