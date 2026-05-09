class config_m extends uvm_object;
    `uvm_object_utils(config_m)


    typedef class Tree;


    // Recursive node carrying an integer value plus children.
    class Tree extends uvm_object;
        `uvm_object_utils(Tree)

        rand int m_value = 0;
        Tree m_children[];

        protected Tree m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Tree p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("value") == null) `uvm_error(get_full_name(), "required field \"value\" missing from input")
            `from_json_int(m_value, value)
            `from_json_object_array(m_children, children)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(m_value, value)
            `to_json_object_array(m_children, children)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("value", m_value, 32, UVM_DEC);
            foreach (m_children[i]) begin
                printer.print_object("children", m_children[i]);
            end
        endfunction : do_print

    endclass

    Tree m_Tree;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

