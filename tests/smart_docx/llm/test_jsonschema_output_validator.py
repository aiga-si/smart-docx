import json
import unittest

from smart_docx.llm.jsonschema_output_validator import OutputValidator


class TestOutputValidator(unittest.TestCase):
    def test_valid_dict(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        validator = OutputValidator()
        expected_reply = {"name": "John", "age": 30}
        reply_json = json.dumps(expected_reply)
        result = validator.run(reply_json, schema)
        self.assertIn("valid_reply", result)
        self.assertEqual(expected_reply, result["valid_reply"])

    def test_invalid_dict(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"]
        }
        validator = OutputValidator()
        reply = {"name": "John"}  # Missing 'age'
        reply_json = json.dumps(reply)
        result = validator.run(reply_json, schema)
        self.assertIn("invalid_reply", result)
        self.assertIn("error_message", result)

    def test_valid_string(self):
        schema = {
            "type": "string",
            "minLength": 1
        }
        validator = OutputValidator()
        reply = "Hello, world!"
        result = validator.run(reply, schema)
        self.assertIn("valid_reply", result)
        self.assertEqual(reply, result["valid_reply"])

    def test_invalid_string(self):
        schema = {
            "type": "string",
            "minLength": 1
        }
        validator = OutputValidator()
        reply = ""  # Empty string is invalid due to minLength
        result = validator.run(reply, schema)
        self.assertIn("invalid_reply", result)
        self.assertIn("error_message", result)

    def test_valid_string_array(self):
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        validator = OutputValidator()
        expected_reply = ["apple", "banana", "cherry"]
        str_repyl = '["apple", "banana", "cherry"]'
        result = validator.run(str_repyl, schema)
        self.assertIn("valid_reply", result)
        self.assertEqual(expected_reply, result["valid_reply"])

    def test_invalid_string_array(self):
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        validator = OutputValidator()
        str_reply = '["apple", 10, "cherry"]'
        result = validator.run(str_reply, schema)
        self.assertIn("invalid_reply", result)
        self.assertIn("error_message", result)

    def test_valid_object_array(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"}
                },
                "required": ["name", "value"]
            }
        }
        validator = OutputValidator()
        expected_reply = [{"name": "item1", "value": 10}, {"name": "item2", "value": 20}]
        json_reply = json.dumps(expected_reply)
        result = validator.run(json_reply, schema)
        self.assertIn("valid_reply", result)
        self.assertEqual(expected_reply, result["valid_reply"])


if __name__ == "__main__":
    unittest.main()
