FILELIST = sv_lang.f

all: clean run

clean:
	@/bin/rm -rf qrun.out modelsim.ini qrun.log vsim_stacktrace.vstf
	@/bin/rm -rf __pycache__ serializers/__pycache__
	@/bin/rm -rf config_m.sv testbench.sv *.json

config_m.sv: examples/types.json serializers/sv_lang.mako serializers/sv_lang.py
	python3 app.py --input examples/types.json --template serializers/sv_lang.mako --output config_m.sv
	@python3 app.py --input examples/types.json --template serializers/sv_lang_tb.mako --output testbench.sv

run: config_m.sv testbench.sv
	qrun -64 -sv -mfcu -permissive -f sv_tb.f testbench.sv
