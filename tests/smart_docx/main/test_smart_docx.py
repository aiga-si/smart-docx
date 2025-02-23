import unittest

from smart_docx.main import SmartDocx
from smart_docx.templates.definitions import load_template_definition
from smart_docx.templates.registry import TemplateRegistry


class TestSmartDocx(unittest.TestCase):
    def setUp(self):
        self.template_path = "./resources/template_def.yaml"
        self.output_path = "./resources/cooking.docx"
        self.registry = TemplateRegistry()

    def test_run_success(self):
        template_def = load_template_definition(self.template_path)
        self.registry.register_template(template_def)

        workflow = SmartDocx(self.registry, self.output_path)

        workflow.run("Kuharska predloga", {
            "dish_name": "Pečen losos z limono",
            "main_ingredient": "Losos",
            "cooking_style": "Žar"
        })


if __name__ == "__main__":
    unittest.main()
