import typing

from .templates.fields_generation import TemplateFieldsGenerator
from .templates.registry import TemplateRegistry
from .templates.rendering import TemplateRenderer


class SmartDocx:
    def __init__(self,
                 template_registry: TemplateRegistry,
                 output_path: str):
        self.template_registry = template_registry
        self.output_path = output_path

    def run(self, template_id: str, inputs: typing.Dict[str, typing.Any]):
        template_definition = self.template_registry.get_template(template_id)
        if not template_definition:
            raise ValueError(f'Template {template_id} not found.')

        template_definition.validate_inputs(inputs)

        fields = TemplateFieldsGenerator(template_definition=template_definition, inputs=inputs).generate_template_fields()

        rendered = TemplateRenderer(template_file=template_definition.file)
        return rendered.render(fields, self.output_path)
