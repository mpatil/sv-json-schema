// Macros mapping schema-generated members to/from sv-embed-json's Val_ tree.
//
// Read side (`from_json_*`): expects local variable `jv` of type `Val_` (an
// object). Skips the field silently if the key is missing or the type is
// unexpected, matching the prior JSONinSV-based behaviour.
//
// Write side (`to_json_*`): expects local variable `jv` of type `ObjectVal_`
// already constructed by the caller. Each macro appends one key.

`define from_json_enum(VAR, TYPE) \
      if (jv.getByKey(`"VAR`") != null) begin \
        string s_ = jv.getByKey(`"VAR`").asString(); \
        void'(TYPE``_wrapper::from_name(s_, m_``VAR)); \
        if (m_``VAR``.name() != s_) \
          $error($sformatf(`"Simulator Error: enum variable VAR of TYPE Error; from_name: %s name: %s`", m_``VAR``.name(), s_)); \
      end else \
        $error(`"enum VAR of TYPE Error`");

`define from_json_enum_array(VAR, TYPE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) begin \
          string s_ = _arr_``VAR``.getByIndex(i).asString(); \
          void'(TYPE``_wrapper::from_name(s_, m_``VAR``[i])); \
          if (m_``VAR``[i].name() != s_) \
            $error($sformatf(`"Simulator Error: enum variable array VAR of TYPE Error; from_name: %s name: %s`", m_``VAR``[i].name(), s_)); \
        end \
      end

`define from_json_string(VAR) \
      if (jv.getByKey(`"VAR`") != null) \
        m_``VAR = jv.getByKey(`"VAR`").asString();

`define from_json_string_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          m_``VAR``[i] = _arr_``VAR``.getByIndex(i).asString(); \
      end

`define from_json_hex(VAR) \
      if (jv.getByKey(`"VAR`") != null) \
        void'($sscanf(jv.getByKey(`"VAR`").asString(), "0x%h", m_``VAR));

`define from_json_hex_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          void'($sscanf(_arr_``VAR``.getByIndex(i).asString(), "0x%h", m_``VAR``[i])); \
      end

`define from_json_binary(VAR) \
      if (jv.getByKey(`"VAR`") != null) \
        void'($sscanf(jv.getByKey(`"VAR`").asString(), "0b%b", m_``VAR));

`define from_json_binary_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          void'($sscanf(_arr_``VAR``.getByIndex(i).asString(), "0b%b", m_``VAR``[i])); \
      end

`define from_json_bool(VAR) \
      if (jv.getByKey(`"VAR`") != null) \
        m_``VAR = jv.getByKey(`"VAR`").isTrue();

`define from_json_bool_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          m_``VAR``[i] = _arr_``VAR``.getByIndex(i).isTrue(); \
      end

`define from_json_int(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isNumber()) \
        m_``VAR = jv.getByKey(`"VAR`").asInt();

`define from_json_int_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          m_``VAR``[i] = _arr_``VAR``.getByIndex(i).asInt(); \
      end

`define from_json_object(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isObject()) begin \
        if (null == m_``VAR) \
          m_``VAR = new("", this); \
        m_``VAR``.fromJSON(jv.getByKey(`"VAR`")); \
      end

`define from_json_object_array(VAR) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) begin \
          m_``VAR``[i] = new("", this); \
          m_``VAR``[i].fromJSON(_arr_``VAR``.getByIndex(i)); \
        end \
      end

`define from_json_object_sub(VAR, TYPE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isObject()) begin \
        TYPE _t_``VAR = new("", this, m__root); \
        _t_``VAR``.fromJSON(jv.getByKey(`"VAR`")); \
        m_``VAR = _t_``VAR; \
      end

`define from_json_object_array_sub(VAR, TYPE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) begin \
          TYPE _t_``VAR = new("", this, m__root); \
          _t_``VAR.fromJSON(_arr_``VAR``.getByIndex(i)); \
          m_``VAR``[i] = _t_``VAR; \
        end \
      end

`define from_json_object_sub_ext(VAR, TYPE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isObject()) begin \
        TYPE _t_``VAR = new(""); \
        _t_``VAR``.fromJSON(jv.getByKey(`"VAR`")); \
        m_``VAR = _t_``VAR; \
      end

`define from_json_oneof(VAR, BASE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isObject()) \
        m_``VAR = BASE``::fromJSONFactory(jv.getByKey(`"VAR`"));

`define from_json_oneof_array(VAR, BASE) \
      if (jv.getByKey(`"VAR`") != null && jv.getByKey(`"VAR`").isArray()) begin \
        Val_ _arr_``VAR = jv.getByKey(`"VAR`"); \
        if (_arr_``VAR``.size() > m_``VAR``.size) \
          m_``VAR = new [_arr_``VAR``.size()] (m_``VAR); \
        for (int i = 0; i < _arr_``VAR``.size(); i++) \
          m_``VAR``[i] = BASE``::fromJSONFactory(_arr_``VAR``.getByIndex(i)); \
      end

`define to_json_enum(VAR) \
      jv.append(`"VAR`", _mkStr(m_``VAR``.name()));

`define to_json_enum_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          _arr_``VAR``.append(_mkStr(m_``VAR``[i].name())); \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_string(VAR) \
      jv.append(`"VAR`", _mkStr(m_``VAR``));

`define to_json_string_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          _arr_``VAR``.append(_mkStr(m_``VAR``[i])); \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_hex(VAR) \
      begin \
        string s_``VAR; \
        s_``VAR``.hextoa(m_``VAR); \
        jv.append(`"VAR`", _mkStr({"0x", s_``VAR})); \
      end

`define to_json_hex_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) begin \
          string s_``VAR; \
          s_``VAR``.hextoa(m_``VAR``[i]); \
          _arr_``VAR``.append(_mkStr({"0x", s_``VAR})); \
        end \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_binary(VAR) \
      begin \
        string s_``VAR; \
        s_``VAR``.bintoa(m_``VAR); \
        jv.append(`"VAR`", _mkStr({"0b", s_``VAR})); \
      end

`define to_json_binary_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) begin \
          string s_``VAR; \
          s_``VAR``.bintoa(m_``VAR``[i]); \
          _arr_``VAR``.append(_mkStr({"0b", s_``VAR})); \
        end \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_bool(VAR) \
      jv.append(`"VAR`", _mkBool(m_``VAR``));

`define to_json_bool_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          _arr_``VAR``.append(_mkBool(m_``VAR``[i])); \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_int(VAR) \
      jv.append(`"VAR`", _mkInt(m_``VAR``));

`define to_json_int_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          _arr_``VAR``.append(_mkInt(m_``VAR``[i])); \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_object(VAR) \
      jv.append(`"VAR`", m_``VAR``.toJSON());

`define to_json_object_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          _arr_``VAR``.append(m_``VAR``[i].toJSON()); \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_object_sub(VAR, TYPE) \
      begin \
        TYPE _t_``VAR; \
        $cast(_t_``VAR, m_``VAR``); \
        jv.append(`"VAR`", _t_``VAR``.toJSON()); \
      end

`define to_json_object_array_sub(VAR, TYPE) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) begin \
          TYPE _t_``VAR; \
          $cast(_t_``VAR, m_``VAR``[i]); \
          _arr_``VAR``.append(_t_``VAR``.toJSON()); \
        end \
        jv.append(`"VAR`", _arr_``VAR); \
      end

`define to_json_oneof(VAR) \
      if (m_``VAR != null) jv.append(`"VAR`", m_``VAR``.toJSON());

`define to_json_oneof_array(VAR) \
      begin \
        ArrayVal_ _arr_``VAR = new(); \
        foreach (m_``VAR``[i]) \
          if (m_``VAR``[i] != null) \
            _arr_``VAR``.append(m_``VAR``[i].toJSON()); \
        jv.append(`"VAR`", _arr_``VAR); \
      end
