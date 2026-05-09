EXAMPLE = axi4_cfg_schema
SCHEMA_DIR = examples
DATA_DIR = $(SCHEMA_DIR)/data
# `app.py` is a shim that puts src/ on sys.path then forwards to the CLI,
# so this works without `pip install -e .`. Once installed, replace with
# `sv-json-schema` for the same effect.
SV_JSON_SCHEMA = python3 app.py

all: clean run

clean:
	@/bin/rm -rf qrun.out modelsim.ini qrun.log vsim_stacktrace.vstf
	@/bin/rm -rf simv simv.daidir csrc ucli.key vc_hdrs.h *.vpd *.fsdb novas.* DVEfiles
	@/bin/rm -rf __pycache__ src/sv_json_schema/__pycache__ tests/__pycache__
	@/bin/rm -rf config_m.sv testbench.sv *.json
	@/bin/rm -rf build dist *.egg-info src/*.egg-info

config_m.sv testbench.sv: $(SCHEMA_DIR)/$(EXAMPLE).json
	$(SV_JSON_SCHEMA) --input $< --class-out config_m.sv --tb-out testbench.sv \
		--tb-data-dir $(DATA_DIR)

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
