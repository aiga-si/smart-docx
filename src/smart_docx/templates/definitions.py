import typing
from collections import deque
from enum import Enum
from os import PathLike
from typing import List, Dict, Any

import jsonschema
import yaml
from docxtpl import DocxTemplate
from jinja2 import Environment, meta
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, field_validator, model_validator, ConfigDict


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

    @field_validator('value')
    @classmethod
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
    file: typing.Union[typing.IO[bytes], str, PathLike]
    description: str
    instructions: str
    fields: List[FieldDefinition]

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow arbitrary types

    @field_validator('fields')
    @classmethod
    def validate_fields(cls, fields: List[FieldDefinition]) -> List[FieldDefinition]:
        field_ids = [field.id for field in fields]

        if len(field_ids) != len(set(field_ids)):
            duplicate_ids = [fid for fid in field_ids if field_ids.count(fid) > 1]
            raise ValueError(f"Duplicate field IDs found: {duplicate_ids}")

        return fields

    @model_validator(mode='after')
    def validate_template_variables(self) -> typing.Self:
        defined_fields = set([f.id for f in self.fields])
        dependencies = set.union(*[f.dependencies for f in self.fields])

        missing_dependencies = dependencies - defined_fields
        if missing_dependencies:
            raise ValueError(f"Missing dependencies: {', '.join(missing_dependencies)}")

        # verify all fields that are provided in the template are defined
        fields_in_template = _get_template_variables(self.file)
        missing_variables = fields_in_template - defined_fields
        if missing_variables:
            raise ValueError(f"Missing defined fields, which are present in template: {', '.join(missing_variables)}")

        # verify there is no cyclic dependencies
        sort_field_definitions(self.fields)

        return self

    def validate_inputs(self, inputs: typing.Dict[str, Any]):
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


def _get_template_variables(file_path: typing.Union[typing.IO[bytes], str, PathLike]) -> typing.Set[str]:
    tpl = DocxTemplate(file_path)
    return tpl.get_undeclared_template_variables()


def sort_field_definitions(fields: typing.List[FieldDefinition]) -> typing.List[FieldDefinition]:
    graph = {field.id: field for field in fields}
    in_degree = {field.id: 0 for field in fields}  # Track incoming edges
    adjacency_list = {field.id: set() for field in fields}

    # populate adjacency list and in-degree count
    for field in fields:
        for dep in field.dependencies:
            if dep not in graph:
                raise ValueError(f"Dependency {dep} not found among field definitions")
            adjacency_list[dep].add(field.id)
            in_degree[field.id] += 1

    # queue with nodes having no dependencies (in-degree = 0)
    queue = deque([field_id for field_id, degree in in_degree.items() if degree == 0])
    sorted_fields = []

    while queue:
        field_id = queue.popleft()
        sorted_fields.append(graph[field_id])

        for neighbor in adjacency_list[field_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_fields) != len(fields):
        raise ValueError("Circular dependency between fields")

    return sorted_fields
