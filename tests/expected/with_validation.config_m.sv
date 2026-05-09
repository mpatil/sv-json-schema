class config_m extends uvm_object;
    `uvm_object_utils(config_m)


    typedef class Cfg;


    // Configuration with validation constraints.
    class Cfg extends uvm_object;
        `uvm_object_utils(Cfg)

        // Display name (3 to 8 chars).
        string m_name;
        string m_tag = "v1";
        rand int m_version = 1;

        protected Cfg m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Cfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            `from_json_string(name)
            if (m_name.len() < 3) `uvm_error(get_full_name(), $sformatf("'name' length %0d below minLength 3", m_name.len()))
            if (m_name.len() > 8) `uvm_error(get_full_name(), $sformatf("'name' length %0d above maxLength 8", m_name.len()))
            `from_json_string(tag)
            if (m_tag != "v1") `uvm_error(get_full_name(), $sformatf("'tag' must equal const %s, got '%s'", "v1", m_tag))
            `from_json_int(version)
            if (m_version != 1) `uvm_error(get_full_name(), $sformatf("'version' must equal const 1, got %0d", m_version))
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_string(name)
            `to_json_string(tag)
            `to_json_int(version)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("name", m_name);
            printer.print_string("tag", m_tag);
                printer.print_field_int("version", m_version, 32, UVM_DEC);
        endfunction : do_print

    endclass

    Cfg m_Cfg;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

