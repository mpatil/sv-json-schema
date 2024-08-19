EXAMPLE = axi4_cfg_schema

all: clean run

clean:
	@/bin/rm -rf qrun.out modelsim.ini qrun.log vsim_stacktrace.vstf
	@/bin/rm -rf __pycache__ serializers/__pycache__
	@/bin/rm -rf config_m.sv testbench.sv *.json

config_m.sv: examples/${EXAMPLE}.json serializers/sv_lang.mako serializers/sv_lang.py
	python3 app.py --input examples/${EXAMPLE}.json --template serializers/sv_lang.mako --output config_m.sv
	@python3 app.py --input examples/${EXAMPLE}.json --template examples/sv_lang_tb.mako --output testbench.sv

run: config_m.sv testbench.sv
	qrun -64 -sv -mfcu -permissive -uvm -uvmhome uvm-1.2 -f sv_tb.f testbench.sv

vcsrun: config_m.sv testbench.sv
	vcs -sverilog +incdir+$UVM_HOME/src $UVM_HOME/src/uvm.sv $UVM_HOME/src/dpi/uvm_dpi.cc -CFLAGS -DVCS testbench.sv -f sv_tb.f
	./simv +vcs+lic+wait

