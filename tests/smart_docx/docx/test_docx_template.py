import unittest

from docxtpl import DocxTemplate


class TestDocx(unittest.TestCase):
    def test_render(self):
        output_path = "./resources/raw/output.docx"
        template_path = "./resources/raw/template.docx"
        context = {
            "name": "Svet",
            "items": [
                {"name": "Item 1", "description": "Description for item 1", "price": 10},
                {"name": "Item 2", "description": "Description for item 2", "price": 20},
                {"name": "Item 3", "description": "Description for item 3", "price": 30},
                {"name": "Item 4", "description": "Description for item 4", "price": 40},
                {"name": "Item 5", "description": "Description for item 5", "price": 50},
                {"name": "Item 6", "description": "Description for item 6", "price": 60},
            ]
        }

        docx = DocxTemplate(template_path)
        docx.render(context)
        docx.save(output_path)


if __name__ == "__main__":
    unittest.main()
