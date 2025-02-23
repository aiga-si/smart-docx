import ast
import json
import typing
from enum import Enum

import jsonschema
from haystack import component


class SchemaType(Enum):
    SIMPLE = 'simple'  # primitive types only
    SIMPLE_ARRAY = 'simple_array'  # array of primitive types
    COMPLEX = 'complex'  # object or an array of objects


def _determine_schema_type(schema: dict) -> SchemaType:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        types = set(schema_type)
    else:
        types = {schema_type}

    if "object" in types:
        return SchemaType.COMPLEX

    if "array" in types:
        items_type = schema.get("items", {}).get("type")
        if "object" in items_type:
            return SchemaType.COMPLEX
        return SchemaType.SIMPLE_ARRAY

    return SchemaType.SIMPLE


@component
class OutputValidator:
    def __init__(self):
        self.iteration_counter = 0

    @component.output_types(valid_reply=typing.Union[dict, str, list], invalid_reply=typing.Optional[str], error_message=typing.Optional[str])
    def run(self, reply: typing.Any, schema: dict):
        self.iteration_counter += 1
        schema_type = _determine_schema_type(schema)
        try:
            parsed_reply = reply
            if isinstance(reply, str):
                if schema_type is SchemaType.COMPLEX:
                    parsed_reply = json.loads(reply)
                elif schema_type is SchemaType.SIMPLE_ARRAY:
                    parsed_reply = ast.literal_eval(reply)

            jsonschema.validate(instance=parsed_reply, schema=schema)
            return {"valid_reply": parsed_reply}

        except (json.JSONDecodeError, jsonschema.ValidationError, ValueError) as e:
            # TODO: switch with a debug log
            print(
                f"OutputValidator at Iteration {self.iteration_counter}: Invalid response from LLM - Let's try again.\n"
                f"Output from LLM:\n {reply} \n"
                f"Error from OutputValidator: {e}"
            )
            return {"invalid_reply": reply, "error_message": str(e)}
