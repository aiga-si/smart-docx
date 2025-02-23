import typing
from enum import Enum
from typing import List, Dict, Any

import jsonschema
import yaml
from jinja2 import Environment, meta
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, field_validator


class SaferDraft7Validator(jsonschema.Draft7Validator):
    META_SCHEMA = {**jsonschema.Draft7Validator.META_SCHEMA, "additionalProperties": False}


class SourceType(Enum):
    INPUT = "INPUT"
    AUTO = "AUTO"


class FieldDefinition(BaseModel):
    id: str
    source: SourceType
    value: dict  # JSON schema
    instructions: str
    _dependencies: typing.Set[str] = []

    @classmethod
    @field_validator('value')
    def validate_json_schema(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError("The JSON schema must not be empty.")

        try:
            SaferDraft7Validator.check_schema(v)
        except SchemaError as e:
            raise ValueError(f"Invalid JSON schema: {e}")

        return v

    def model_post_init(self, _: Any) -> None:
        env = Environment()
        parsed_content = env.parse(self.instructions)
        self._dependencies = meta.find_undeclared_variables(parsed_content)

    @property
    def dependencies(self) -> typing.Set[str]:
        return self._dependencies


class TemplateDefinition(BaseModel):
    name: str
    file: str  # Path to the DOCX file
    description: str
    instructions: str
    fields: List[FieldDefinition]

    @classmethod
    @field_validator('fields')
    def validate_fields(cls, fields: List[FieldDefinition]) -> List[FieldDefinition]:
        field_ids = [field.id for field in fields]

        if len(field_ids) != len(set(field_ids)):
            duplicate_ids = [fid for fid in field_ids if field_ids.count(fid) > 1]
            raise ValueError(f"Duplicate field IDs found: {duplicate_ids}")

        return fields

    def validate_inputs(self, inputs: typing.Dict[str, Any]):
        # check if any missing
        provided_inputs = inputs.keys()
        template_required_inputs = set([field.id for field in self.fields if field.source == SourceType.INPUT])

        missing_inputs = template_required_inputs - provided_inputs
        if missing_inputs:
            raise ValueError(f"Missing inputs: {', '.join(missing_inputs)}")


def load_template_definition(yaml_path: str) -> TemplateDefinition:
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    fields = [FieldDefinition(**field) for field in data.get("fields", [])]

    return TemplateDefinition(
        name=data["name"],
        file=data["file"],
        description=data.get("description", ""),
        instructions=data.get("instructions", ""),
        fields=fields
    )
