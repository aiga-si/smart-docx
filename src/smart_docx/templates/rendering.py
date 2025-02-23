from dataclasses import dataclass
from os import PathLike
from typing import List, Dict, Union, IO, Any

from docxtpl import DocxTemplate


@dataclass
class Field:
    id: str
    value: Any


def _fields_to_dict(fields: List[Field]) -> Dict[str, Any]:
    d = dict()
    for field in fields:
        d[field.id] = field.value
    return d


class TemplateRenderer:

    def __init__(self, template_file: Union[IO[bytes], str, PathLike]):
        self.template_path = template_file

    def render(self, fields: List[Field], output_path: str):
        context = _fields_to_dict(fields)

        try:
            doc = DocxTemplate(self.template_path)
            doc.render(context)
            doc.save(output_path)
        except Exception as e:
            raise RuntimeError(f"Failed to render template: {e}")
