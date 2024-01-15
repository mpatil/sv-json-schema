`define from_json_enum(VAR, TYPE) \
      if (JSONValue::JSON_STRING == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        string s_ = jv.getObjectMember(`"VAR`").getString(); \
        void'(TYPE``_wrapper::from_name(s_, m_``VAR)); \
        if (m_``VAR``.name() != s_) \
          $error($sformatf(`"Simulator Error: enum variable VAR of TYPE Error; from_name: %s name: %s`", m_``VAR``.name(), s_)); \
      end  \
      else \
      begin \
        $error(`"enum VAR of TYPE Error`"); \
      end
`define from_json_enum_array(VAR, TYPE) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          void'(TYPE``_wrapper::from_name(jv.getObjectMember(`"VAR`").getArrayElement(i).getString(), m_``VAR``[i]));  \
          if (m_``VAR``[i].name() != jv.getObjectMember(`"VAR`").getArrayElement(i).getString()) \
            $error($sformatf(`"Simulator Error: enum variable array VAR of TYPE Error; from_name: %s name: %s`", m_``VAR``[i].name(), jv.getObjectMember(`"VAR`").getArrayElement(i).getString())); \
        end \
      end
`define from_json_string(VAR) \
      if (JSONValue::JSON_STRING == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        m_``VAR = jv.getObjectMember(`"VAR`").getString();  \
      end
`define from_json_string_array(VAR) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          m_``VAR``[i] = jv.getObjectMember(`"VAR`").getArrayElement(i).getString();  \
        end \
      end
`define from_json_hex(VAR) \
      if (JSONValue::JSON_STRING == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        void'($sscanf(jv.getObjectMember(`"VAR`").getString(), "0x%h", m_``VAR)); \
      end
`define from_json_hex_array(VAR) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          void'($sscanf(jv.getObjectMember(`"VAR`").getArrayElement(i).getString(), "0x%h", m_``VAR[i])); \
        end \
      end
`define from_json_bool(VAR) \
      case(jv.getObjectMember(`"VAR`").getType()) \
          JSONValue::JSON_TRUE: m_``VAR = 1;  \
          JSONValue::JSON_FALSE: m_``VAR = 0;  \
          default: $error($sformatf(`"Simulator Error: boolean  variable VAR`")); \
      endcase
`define from_json_bool_array(VAR) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          case(jv.getObjectMember(`"VAR`").getArrayElement(i).getType()) \
              JSONValue::JSON_TRUE: m_``VAR``[i] = 1;  \
              JSONValue::JSON_FALSE: m_``VAR``[i] = 0;  \
              default: $error($sformatf(`"Simulator Error: boolean  variable VAR`")); \
          endcase \
        end \
      end
`define from_json_int(VAR) \
      if (JSONValue::JSON_NUMBER == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        m_``VAR = jv.getObjectMember(`"VAR`").getNumber();  \
      end
`define from_json_int_array(VAR) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          m_``VAR``[i] = jv.getObjectMember(`"VAR`").getArrayElement(i).getNumber();  \
        end \
      end
`define from_json_object(VAR) \
      if (JSONValue::JSON_OBJECT == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (null ==  m_``VAR) \
          m_``VAR = new("", this); \
        m_``VAR``.fromJSON(jv.getObjectMember(`"VAR`"));  \
      end
`define from_json_object_array(VAR) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          m_``VAR``[i] = new("", this); \
          m_``VAR``[i].fromJSON(jv.getObjectMember(`"VAR`").getArrayElement(i));  \
        end \
      end
`define from_json_object_sub(VAR, TYPE) \
      if (JSONValue::JSON_OBJECT == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        TYPE _t_``VAR = new("", this, m__root); \
        _t_``VAR``.fromJSON(jv.getObjectMember(`"VAR`"));  \
        m_``VAR = _t_``VAR; \
      end
`define from_json_object_array_sub(VAR, TYPE) \
      if (JSONValue::JSON_ARRAY == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        if (jv.getObjectMember(`"VAR`").getArraySize() >  m_``VAR``.size) \
          m_``VAR = new [jv.getObjectMember(`"VAR`").getArraySize()] (m_``VAR); \
        for (int i = 0; i < jv.getObjectMember(`"VAR`").getArraySize(); i++) begin \
          TYPE _t_``VAR = new("", this, m__root); \
          _t_``VAR.fromJSON(jv.getObjectMember(`"VAR`").getArrayElement(i));  \
          m_``VAR``[i] = _t_``VAR; \
        end \
      end
`define to_json_enum(VAR) \
      begin \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_STRING); \
        _jv_``VAR.setString(m_``VAR``.name()); \
      end
`define to_json_enum_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_NUMBER); \
          _jv_``VAR.setString(m_``VAR``[i].name()); \
        end \
      end
`define to_json_string(VAR) \
      begin \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_STRING); \
        _jv_``VAR.setString(m_``VAR); \
      end
`define to_json_string_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_STRING); \
          _jv_``VAR.setString(m_``VAR``[i]); \
        end \
      end
`define to_json_hex(VAR) \
      begin \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_STRING); \
        string s_``VAR; \
        s_``VAR.hextoa(m_``VAR); \
        _jv_``VAR.setString({"0x", s_``VAR}); \
      end
`define to_json_hex_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          string s_``VAR; \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_STRING); \
          s_``VAR.hextoa(m_``VAR[i]); \
          _jv_``VAR.setString({"0x", s_``VAR``}); \
        end \
      end
`define to_json_bool(VAR) \
      case(m_``VAR) \
          1: void'(jv.createMemberOfObject(`"VAR`", JSONValue::JSON_TRUE)); \
          0: void'(jv.createMemberOfObject(`"VAR`", JSONValue::JSON_FALSE)); \
          default: $error($sformatf(`"Simulator Error: boolean  variable VAR`")); \
      endcase
`define to_json_bool_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          case(m_``VAR``[i]) \
              1: void'(_jva_``VAR.createValueOfArray(JSONValue::JSON_TRUE)); \
              0: void'(_jva_``VAR.createValueOfArray(JSONValue::JSON_FALSE)); \
              default: $error($sformatf(`"Simulator Error: boolean  variable VAR`")); \
          endcase \
        end \
      end
`define to_json_int(VAR) \
      begin \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_NUMBER); \
        _jv_``VAR.setNumber(m_``VAR); \
      end
`define to_json_int_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_NUMBER); \
          _jv_``VAR.setNumber(m_``VAR``[i]); \
        end \
      end
`define to_json_object(VAR) \
      begin \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_OBJECT); \
        m_``VAR``.toJSON(_jv_``VAR); \
      end
`define to_json_object_array(VAR) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_OBJECT); \
          m_``VAR``[i].toJSON(_jv_``VAR); \
        end \
      end
`define to_json_object_sub(VAR, TYPE) \
      begin \
        TYPE _t_``VAR; \
        JSONValue _jv_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_OBJECT); \
        $cast(_t_``VAR, m_``VAR``);  \
        _t_``VAR``.toJSON(_jv_``VAR); \
      end
`define to_json_object_array_sub(VAR, TYPE) \
      begin \
        JSONValue _jva_``VAR = jv.createMemberOfObject(`"VAR`", JSONValue::JSON_ARRAY); \
        foreach(m_``VAR``[i]) begin \
          TYPE _t_``VAR;  \
          JSONValue _jv_``VAR = _jva_``VAR.createValueOfArray(JSONValue::JSON_OBJECT); \
          $cast(_t_``VAR, m_``VAR``[i]);  \
          _t_``VAR.toJSON(_jv_``VAR); \
        end \
      end
`define from_json_object_sub_ext(VAR, TYPE) \
      if (JSONValue::JSON_OBJECT == jv.getObjectMember(`"VAR`").getType()) \
      begin \
        TYPE _t_``VAR = new("" ); \
        _t_``VAR``.fromJSON(jv.getObjectMember(`"VAR`"));  \
        m_``VAR = _t_``VAR; \
      end
