import unittest

from smart_docx.templates.definitions import FieldDefinition, SourceType, TemplateDefinition


class TestTemplateDefinition(unittest.TestCase):
    def test_valid_template_definition(self):
        field_def = FieldDefinition(
            id="username",
            source=SourceType.INPUT,
            instructions="Enter the username for {{ user }}",
            value={"type": "string"},
        )

        template_def = TemplateDefinition(
            name="UserTemplate",
            file="path/to/template.docx",
            description="Template for user details",
            instructions="Fill in the user details",
            fields=[field_def]
        )

        # Assert that the template definition is created successfully
        self.assertEqual("UserTemplate", template_def.name)
        self.assertEqual("path/to/template.docx", template_def.file)
        self.assertEqual("Template for user details", template_def.description)
        self.assertEqual("Fill in the user details", template_def.instructions)
        self.assertEqual(1, len(template_def.fields))
        self.assertEqual("username", template_def.fields[0].id)
        self.assertEqual(SourceType.INPUT, template_def.fields[0].source)
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
                file="path/to/template.docx",
                description="Template with duplicate fields",
                instructions="Fill in the user details",
                fields=[field_def_1, field_def_2]
            )

        self.assertIn("Duplicate field IDs found:", str(context.exception))


if __name__ == "__main__":
    unittest.main()
