class config_m extends uvm_object;
    `uvm_object_utils(config_m)


    typedef class Strict;
    typedef class Loose;


    class Strict extends uvm_object;
        `uvm_object_utils(Strict)

        rand int m_a = 0;
        string m_b = "hello";

        protected Strict m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Strict p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("a") == null) `uvm_error(get_full_name(), "required field \"a\" missing from input")
            `from_json_int(m_a, a)
            `from_json_string(m_b, b)
            begin
                ObjectVal_ _obj_jv;
                string _allowed[] = { "a", "b" };
                if ($cast(_obj_jv, jv)) begin
                    for (int _i = 0; _i < _obj_jv.size(); _i++) begin
                        string _k = _obj_jv.keyAt(_i);
                        bit _ok = 0;
                        foreach (_allowed[_a]) if (_k == _allowed[_a]) _ok = 1;
                        if (!_ok)
                            `uvm_error(get_full_name(), $sformatf("unexpected property '%s' (additionalProperties: false)", _k))
                    end
                end
            end
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(m_a, a)
            `to_json_string(m_b, b)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("a", m_a, 32, UVM_DEC);
            printer.print_string("b", m_b);
        endfunction : do_print

    endclass

    class Loose extends uvm_object;
        `uvm_object_utils(Loose)

        rand int m_x = 0;

        protected Loose m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Loose p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            `from_json_int(m_x, x)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(m_x, x)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("x", m_x, 32, UVM_DEC);
        endfunction : do_print

    endclass

    Strict m_Strict;
    Loose m_Loose;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

