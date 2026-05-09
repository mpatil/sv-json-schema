![](https://img.shields.io/badge/license-MIT-green)

# sv-json-schema
This is a tool to generate a SystemVerilog configuration class from a schema specification of the data. The data format is JSON.

## Introduction

Given a JSON schema specification of data, the tool produces a systemverilog class which when instantiated as an object can read and parse a JSON data file(conforming to the specified schema), dump a JSON file of the its representation and randomize its data in the specified constrained manner.

The json schema library used is statham-schema. The SystemVerilog serializer/deserializer is built on sv-embed-json.

## Reference

1. [statham-schema](https://github.com/jacksmith15/statham-schema)
1. [sv-embed-json](https://github.com/mpatil/sv-embed-json)
1. [JSON Schema](https://json-schema.org/)

## Development

1. Clone the repository: `git clone https://github.com/mpatil/sv-json-schema.git && cd sv-json-schema`
1. Initialise git submodules: `git submodule update --init --recursive`
1. Install the requirements: `pip install -r requirements.txt`
1. Setup simulator env. Mentor Questa (`qrun`) and Synopsys VCS are supported.
1. Run the default generation with Questa: `make`
1. Or run with VCS: `make vcsrun`
