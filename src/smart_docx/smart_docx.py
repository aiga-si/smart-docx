import typing
from os import PathLike

from docxtpl import DocxTemplate

from .templates.definitions import TemplateDefinition
from .templates.fields_generation import TemplateFieldsGenerator, Field


def _fields_to_dict(fields: typing.List[Field]) -> typing.Dict[str, typing.Any]:
    return {field.id: field.value for field in fields}


class SmartDocx:
    def __init__(self, template_definition: TemplateDefinition):
        self.template_definition = template_definition
        self.docx = None

    def render(self, inputs: typing.Dict[str, typing.Any]):
        self.template_definition.validate_inputs(inputs)
        generator = TemplateFieldsGenerator(self.template_definition, inputs=inputs)
        fields = generator.generate_template_fields()

        context = _fields_to_dict(fields)
        self.docx = DocxTemplate(self.template_definition.file)
        self.docx.render(context)

    def save(self, filename: typing.Union[typing.IO[bytes], str, PathLike]):
        if not self.docx and not self.docx.is_rendered:
            raise ValueError("Document has not yet been rendered")
        self.docx.save(filename)
