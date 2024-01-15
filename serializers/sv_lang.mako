class config_m extends uvm_object;
    `uvm_object_utils(config_m)

% for ty in params['enums']:
<%
    decls = ',\n        '.join(params['enums'][ty])
%>\
    typedef enum {
        ${decls}
    } ${ty};
    typedef uvm_enum_wrapper#(${ty}) ${ty}_wrapper;

% endfor

% for ty in params['classes']:
    typedef class ${ty};
% endfor

% for ty in params['classes']:
<%
    mem_s   = []
    con_s   = []
    prand_s = []
    fjson_s = []
    tjson_s = []
    prnt_s  = []
    for mem in params['classes'][ty]:
        n = mem['name']
        r = f"rand " if mem['isRand'] else ""
        w = f" [{mem['width']}-1:0]" if mem['width'] is not None else ""
        m = f"{r}{mem['type']}{w} m_{n}"
        e = f", {mem['type']}" if mem['isEnum'] else ""

        fjson_s.append(f"`from_json_{mem['type_cat']}({n}{e})")
        tjson_s.append(f"`to_json_{mem['type_cat']}({n})")

        if mem['isArray']:
            if mem['type_cat'] == "string_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_string("{n}", m_{n}[i]);
            end""")
            elif mem['type_cat'] == "enum_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_string("{n}", m_{n}[i].name);
            end""")
            elif mem['type_cat'] == "int_array":
                if mem['type'] == "real":
                    uvm_prnt = f"""printer.print_real("{n}", m_{n}[i]);"""
                else:
                    uvm_prnt = f"""printer.print_field_int("{n}", m_{n}[i], 32, UVM_DEC);"""
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                {uvm_prnt}
            end""")
            elif mem['type_cat'] == "bool_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_field_int("{n}", m_{n}[i], 1, UVM_BIN);
            end""")
            elif mem['type_cat'] == "hex_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_field_int("{n}", m_{n}[i], {mem['width']}, UVM_HEX);
            end""")
            elif mem['type_cat'] == "object_array":
                prand_s.append(f"""\
            foreach (m_{n}[i]) begin
                m_{n}[i] = new($sformatf("{n}[%0d]", i));
                void'(m_{n}[i].randomize());
            end""")
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_object("{n}", m_{n}[i]);
            end""")

            xi = "" if mem['minItems'] is None else f"m_{n}.size >= {mem['minItems']}; "
            ni = "" if mem['maxItems'] is None else f"m_{n}.size <= {mem['maxItems']}; "

            mem_s.append(f"{m}[];")

            if xi or ni:
                con_s.append(f"constraint {n}_size_c {{ {ni}{xi}}};")

            if mem['minimum'] or mem['maximum']:
                con_s.append(f"constraint {n}_minmax_c {{ {mem['minimum']} {mem['maximum']}}};")
        else:
            if mem['type_cat'] == "string":
                prnt_s.append(f"""\
            printer.print_string("{n}", m_{n});""")
            elif mem['type_cat'] == "enum":
                prnt_s.append(f"""\
            printer.print_string("{n}", m_{n}.name);""")
            elif mem['type_cat'] == "int":
                if mem['type'] == "real":
                    uvm_prnt = f"""printer.print_real("{n}", m_{n});"""
                else:
                    uvm_prnt = f"""printer.print_field_int("{n}", m_{n}, 32, UVM_DEC);"""
                prnt_s.append(f"""\
                {uvm_prnt}""")
            elif mem['type_cat'] == "bool":
                prnt_s.append(f"""\
            printer.print_field_int("{n}", m_{n}, 1, UVM_BIN);""")
            elif mem['type_cat'] == "hex":
                prnt_s.append(f"""\
            printer.print_field_int("{n}", m_{n}, {mem['width']}, UVM_HEX);""")
            elif mem['type_cat'] == "object":
                prand_s.append(f"""\
            m_{n} = new("{n}");
            void'(m_{n}.randomize());""")
                prnt_s.append(f"""\
            printer.print_object("{n}", m_{n});""")

            if mem['def']:
                mem_s.append(f"{m} = {mem['def']};")
            else:
                mem_s.append(f"{m};")

            if mem['minimum'] or mem['maximum']:
                con_s.append(f"constraint {n}_minmax_c {{ {mem['minimum']} {mem['maximum']}}};")

    mems   = '\n        '.join(mem_s)
    cons   = '\n        '.join(con_s)
    prands = '\n'.join(prand_s)
    tjsons = '\n            '.join(tjson_s)
    fjsons = '\n            '.join(fjson_s)
    prnts  = '\n'.join(prnt_s)
%>\
    class ${ty} extends uvm_object;
        `uvm_object_utils(${ty})

        ${mems}

        protected ${ty} m__root;
        protected uvm_object m__parent;

        ${cons}

        function new (string name ="", input uvm_object p__parent = null, input ${ty} p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();
${prands}
        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(JSONValue jv);
            ${fjsons}
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function void toJSON(ref JSONValue jv);
            jv.setObject();
            ${tjsons}
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
${prnts}
        endfunction : do_print

    endclass

% endfor
% for ty in params['classes']:
    ${ty} m_${ty};
% endfor

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

