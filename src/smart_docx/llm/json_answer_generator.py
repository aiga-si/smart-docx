import typing

from haystack import Pipeline
from haystack.components.converters import OutputAdapter
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from .json_converter import JsonConverter
from .jsonschema_output_validator import OutputValidator
from .. import settings


def _init_pipeline(system_prompt: str):
    pipeline = Pipeline(max_loops_allowed=5)
    answer_generator = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN),
                                       system_prompt=system_prompt,
                                       model=settings.QA_MODEL)

    json_converter = JsonConverter(api_key=Secret.from_token(settings.OPENAI_API_TOKEN), model=settings.JSON_CONVERTER_MODEL)

    output_validator = OutputValidator()

    pipeline.add_component(name="llm", instance=answer_generator)
    pipeline.add_component(name="llm_adapter", instance=OutputAdapter(template="{{ replies[0] }}", output_type=str))
    pipeline.add_component(name="json_converter", instance=json_converter)
    pipeline.add_component(name="output_validator", instance=output_validator)

    pipeline.connect("llm.replies", "llm_adapter")
    pipeline.connect("llm_adapter", "json_converter.answer")

    pipeline.connect("json_converter", "output_validator")
    pipeline.connect("output_validator.invalid_reply", "json_converter.invalid_reply")
    pipeline.connect("output_validator.error_message", "json_converter.error_message")
    return pipeline


class JsonAnswerGenerator:
    def __init__(self, system_prompt: str):
        self.pipeline = _init_pipeline(system_prompt)

    def answer(self, question: str, schema: dict) -> typing.Union[dict, str]:
        result = self.pipeline.run(
            {
                "llm": {"prompt": question},
                "json_converter": {"schema": schema, "question": question},
                "output_validator": {"schema": schema}}
        )
        return result.get("output_validator").get("valid_reply")
