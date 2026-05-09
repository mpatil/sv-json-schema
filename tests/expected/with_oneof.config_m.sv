class config_m extends uvm_object;
    `uvm_object_utils(config_m)


    typedef class AnyMap;
    typedef class AddrMap;
    typedef class RegMap;
    typedef class Cfg;

    class AnyMap extends uvm_object;
        `uvm_object_utils(AnyMap)

        function new (string name ="");
            super.new(name);
        endfunction : new

`ifdef JSON_PKG
        static function AnyMap fromJSONFactory(Val_ jv);
            string disc;
            AnyMap result = null;
            if (jv == null) return null;
            if (jv.getByKey("kind") == null) begin
              `uvm_error("AnyMap", "discriminator field \"kind\" missing from input")
              return null;
            end
            disc = jv.getByKey("kind").asString();
            case (disc)
              "addr": begin AddrMap _t = new(""); _t.fromJSON(jv); result = _t; end
              "reg": begin RegMap _t = new(""); _t.fromJSON(jv); result = _t; end
              default: `uvm_error("AnyMap", $sformatf("unknown kind: %s", disc))
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


    class AddrMap extends AnyMap;
        `uvm_object_utils(AddrMap)

        string m_kind = "addr";
        rand int m_size = 0;
        rand logic [32-1:0] m_region = 'h0;

        protected AddrMap m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input AddrMap p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("kind") == null) `uvm_error(get_full_name(), "required field \"kind\" missing from input")
            `from_json_string(m_kind, kind)
            if (jv.getByKey("size") == null) `uvm_error(get_full_name(), "required field \"size\" missing from input")
            `from_json_int(m_size, size)
            `from_json_hex(m_region, region)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_string(m_kind, kind)
            `to_json_int(m_size, size)
            `to_json_hex(m_region, region)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("kind", m_kind);
                printer.print_field_int("size", m_size, 32, UVM_DEC);
            printer.print_field_int("region", m_region, 32, UVM_HEX);
        endfunction : do_print

    endclass

    class RegMap extends AnyMap;
        `uvm_object_utils(RegMap)

        string m_kind = "reg";
        rand int m_offset = 0;

        protected RegMap m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input RegMap p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();

        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            if (jv.getByKey("kind") == null) `uvm_error(get_full_name(), "required field \"kind\" missing from input")
            `from_json_string(m_kind, kind)
            if (jv.getByKey("offset") == null) `uvm_error(get_full_name(), "required field \"offset\" missing from input")
            `from_json_int(m_offset, offset)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_string(m_kind, kind)
            `to_json_int(m_offset, offset)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("kind", m_kind);
                printer.print_field_int("offset", m_offset, 32, UVM_DEC);
        endfunction : do_print

    endclass

    class Cfg extends uvm_object;
        `uvm_object_utils(Cfg)

        string m_name = "cfg";
        AnyMap m_map;

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
            `from_json_string(m_name, name)
            if (jv.getByKey("map") == null) `uvm_error(get_full_name(), "required field \"map\" missing from input")
            `from_json_oneof(m_map, map, AnyMap)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_string(m_name, name)
            `to_json_oneof(m_map, map)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("name", m_name);
            if (m_map != null) printer.print_object("map", m_map);
        endfunction : do_print

    endclass

    AddrMap m_AddrMap;
    RegMap m_RegMap;
    Cfg m_Cfg;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

