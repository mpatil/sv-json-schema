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

% for base in params['oneOfs']:
    typedef class ${base};
% endfor
% for ty in params['classes']:
    typedef class ${ty};
% endfor

% for base, spec in params['oneOfs'].items():
<%
    disc = spec['discriminator']
    cases = '\n              '.join(
        f'"{br["value"]}": begin {br["name"]} _t = new(""); _t.fromJSON(jv); result = _t; end'
        for br in spec['branches']
    )
%>\
    class ${base} extends uvm_object;
        `uvm_object_utils(${base})

        function new (string name ="");
            super.new(name);
        endfunction : new

`ifdef JSON_PKG
        static function ${base} fromJSONFactory(Val_ jv);
            string disc;
            ${base} result = null;
            if (jv == null) return null;
            if (jv.getByKey("${disc}") == null) begin
              `uvm_error("${base}", "discriminator field \"${disc}\" missing from input")
              return null;
            end
            disc = jv.getByKey("${disc}").asString();
            case (disc)
              ${cases}
              default: `uvm_error("${base}", $sformatf("unknown ${disc}: %s", disc))
            endcase
            return result;
        endfunction : fromJSONFactory

        virtual function void fromJSON(Val_ jv);
        endfunction : fromJSON

        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            return jv;
        endfunction : toJSON
`endif
    endclass

% endfor

% for ty, cls in params['classes'].items():
<%
    mem_s   = []
    con_s   = []
    prand_s = []
    fjson_s = []
    tjson_s = []
    prnt_s  = []
    for mem in cls['members']:
        n = mem['name']
        r = f"rand " if mem['isRand'] else ""
        w = f" [{mem['width']}-1:0]" if mem['width'] is not None else ""
        m = f"{r}{mem['type']}{w} m_{n}"
        if mem['type_cat'] in ("oneof", "oneof_array"):
            e = f", {mem['oneOfBase']}"
        elif mem['isEnum']:
            e = f", {mem['type']}"
        else:
            e = ""

        if mem.get('isRequired'):
            fjson_s.append(
                f'if (jv.getByKey("{n}") == null) '
                f'`uvm_error(get_full_name(), "required field \\"{n}\\" missing from input")'
            )
        if mem['type_cat'] == 'enum_int':
            fjson_s.append(f"`from_json_int({n})")
            tjson_s.append(f"`to_json_int({n})")
            vals = ', '.join(str(v) for v in mem['enumIntValues'])
            fjson_s.append(
                f'if (! (m_{n} inside {{ {vals} }})) '
                f'`uvm_error(get_full_name(), $sformatf("\'{n}\' value %0d not in enum", m_{n}))'
            )
        elif mem['type_cat'] == 'enum_int_array':
            fjson_s.append(f"`from_json_int_array({n})")
            tjson_s.append(f"`to_json_int_array({n})")
            vals = ', '.join(str(v) for v in mem['enumIntValues'])
            fjson_s.append(
                f"foreach (m_{n}[_i]) "
                f"if (! (m_{n}[_i] inside {{ {vals} }})) "
                f'`uvm_error(get_full_name(), $sformatf("\'{n}\' element %0d not in enum", m_{n}[_i]))'
            )
        else:
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
            elif mem['type_cat'] in ("int_array", "enum_int_array"):
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
            elif mem['type_cat'] == "binary_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                printer.print_field_int("{n}", m_{n}[i], {mem['width']}, UVM_BIN);
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
            elif mem['type_cat'] == "oneof_array":
                prnt_s.append(f"""\
            foreach (m_{n}[i]) begin
                if (m_{n}[i] != null) printer.print_object("{n}", m_{n}[i]);
            end""")

            xi = "" if mem['minItems'] is None else f"m_{n}.size >= {mem['minItems']}; "
            ni = "" if mem['maxItems'] is None else f"m_{n}.size <= {mem['maxItems']}; "

            mem_s.append(f"{m}[];")

            if xi or ni:
                con_s.append(f"constraint {n}_size_c {{ {ni}{xi}}};")

            if mem['rangeConstraints']:
                con_s.append(
                    f"constraint {n}_range_c {{ {'; '.join(mem['rangeConstraints'])}; }};"
                )
            if mem.get('uniqueItems'):
                con_s.append(f"constraint {n}_unique_c {{ unique {{ m_{n} }}; }};")
            if mem['type_cat'] == 'enum_int_array':
                vals = ', '.join(str(v) for v in mem['enumIntValues'])
                con_s.append(
                    f"constraint {n}_enum_c {{ foreach (m_{n}[_i]) m_{n}[_i] inside {{ {vals} }}; }};"
                )
        else:
            if mem['type_cat'] == "string":
                prnt_s.append(f"""\
            printer.print_string("{n}", m_{n});""")
            elif mem['type_cat'] == "enum":
                prnt_s.append(f"""\
            printer.print_string("{n}", m_{n}.name);""")
            elif mem['type_cat'] in ("int", "enum_int"):
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
            elif mem['type_cat'] == "binary":
                prnt_s.append(f"""\
            printer.print_field_int("{n}", m_{n}, {mem['width']}, UVM_BIN);""")
            elif mem['type_cat'] == "object":
                prand_s.append(f"""\
            m_{n} = new("{n}");
            void'(m_{n}.randomize());""")
                prnt_s.append(f"""\
            printer.print_object("{n}", m_{n});""")
            elif mem['type_cat'] == "oneof":
                prnt_s.append(f"""\
            if (m_{n} != null) printer.print_object("{n}", m_{n});""")

            if mem['def']:
                mem_s.append(f"{m} = {mem['def']};")
            else:
                mem_s.append(f"{m};")

            if mem['rangeConstraints']:
                con_s.append(
                    f"constraint {n}_range_c {{ {'; '.join(mem['rangeConstraints'])}; }};"
                )
            if mem['type_cat'] == 'enum_int':
                vals = ', '.join(str(v) for v in mem['enumIntValues'])
                con_s.append(
                    f"constraint {n}_enum_c {{ m_{n} inside {{ {vals} }}; }};"
                )

    if cls.get('strict'):
        allowed_names = ", ".join(f'"{m["name"]}"' for m in cls['members'])
        fjson_s.append(f"""\
begin
                ObjectVal_ _obj_jv;
                string _allowed[] = {{ {allowed_names} }};
                if ($cast(_obj_jv, jv)) begin
                    for (int _i = 0; _i < _obj_jv.size(); _i++) begin
                        string _k = _obj_jv.keyAt(_i);
                        bit _ok = 0;
                        foreach (_allowed[_a]) if (_k == _allowed[_a]) _ok = 1;
                        if (!_ok)
                            `uvm_error(get_full_name(), $sformatf("unexpected property '%s' (additionalProperties: false)", _k))
                    end
                end
            end""")

    mems   = '\n        '.join(mem_s)
    cons   = '\n        '.join(con_s)
    prands = '\n'.join(prand_s)
    tjsons = '\n            '.join(tjson_s)
    fjsons = '\n            '.join(fjson_s)
    prnts  = '\n'.join(prnt_s)
%>\
    class ${ty} extends ${cls['extends']};
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
        virtual function void fromJSON(Val_ jv);
            ${fjsons}
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            ${tjsons}
            return jv;
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

