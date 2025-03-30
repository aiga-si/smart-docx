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
            ],
            "items2": [
                {"name": "Item 1", "description": "Description for item 1", "price": 10},
                {"name": "Item 2", "description": "Description for item 2", "price": 20},
                {"name": "Item 3", "description": "Description for item 3", "price": 30},
            ]
        }

        docx = DocxTemplate(template_path)
        docx.render(context)
        docx.save(output_path)


if __name__ == "__main__":
    unittest.main()
