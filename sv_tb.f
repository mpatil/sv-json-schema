-64 +define+UVM
 -uvm -uvmhome uvm-1.2
 JSONinSV/json_pkg/json_pkg.sv
+incdir+JSONinSV/json_pkg
+incdir+serializers
+define+JSON_PKG serializers/sv_tb_pkg.sv +incdir+./
+UVM_VERBOSITY=UVM_MEDIUM
