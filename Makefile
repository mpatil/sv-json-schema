EXAMPLE = axi4_cfg_schema

all: clean run

clean:
	@/bin/rm -rf qrun.out modelsim.ini qrun.log vsim_stacktrace.vstf
	@/bin/rm -rf simv simv.daidir csrc ucli.key vc_hdrs.h *.vpd *.fsdb novas.* DVEfiles
	@/bin/rm -rf __pycache__ serializers/__pycache__
	@/bin/rm -rf config_m.sv testbench.sv *.json

config_m.sv testbench.sv: examples/${EXAMPLE}.json serializers/sv_lang.mako serializers/sv_lang.py serializers/bitvec.py examples/sv_lang_tb.mako
	python3 app.py --input examples/${EXAMPLE}.json --class-out config_m.sv --tb-out testbench.sv

run: config_m.sv testbench.sv
	qrun -64 -sv -mfcu -permissive -uvm -uvmhome uvm-1.2 -f sv_tb.f testbench.sv +UVM_VERBOSITY=UVM_MEDIUM

vcsrun: config_m.sv testbench.sv
	vcs -full64 -sverilog -ntb_opts uvm-1.2 -timescale=1ns/1ps -f sv_tb.f testbench.sv
	./simv +UVM_VERBOSITY=UVM_MEDIUM +vcs+lic+wait

test:
	python3 -m pytest tests

test-fast:
	python3 -m pytest tests --ignore=tests/test_e2e.py

update-golden:
	python3 -m pytest tests/test_generation.py --update-golden

