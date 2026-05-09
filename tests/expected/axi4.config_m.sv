class config_m extends uvm_object;
    `uvm_object_utils(config_m)

    typedef enum {
        NORMAL=0,
        STRIPE
    } AddrMapKind;
    typedef uvm_enum_wrapper#(AddrMapKind) AddrMapKind_wrapper;

    typedef enum {
        UNK=0,
        NS=1,
        SI=2,
        SO=3,
        SS=-1
    } AddrMapDomain;
    typedef uvm_enum_wrapper#(AddrMapDomain) AddrMapDomain_wrapper;

    typedef enum {
        MEM_NORMAL=0,
        MEM_DEVICE=1
    } AddrMapMem;
    typedef uvm_enum_wrapper#(AddrMapMem) AddrMapMem_wrapper;


    typedef class AddrMap;
    typedef class Cfg;
    typedef class MasterCfg;
    typedef class SlaveCfg;

    class AddrMap extends uvm_object;
        `uvm_object_utils(AddrMap)

        rand AddrMapKind m_kind = NORMAL;
        string m_name = "addr_map";
        rand int m_id = 0;
        rand AddrMapMem m_domain;
        rand logic [32-1:0] m_region = 'h0;
        rand logic [32-1:0] m_addr = 'h0;
        rand int m_size;
        rand logic [4-1:0] m_mode = 'b0000;

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
            `from_json_enum(kind, AddrMapKind)
            `from_json_string(name)
            `from_json_int(id)
            `from_json_enum(domain, AddrMapMem)
            `from_json_hex(region)
            if (jv.getByKey("addr") == null) `uvm_error(get_full_name(), "required field \"addr\" missing from input")
            `from_json_hex(addr)
            if (jv.getByKey("size") == null) `uvm_error(get_full_name(), "required field \"size\" missing from input")
            `from_json_int(size)
            `from_json_binary(mode)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_enum(kind)
            `to_json_string(name)
            `to_json_int(id)
            `to_json_enum(domain)
            `to_json_hex(region)
            `to_json_hex(addr)
            `to_json_int(size)
            `to_json_binary(mode)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_string("kind", m_kind.name);
            printer.print_string("name", m_name);
                printer.print_field_int("id", m_id, 32, UVM_DEC);
            printer.print_string("domain", m_domain.name);
            printer.print_field_int("region", m_region, 32, UVM_HEX);
            printer.print_field_int("addr", m_addr, 32, UVM_HEX);
                printer.print_field_int("size", m_size, 32, UVM_DEC);
            printer.print_field_int("mode", m_mode, 4, UVM_BIN);
        endfunction : do_print

    endclass

    class Cfg extends uvm_object;
        `uvm_object_utils(Cfg)

        rand bit m_is_active = 0;
        rand bit m_en_ext_clock = 1;
        string m_txn_log_filelname = "txn%0d.log";
        rand AddrMap m_addr_map;
        rand int m_awuser_width;

        protected Cfg m__root;
        protected uvm_object m__parent;

        

        function new (string name ="", input uvm_object p__parent = null, input Cfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();
            m_addr_map = new("addr_map");
            void'(m_addr_map.randomize());
        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            `from_json_bool(is_active)
            `from_json_bool(en_ext_clock)
            `from_json_string(txn_log_filelname)
            `from_json_object(addr_map)
            `from_json_int(awuser_width)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_bool(is_active)
            `to_json_bool(en_ext_clock)
            `to_json_string(txn_log_filelname)
            `to_json_object(addr_map)
            `to_json_int(awuser_width)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            printer.print_field_int("is_active", m_is_active, 1, UVM_BIN);
            printer.print_field_int("en_ext_clock", m_en_ext_clock, 1, UVM_BIN);
            printer.print_string("txn_log_filelname", m_txn_log_filelname);
            printer.print_object("addr_map", m_addr_map);
                printer.print_field_int("awuser_width", m_awuser_width, 32, UVM_DEC);
        endfunction : do_print

    endclass

    class MasterCfg extends uvm_object;
        `uvm_object_utils(MasterCfg)

        rand Cfg m_cfg[];

        protected MasterCfg m__root;
        protected uvm_object m__parent;

        constraint cfg_size_c { m_cfg.size <= 4; m_cfg.size >= 1; };

        function new (string name ="", input uvm_object p__parent = null, input MasterCfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();
            foreach (m_cfg[i]) begin
                m_cfg[i] = new($sformatf("cfg[%0d]", i));
                void'(m_cfg[i].randomize());
            end
        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            `from_json_object_array(cfg)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_object_array(cfg)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            foreach (m_cfg[i]) begin
                printer.print_object("cfg", m_cfg[i]);
            end
        endfunction : do_print

    endclass

    class SlaveCfg extends uvm_object;
        `uvm_object_utils(SlaveCfg)

        rand Cfg m_cfg[];

        protected SlaveCfg m__root;
        protected uvm_object m__parent;

        constraint cfg_size_c { m_cfg.size <= 2; m_cfg.size >= 0; };

        function new (string name ="", input uvm_object p__parent = null, input SlaveCfg p__root = null);
            super.new(name);

            m__parent = p__parent;
            m__root = this;
        endfunction : new

        function void post_randomize();
            foreach (m_cfg[i]) begin
                m_cfg[i] = new($sformatf("cfg[%0d]", i));
                void'(m_cfg[i].randomize());
            end
        endfunction : post_randomize

`ifdef JSON_PKG
        virtual function void fromJSON(Val_ jv);
            `from_json_object_array(cfg)
        endfunction : fromJSON
`endif

`ifdef JSON_PKG
        virtual function ObjectVal_ toJSON();
            ObjectVal_ jv = new();
            `to_json_object_array(cfg)
            return jv;
        endfunction : toJSON
`endif

        virtual function void do_print(uvm_printer printer);
            foreach (m_cfg[i]) begin
                printer.print_object("cfg", m_cfg[i]);
            end
        endfunction : do_print

    endclass

    AddrMap m_AddrMap;
    Cfg m_Cfg;
    MasterCfg m_MasterCfg;
    SlaveCfg m_SlaveCfg;

    function new (string name ="");
      super.new(name);
    endfunction : new
endclass

