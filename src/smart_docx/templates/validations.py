import typing
from collections import deque

from docxtpl import DocxTemplate

from .definitions import TemplateDefinition, FieldDefinition


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


def _get_template_variables(file_path: str) -> typing.Set[str]:
    tpl = DocxTemplate(file_path)
    return tpl.get_undeclared_template_variables()


def validate_template_variables(template_definition: TemplateDefinition) -> None:
    defined_fields = set([f.id for f in template_definition.fields])
    dependencies = set.union(*[f.dependencies for f in template_definition.fields])

    missing_dependencies = dependencies - defined_fields
    if missing_dependencies:
        raise ValueError(f"Missing dependencies: {', '.join(missing_dependencies)}")

    # verify all fields that are provided in the template are defined
    fields_in_template = _get_template_variables(template_definition.file)
    missing_variables = fields_in_template - defined_fields
    if missing_variables:
        raise ValueError(f"Missing defined fields, which are present in template: {', '.join(missing_variables)}")

    # verify there is no cyclic dependencies
    sort_field_definitions(template_definition.fields)

    return None
