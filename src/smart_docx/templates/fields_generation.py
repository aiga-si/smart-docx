import typing
from dataclasses import dataclass
from typing import Any

import jinja2

from .definitions import TemplateDefinition, SourceType, sort_field_definitions
from ..llm.json_answer_generator import JsonAnswerGenerator

_question_template = """
    Glede na navodila in kontekst, odgovori na vprašanje.    

    Vprašanje: 
    {{question}}
    """


@dataclass
class Field:
    id: str
    value: Any


def _create_question(context: str, question: str) -> str:
    return _question_template.format(context=context, question=question)


class TemplateFieldsGenerator:
    def __init__(self,
                 template_definition: TemplateDefinition,
                 inputs: typing.Dict[str, Any]):
        self.template_definition = template_definition
        self.inputs = {k: Field(k, v) for k, v in inputs.items()}
        self.answer_generator = JsonAnswerGenerator(system_prompt=template_definition.instructions)

    @staticmethod
    def _render_field_instructions(instructions: str, ctx: typing.Dict[str, typing.Any]) -> str:
        return jinja2.Template(instructions).render(ctx)

    def _generate_field_value(self, field_instructions: str, field_context: typing.Dict[str, typing.Any], field_schema: dict) -> typing.Union[str, dict, list]:
        question = _create_question(field_context, field_instructions)
        return self.answer_generator.answer(question, field_schema)

    def generate_template_fields(self) -> typing.List[Field]:
        context = self.inputs.copy()
        template_fields = list(self.inputs.values())

        # sort them, since some may have dependencies on others
        sorted_field_definitions = sort_field_definitions(self.template_definition.fields)

        for field_def in sorted_field_definitions:
            if field_def.source != SourceType.AUTO:
                continue

            field_instructions = field_def.instructions
            field_context = {dep_id: context[dep_id].value for dep_id in field_def.dependencies}

            if field_context:
                field_instructions = self._render_field_instructions(field_def.instructions, field_context)

            field_value = self._generate_field_value(field_instructions, field_context, field_def.value)
            template_field = Field(id=field_def.id, value=field_value)

            context[field_def.id] = template_field
            template_fields.append(template_field)

        return template_fields
