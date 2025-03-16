import unittest

from smart_docx.smart_docx import SmartDocx
from smart_docx.templates.definitions import load_template_definition


class TestSmartDocx(unittest.TestCase):
    def test_render_and_save(self):
        template_def_path = "./resources/template_def.yaml"
        output_path = "./resources/cooking.docx"

        template_def = load_template_definition(template_def_path)
        template_file_path = "./resources/cooking_template.docx"

        smart_docx = SmartDocx(template_definition=template_def, template_file=template_file_path)

        smart_docx.render({
            "dish_name": "Pečen losos z limono",
            "main_ingredient": "Losos",
            "cooking_style": "Žar"
        })

        smart_docx.save(output_path)


if __name__ == "__main__":
    unittest.main()
