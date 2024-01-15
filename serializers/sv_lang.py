from typing import Set, Type, Union

from statham.schema.elements import (
    AllOf,
    AnyOf,
    Array,
    Boolean,
    CompositionElement,
    Integer,
    Not,
    Nothing,
    Null,
    Number,
    Object,
    OneOf,
    Element,
    String,
)

from statham.schema.constants import Maybe, NotPassed
from statham.schema.elements.meta import ObjectMeta
from statham.serializers.orderer import orderer, get_children

import inspect
from pprint import pprint

def sv_type(typeObj):
    if typeObj is None:
        return '???', False
    if isinstance(typeObj, Integer):
        return 'int', True
    elif isinstance(typeObj, Number):
        return 'real', False
    elif isinstance(typeObj, Boolean):
        return 'bit', True
    elif isinstance(typeObj, String):
        if not isinstance(typeObj.format, NotPassed) and typeObj.format == "hex":
            return 'logic', True
        else:
            return 'string', False
    elif isinstance(typeObj, ObjectMeta):
        return f"{typeObj}", True
    elif isinstance(typeObj, Array):
        return sv_type(typeObj.items)

def sv_width(typeObj):
    width = None
    if isinstance(typeObj, String) and not isinstance(typeObj.format, NotPassed):
          if typeObj.format == "hex":
              width = 32 if isinstance(typeObj.width, NotPassed) else typeObj.width
    elif isinstance(typeObj, Array):
        return sv_width(typeObj.items)
    return width

def json_type(typeObj):
    if typeObj is None:
        return None
    elif isinstance(typeObj, Integer):
        return 'int'
    elif isinstance(typeObj, Number):
        return 'int'
    elif isinstance(typeObj, Boolean):
        return 'bool'
    elif isinstance(typeObj, String):
        if not isinstance(typeObj.format, NotPassed) and typeObj.format == "hex":
            return 'hex'
        else:
            return 'string'
    elif isinstance(typeObj, ObjectMeta):
        if isinstance(typeObj.enum, NotPassed):
            return 'object'
        else:
            return 'enum'
    elif isinstance(typeObj, Array):
        return f"{json_type(typeObj.items)}_array"

def sv_def(typeObj):
    if typeObj is None or isinstance(typeObj.default, NotPassed):
        return None
    ret = typeObj.default
    if isinstance(typeObj, Integer):
        return f"{ret}"
    elif isinstance(typeObj, Number):
        return f"{ret}"
    elif isinstance(typeObj, Boolean):
        return f"{1 if ret else 0}"
    elif isinstance(typeObj, String):
        if not isinstance(typeObj.format, NotPassed):
            if typeObj.format == "hex":
                return f"'h{ret[2:]}"
            else:
                return f"\"{ret}\" /* */"
        return f"\"{ret}\""
    elif isinstance(typeObj, ObjectMeta):
        return f"{ret}"
    elif isinstance(typeObj, Array):
        return sv_def(typeObj.items)
    else:
        return '????'

def serialize_enums(*elements: Element):
    es = {}
    for o in orderer(*elements):
        if not isinstance(o.enum, NotPassed):
            vs = []
            for k, v in o.enum.items():
                if v == None:
                    vs.append(f"{k}")
                else:
                    vs.append(f"{k}={v}")
            es[str(o)] = vs
    return es

def serialize_classes(*elements: Element):
    cs = {}
    for o in orderer(*elements):
        if isinstance(o.enum, NotPassed):
            ms = []
            for p in o.properties:
                elem = o._properties[p].element

                prop = {}
                prop["name"] = p
                prop["type_cat"] = json_type(elem)
                prop['type'], prop['isRand'] = sv_type(elem)
                prop['def'] = sv_def(elem)
                prop['width'] = sv_width(elem)
                prop['isArray'] = isinstance(o._properties[p].element, Array)

                if (isinstance(o._properties[p].element, Array)):
                    prop['maxItems'] = None if isinstance(elem.maxItems, NotPassed) else elem.maxItems
                    prop['minItems'] = None if isinstance(elem.minItems, NotPassed) else elem.minItems
                    prop['maximum']  = "" if getattr(elem.items, "maximum", None) is None or \
                                             isinstance(elem.items.maximum, NotPassed) \
                                          else f"foreach ( m_{p}[i] ) {{ m_{p}[i] <= {elem.items.maximum} }}; "
                    prop['minimum']  = "" if getattr(elem.items, "minimum", None) is None or \
                                             isinstance(elem.items.minimum, NotPassed) \
                                          else f"foreach ( m_{p}[i] ) {{ m_{p}[i] >= {elem.items.minimum} }}; "
                    prop['isEnum']   = False if isinstance(elem.items.enum, NotPassed) else True
                else:
                    prop['maximum']  = "" if getattr(elem, "maximum", None) is None or \
                                             isinstance(elem.maximum, NotPassed) \
                                          else f"m_{p} <= {elem.maximum}; "
                    prop['minimum']  = "" if getattr(elem, "minimum", None) is None or \
                                             isinstance(elem.minimum, NotPassed) \
                                          else f"m_{p} >= {elem.minimum}; "
                    prop['isEnum']   = False if isinstance(elem.enum, NotPassed) else True
                ms.append(prop)
            cs[str(o)] = ms
    return cs

def serialize_sv(*elements: Element):
    ret = {}
    ret['enums'] = serialize_enums(*elements)
    ret['classes'] = serialize_classes(*elements)
    return ret
