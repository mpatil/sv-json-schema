class config_m extends uvm_object;
    `uvm_object_utils(config_m)

    typedef enum {
        red,
        green,
        blue
    } Cfg_color_e;
    typedef uvm_enum_wrapper#(Cfg_color_e) Cfg_color_e_wrapper;

    typedef enum {
        a,
        b
    } Cfg_tags_e;
    typedef uvm_enum_wrapper#(Cfg_tags_e) Cfg_tags_e_wrapper;


    typedef class Cfg;


    class Cfg extends uvm_object;
        `uvm_object_utils(Cfg)

        rand Cfg_color_e m_color = red;
        rand int m_level;
        rand Cfg_tags_e m_tags[];
        rand int m_vals[];

        protected Cfg m__root;
        protected uvm_object m__parent;

        constraint level_enum_c { m_level inside { 0, 1, 5 }; };
        constraint tags_size_c { m_tags.size <= 3; m_tags.size >= 1; };
        constraint vals_size_c { m_vals.size <= 3; m_vals.size >= 1; };
        constraint vals_enum_c { foreach (m_vals[_i]) m_vals[_i] inside { 1, 2, 3 }; };

        function new (string name ="", input uvm_object p__parent = null, input Cfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("color") == null) `uvm_error(get_full_name(), "required field \"color\" missing from input")
            `from_json_enum(color, Cfg_color_e)
            if (jv.getByKey("level") == null) `uvm_error(get_full_name(), "required field \"level\" missing from input")
            `from_json_int(level)
            if (! (m_level inside { 0, 1, 5 })) `uvm_error(get_full_name(), $sformatf("'level' value %0d not in enum", m_level))
            `from_json_enum_array(tags, Cfg_tags_e)
            `from_json_int_array(vals)
            foreach (m_vals[_i]) if (! (m_vals[_i] inside { 1, 2, 3 })) `uvm_error(get_full_name(), $sformatf("'vals' element %0d not in enum", m_vals[_i]))
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_enum(color)
            `to_json_int(level)
            `to_json_enum_array(tags)
            `to_json_int_array(vals)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("color", m_color.name);
                printer.print_field_int("level", m_level, 32, UVM_DEC);
            foreach (m_tags[i]) begin
                printer.print_string("tags", m_tags[i].name);
            end
            foreach (m_vals[i]) begin
                printer.print_field_int("vals", m_vals[i], 32, UVM_DEC);
            end
        endfunction : do_print

    endclass

    Cfg m_Cfg;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

