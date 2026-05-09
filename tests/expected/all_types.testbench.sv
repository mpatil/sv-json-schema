import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

  initial begin
      automatic Val_ jv = pJSON("examples/data/Inner.json");

      if (jv == null) begin
        $display("JSON parse failed: Inner");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Inner[i]: %0d", i);
          v.m_Inner = new();
          void'(v.m_Inner.randomize());
          v.m_Inner.fromJSON(jv.getByIndex(i));
          v.m_Inner.print(uvm_default_table_printer);
          jv_out = v.m_Inner.toJSON();
          fh = $fopen($sformatf("Inner%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end

  initial begin
      automatic Val_ jv = pJSON("examples/data/AllTypes.json");

      if (jv == null) begin
        $display("JSON parse failed: AllTypes");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("AllTypes[i]: %0d", i);
          v.m_AllTypes = new();
          void'(v.m_AllTypes.randomize());
          v.m_AllTypes.fromJSON(jv.getByIndex(i));
          v.m_AllTypes.print(uvm_default_table_printer);
          jv_out = v.m_AllTypes.toJSON();
          fh = $fopen($sformatf("AllTypes%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end


endprogram
