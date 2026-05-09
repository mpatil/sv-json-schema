class config_m extends uvm_object;
    `uvm_object_utils(config_m)


    typedef class Identifiable;
    typedef class Cfg;


    // Generic id/name mixin.
    class Identifiable extends uvm_object;
        `uvm_object_utils(Identifiable)

        rand int m_id = 0;
        string m_name = "";

        protected Identifiable m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Identifiable p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("id") == null) `uvm_error(get_full_name(), "required field \"id\" missing from input")
            `from_json_int(m_id, id)
            `from_json_string(m_name, name)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(m_id, id)
            `to_json_string(m_name, name)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("id", m_id, 32, UVM_DEC);
            printer.print_string("name", m_name);
        endfunction : do_print

    endclass

    class Cfg extends uvm_object;
        `uvm_object_utils(Cfg)

        rand int m_awuser;
        rand int m_id = 0;
        string m_name = "";

        protected Cfg m__root;
        protected uvm_object m__parent;

        constraint awuser_range_c { m_awuser >= 0; m_awuser <= 15; };

        function new (string name ="", input uvm_object p__parent = null, input Cfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("awuser") == null) `uvm_error(get_full_name(), "required field \"awuser\" missing from input")
            `from_json_int(m_awuser, awuser)
            if (jv.getByKey("id") == null) `uvm_error(get_full_name(), "required field \"id\" missing from input")
            `from_json_int(m_id, id)
            `from_json_string(m_name, name)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(m_awuser, awuser)
            `to_json_int(m_id, id)
            `to_json_string(m_name, name)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("awuser", m_awuser, 32, UVM_DEC);
                printer.print_field_int("id", m_id, 32, UVM_DEC);
            printer.print_string("name", m_name);
        endfunction : do_print

    endclass

    Identifiable m_Identifiable;
    Cfg m_Cfg;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

