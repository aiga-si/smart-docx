import unittest

from jsonschema import validate, ValidationError

from smart_docx.llm.json_answer_generator import JsonAnswerGenerator


class TestJsonAnswerGenerator(unittest.TestCase):
    def test_generate_answer(self):
        system_prompt = "Na vprašanje odgovori čim bolj natančno in sledi navodilom."
        question = "Povej mi ime, starost in stranko trenutnega predsednika ZDA"
        json_schema = {
            "type": "object",
            "properties": {
                "ime": {"type": "string"},
                "starost": {"type": "integer"},
                "stranka": {"type": "string"}
            },
            "required": ["ime", "starost", "stranka"]
        }

        ag = JsonAnswerGenerator(system_prompt)
        answer = ag.answer(question, json_schema)

        print(answer)

        # Validate that the answer conforms to the JSON schema
        try:
            validate(instance=answer, schema=json_schema)
            valid = True
        except ValidationError as e:
            print("Validation Error:", e)
            valid = False

        self.assertTrue(valid, "The generated answer does not conform to the expected JSON schema")


if __name__ == '__main__':
    unittest.main()
