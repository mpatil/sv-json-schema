![](https://img.shields.io/badge/license-MIT-green)

# sv-json-schema
This is a SystemVerilog configuration class (with json transducers) generation utility from  JSON schema.

## Introduction

This utility allows taking a json schema and generating a corresponding SystemVerilog configuration class with JSON serializer and deserializer.

The json schema library used is statham-schema. The SystemVerilog serializer deserializer comes from JSONinSV.

## Reference

1. [statham-schema](https://github.com/jacksmith15/statham-schema)
1. [JSONinSV](https://github.com/zhouchuanrui/JSONinSV)
1. [JSON Schema](https://json-schema.org/)

## Development

1. Clone the repository: `git clone https://github.com/mpatil/sv-json-schema.git && cd sv-json-schema`
1. Initialise git submodules: `git submodule update --init --recursive`
1. Install the requirements: `pip install -r requirements.txt`
1. Setup simulator env. Only mentor questa supported right now.
1. Run the default generation: `make`
