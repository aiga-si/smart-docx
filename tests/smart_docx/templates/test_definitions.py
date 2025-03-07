import os
import tempfile
import typing
import unittest

from docx import Document

from smart_docx.templates.definitions import FieldDefinition, SourceType, TemplateDefinition


class TestTemplateDefinition(unittest.TestCase):
    def setUp(self):
        self.created_files = []

    def tearDown(self):
        for file in self.created_files:
            if os.path.exists(file) and os.path.isfile(file):
                print(f"Removing file {file}")
                os.remove(file)

    def create_temp_docx_file(self, paragraphs: typing.List[str]) -> str:
        file_path = tempfile.NamedTemporaryFile(delete_on_close=False, delete=False, suffix='.docx')
        doc = Document()
        for par in paragraphs:
            doc.add_paragraph(par)
        doc.save(file_path)
        self.created_files.append(file_path.name)
        return file_path.name

    def test_valid_template_definition(self):
        docx = self.create_temp_docx_file([
            "Hello my name is {{ user }}",
            "My username is {{ username }}"
        ])

        template_def = TemplateDefinition(
            name="UserTemplate",
            file=docx,
            description="Template for user details",
            instructions="Fill in the user details",
            fields=[
                FieldDefinition(
                    id="username",
                    source=SourceType.AUTO,
                    instructions="Enter the username for {{ user }}",
                    value={"type": "string"},
                ),
                FieldDefinition(
                    id="user",
                    source=SourceType.INPUT,
                    instructions="User",
                    value={"type": "string"},
                )
            ]
        )

        # Assert that the template definition is created successfully
        self.assertEqual("UserTemplate", template_def.name)
        self.assertEqual(docx, template_def.file)
        self.assertEqual("Template for user details", template_def.description)
        self.assertEqual("Fill in the user details", template_def.instructions)
        self.assertEqual(2, len(template_def.fields))
        self.assertEqual("username", template_def.fields[0].id)
        self.assertEqual(SourceType.AUTO, template_def.fields[0].source)
        self.assertEqual({"type": "string"}, template_def.fields[0].value)
        self.assertEqual("Enter the username for {{ user }}", template_def.fields[0].instructions)
        self.assertEqual({"user"}, template_def.fields[0]._dependencies)

    def test_invalid_field_definition_invalid_json_schema(self):
        # Test invalid JSON schema in FieldDefinition
        with self.assertRaises(ValueError):
            FieldDefinition(
                id="username",
                source=SourceType.INPUT,
                value={1: 1},  # Invalid JSON schema
                instructions="Enter the username"
            )

    def test_invalid_template_definition_duplicate_field_ids(self):
        docx = self.create_temp_docx_file([
            "My username is {{ username }}"
        ])

        # Test duplicate field IDs in TemplateDefinition
        field_def_1 = FieldDefinition(
            id="username",
            source=SourceType.INPUT,
            value={"type": "string"},
            instructions="Enter the username"
        )
        field_def_2 = FieldDefinition(
            id="username",  # Duplicate ID
            source=SourceType.INPUT,
            value={"type": "string"},
            instructions="Enter another username"
        )

        with self.assertRaises(ValueError) as context:
            TemplateDefinition(
                name="DuplicateFieldTemplate",
                file=docx,
                description="Template with duplicate fields",
                instructions="Fill in the user details",
                fields=[field_def_1, field_def_2]
            )

        self.assertIn("Duplicate field IDs found:", str(context.exception))

    def test_validate_template_variables(self):
        template_docx = self.create_temp_docx_file([
            "Name: {{ name }}",
            "Date: {{ date }}",
            "Purpose: {{r purpose }}"
        ])

        # valid template definition
        template_def = TemplateDefinition(
            name="test",
            file=template_docx,
            instructions="instructions ...",
            description="description ...",
            fields=[
                FieldDefinition(
                    id="name",
                    source=SourceType.AUTO,
                    value={"type": "string"},
                    instructions="Get name of the person"
                ),
                FieldDefinition(
                    id="date",
                    source=SourceType.AUTO,
                    value={"type": "string"},
                    instructions="Get date of birth"
                ),
                FieldDefinition(
                    id="purpose",
                    source=SourceType.AUTO,
                    value={"type": "string"},
                    instructions="Purpose of event"
                ),
            ]
        )

    def test_validate_invalid_variables(self):
        template_docx = self.create_temp_docx_file([
            "Name: {{ name }}",
            "Date: {{ date }}",
            "Purpose: {{r purpose }}"
        ])

        with self.assertRaises(ValueError) as context:
            # missing field definition
            TemplateDefinition(
                name="test",
                file=template_docx,
                instructions="instructions ...",
                description="description ...",
                fields=[
                    FieldDefinition(
                        id="name",
                        source=SourceType.AUTO,
                        value={"type": "string"},
                        instructions="Get name of the person"
                    ),
                    FieldDefinition(
                        id="date",
                        source=SourceType.AUTO,
                        value={"type": "string"},
                        instructions="Get date of birth"
                    ),
                ]
            )

        self.assertIn("Missing defined fields, which are present in template: purpose", str(context.exception))

        # circular dependencies
        with self.assertRaises(ValueError) as context:
            circular_dependencies = TemplateDefinition(
                file=template_docx,
                name="circular_dependencies",
                instructions="instructions ...",
                description="description ...",
                fields=[
                    FieldDefinition(
                        id="name",
                        source=SourceType.AUTO,
                        value={"type": "string"},
                        instructions="Get name of the person {{ purpose }}"
                    ),
                    FieldDefinition(
                        id="date",
                        source=SourceType.AUTO,
                        value={"type": "string"},
                        instructions="Get date of birth {{ name }}"
                    ),
                    FieldDefinition(
                        id="purpose",
                        source=SourceType.AUTO,
                        value={"type": "string"},
                        instructions="Purpose of event {{ date }}"
                    ),
                ]
            )

        self.assertIn("Circular dependency between fields", str(context.exception))


if __name__ == "__main__":
    unittest.main()
