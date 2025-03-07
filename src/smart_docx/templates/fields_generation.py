import typing
from dataclasses import dataclass
from typing import Any

import jinja2
from haystack import Pipeline
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.generators import OpenAIGenerator

from .definitions import TemplateDefinition, SourceType, sort_field_definitions
from .. import settings
from ..llm.generator import Generator

prompt_template = """
    Glede na navodila in kontekst, odgovori na vprašanje.    

    Kontekst:
    {{context}}

    Vprašanje: 
    {{question}}
    """


def _init_pipeline(instructions: str) -> Pipeline:
    p = Pipeline()
    p.add_component(instance=PromptBuilder(template=prompt_template), name="prompt_builder")
    p.add_component(instance=OpenAIGenerator(system_prompt=instructions, api_key=settings.OPENAI_API_KEY), name="llm")
    p.connect("prompt_builder", "llm")
    return p


@dataclass
class Field:
    id: str
    value: Any


class TemplateFieldsGenerator:
    def __init__(self,
                 template_definition: TemplateDefinition,
                 inputs: typing.Dict[str, Any]):
        self.template_definition = template_definition
        self.inputs = {k: Field(k, v) for k, v in inputs.items()}
        self.generator = Generator(system_prompt=template_definition.instructions,
                                   prompt_template=prompt_template)

    @staticmethod
    def _render_field_instructions(instructions: str, ctx: typing.Dict[str, typing.Any]) -> str:
        return jinja2.Template(instructions).render(ctx)

    def _generate_field_value(self, field_instructions: str, field_context: typing.Dict[str, typing.Any], field_schema: dict) -> typing.Union[str, dict, list]:
        return self.generator.generate_text({"question": field_instructions, "context": field_context}, field_schema)

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
