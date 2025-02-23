import typing

from .definitions import TemplateDefinition
from .validations import validate_template_variables


class TemplateRegistry:
    def __init__(self):
        self.templates: typing.Dict[str, TemplateDefinition] = {}

    def register_template(self, template: TemplateDefinition):
        validate_template_variables(template)

        if template.name in self.templates:
            raise ValueError(f"Template {template.name} already registered")
        self.templates[template.name] = template

    def get_template(self, name: str) -> typing.Optional[TemplateDefinition]:
        return self.templates.get(name)

    def remove_template(self, name: str):
        if name in self.templates:
            del self.templates[name]
        else:
            raise ValueError("Template not found")
