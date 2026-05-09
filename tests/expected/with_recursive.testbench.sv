import uvm_pkg::*;
`include "uvm_macros.svh"
import sv_tb_pkg::*;
import json_pkg::Val_;
import json_pkg::ObjectVal_;
import json_pkg::pJSON;

program top();

  initial begin
      automatic Val_ jv = pJSON("examples/data/Tree.json");

      if (jv == null) begin
        $display("JSON parse failed: Tree");
      end else begin
        for (int i = 0; i < jv.size(); i++) begin
          automatic ObjectVal_ jv_out;
          automatic config_m v = new();
          automatic int fh;
          $display("Tree[i]: %0d", i);
          v.m_Tree = new();
          void'(v.m_Tree.randomize());
          v.m_Tree.fromJSON(jv.getByIndex(i));
          v.m_Tree.print(uvm_default_table_printer);
          jv_out = v.m_Tree.toJSON();
          fh = $fopen($sformatf("Tree%0d.json", i), "w");
          if (fh) begin
            $fwrite(fh, "%s\n", jv_out.convert2string());
            $fclose(fh);
          end
        end
      end
  end


endprogram
