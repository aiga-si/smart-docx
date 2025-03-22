import unittest

from smart_docx.llm.json_converter import clean_json_string


class TestJsonConverter(unittest.TestCase):
    def test_clean_json_string(self):
        self.assertEqual(clean_json_string("```json\n{\"key\": \"value\"}\n```"), "{\"key\": \"value\"}")

        self.assertEqual(clean_json_string("```json{\"key\": \"value\"}```"), "{\"key\": \"value\"}")

        self.assertEqual(clean_json_string("{\"key\": \"value\"}"), "{\"key\": \"value\"}")

        self.assertEqual(clean_json_string(""), "")

        self.assertEqual(clean_json_string("```json\n```"), "")

        self.assertEqual(clean_json_string("Some text ```json\n{\"key\": \"value\"}\n``` some text after"), "{\"key\": \"value\"}")


if __name__ == "__main__":
    unittest.main()
