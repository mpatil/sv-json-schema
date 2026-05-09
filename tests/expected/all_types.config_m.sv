class config_m extends uvm_object;
    `uvm_object_utils(config_m)

    typedef enum {
        M_OFF=0,
        M_ON=1
    } Mode;
    typedef uvm_enum_wrapper#(Mode) Mode_wrapper;


    typedef class Inner;
    typedef class AllTypes;


    class Inner extends uvm_object;
        `uvm_object_utils(Inner)

        string m_tag = "tag0";
        rand int m_n = 0;

        protected Inner m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Inner p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("tag") == null) `uvm_error(get_full_name(), "required field \"tag\" missing from input")
            `from_json_string(tag)
            `from_json_int(n)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_string(tag)
            `to_json_int(n)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("tag", m_tag);
                printer.print_field_int("n", m_n, 32, UVM_DEC);
        endfunction : do_print

    endclass

    class AllTypes extends uvm_object;
        `uvm_object_utils(AllTypes)

        rand int m_i = 0;
        rand longint m_i64;
        rand longint m_i64_arr[];
        rand int m_i_excl;
        rand int m_i_mult;
        rand int m_uniq_arr[];
        rand int m_i_arr[];
        rand bit m_b = 0;
        rand bit m_b_arr[];
        string m_s = "default";
        string m_s_arr[];
        rand logic [16-1:0] m_h = 'h0;
        rand logic [8-1:0] m_h_arr[];
        rand logic [4-1:0] m_bn = 'b0000;
        rand logic [2-1:0] m_bn_arr[];
        rand Mode m_e;
        rand Inner m_obj;
        rand Inner m_obj_arr[];

        protected AllTypes m__root;
        protected uvm_object m__parent;

        constraint i64_arr_size_c { m_i64_arr.size <= 2; m_i64_arr.size >= 1; };
        constraint i_excl_range_c { m_i_excl > 0; m_i_excl < 100; };
        constraint i_mult_range_c { m_i_mult % 4 == 0; };
        constraint uniq_arr_size_c { m_uniq_arr.size <= 4; m_uniq_arr.size >= 2; };
        constraint uniq_arr_unique_c { unique { m_uniq_arr }; };
        constraint i_arr_size_c { m_i_arr.size <= 4; m_i_arr.size >= 1; };
        constraint b_arr_size_c { m_b_arr.size <= 2; m_b_arr.size >= 1; };
        constraint s_arr_size_c { m_s_arr.size <= 2; m_s_arr.size >= 1; };
        constraint h_arr_size_c { m_h_arr.size <= 2; m_h_arr.size >= 1; };
        constraint bn_arr_size_c { m_bn_arr.size <= 2; m_bn_arr.size >= 1; };
        constraint obj_arr_size_c { m_obj_arr.size <= 2; m_obj_arr.size >= 1; };

        function new (string name ="", input uvm_object p__parent = null, input AllTypes p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();
            m_obj = new("obj");
            void'(m_obj.randomize());
            foreach (m_obj_arr[i]) begin
                m_obj_arr[i] = new($sformatf("obj_arr[%0d]", i));
                void'(m_obj_arr[i].randomize());
            end
        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("i") == null) `uvm_error(get_full_name(), "required field \"i\" missing from input")
            `from_json_int(i)
            `from_json_int(i64)
            `from_json_int_array(i64_arr)
            `from_json_int(i_excl)
            `from_json_int(i_mult)
            `from_json_int_array(uniq_arr)
            `from_json_int_array(i_arr)
            `from_json_bool(b)
            `from_json_bool_array(b_arr)
            `from_json_string(s)
            `from_json_string_array(s_arr)
            if (jv.getByKey("h") == null) `uvm_error(get_full_name(), "required field \"h\" missing from input")
            `from_json_hex(h)
            `from_json_hex_array(h_arr)
            `from_json_binary(bn)
            `from_json_binary_array(bn_arr)
            `from_json_enum(e, Mode)
            if (jv.getByKey("obj") == null) `uvm_error(get_full_name(), "required field \"obj\" missing from input")
            `from_json_object(obj)
            `from_json_object_array(obj_arr)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_int(i)
            `to_json_int(i64)
            `to_json_int_array(i64_arr)
            `to_json_int(i_excl)
            `to_json_int(i_mult)
            `to_json_int_array(uniq_arr)
            `to_json_int_array(i_arr)
            `to_json_bool(b)
            `to_json_bool_array(b_arr)
            `to_json_string(s)
            `to_json_string_array(s_arr)
            `to_json_hex(h)
            `to_json_hex_array(h_arr)
            `to_json_binary(bn)
            `to_json_binary_array(bn_arr)
            `to_json_enum(e)
            `to_json_object(obj)
            `to_json_object_array(obj_arr)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
                printer.print_field_int("i", m_i, 32, UVM_DEC);
                printer.print_field_int("i64", m_i64, 64, UVM_DEC);
            foreach (m_i64_arr[i]) begin
                printer.print_field_int("i64_arr", m_i64_arr[i], 64, UVM_DEC);
            end
                printer.print_field_int("i_excl", m_i_excl, 32, UVM_DEC);
                printer.print_field_int("i_mult", m_i_mult, 32, UVM_DEC);
            foreach (m_uniq_arr[i]) begin
                printer.print_field_int("uniq_arr", m_uniq_arr[i], 32, UVM_DEC);
            end
            foreach (m_i_arr[i]) begin
                printer.print_field_int("i_arr", m_i_arr[i], 32, UVM_DEC);
            end
            printer.print_field_int("b", m_b, 1, UVM_BIN);
            foreach (m_b_arr[i]) begin
                printer.print_field_int("b_arr", m_b_arr[i], 1, UVM_BIN);
            end
            printer.print_string("s", m_s);
            foreach (m_s_arr[i]) begin
                printer.print_string("s_arr", m_s_arr[i]);
            end
            printer.print_field_int("h", m_h, 16, UVM_HEX);
            foreach (m_h_arr[i]) begin
                printer.print_field_int("h_arr", m_h_arr[i], 8, UVM_HEX);
            end
            printer.print_field_int("bn", m_bn, 4, UVM_BIN);
            foreach (m_bn_arr[i]) begin
                printer.print_field_int("bn_arr", m_bn_arr[i], 2, UVM_BIN);
            end
            printer.print_string("e", m_e.name);
            printer.print_object("obj", m_obj);
            foreach (m_obj_arr[i]) begin
                printer.print_object("obj_arr", m_obj_arr[i]);
            end
        endfunction : do_print

    endclass

    Inner m_Inner;
    AllTypes m_AllTypes;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

