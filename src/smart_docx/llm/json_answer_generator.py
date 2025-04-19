import os
import typing

from haystack import Pipeline, component
from haystack.components.converters import OutputAdapter
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from haystack_integrations.components.generators.google_ai import GoogleAIGeminiGenerator

from .json_converter import JsonConverter
from .jsonschema_output_validator import OutputValidator


def _get_llm_generator():
    openai_api_token = os.getenv("OPENAI_API_TOKEN")
    gemini_api_token = os.getenv("GOOGLE_API_KEY")

    if openai_api_token:
        return AnswerGenerator(generator=OpenAIGenerator(api_key=Secret.from_token(openai_api_token), model="gpt-4o"))
    elif gemini_api_token:
        return AnswerGenerator(generator=GoogleAIGeminiGenerator(api_key=Secret.from_token(gemini_api_token), model="gemini-2.0-flash"))
    else:
        raise ValueError("No valid API key found in environment variables.")


@component
class AnswerGenerator:

    def __init__(self, generator: typing.Union[OpenAIGenerator, GoogleAIGeminiGenerator]):
        self.generator = generator

    @component.output_types(replies=typing.List[str])
    def run(self, prompt: str):
        if isinstance(self.generator, OpenAIGenerator):
            return self.generator.run(prompt=prompt)
        if isinstance(self.generator, GoogleAIGeminiGenerator):
            return self.generator.run(parts=[prompt])

def _init_pipeline():
    pipeline = Pipeline(max_runs_per_component=5)
    generator = _get_llm_generator()
    json_converter = JsonConverter(generator)

    output_validator = OutputValidator()

    pipeline.add_component(name="llm", instance=generator)
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
        self.system_prompt = system_prompt
        self.pipeline = _init_pipeline()

    def answer(self, question: str, schema: dict) -> typing.Union[dict, str]:
        task = f"{self.system_prompt} \n {question}"
        result = self.pipeline.run(
            {
                "llm": {"prompt": task},
                "json_converter": {"schema": schema, "question": question},
                "output_validator": {"schema": schema}}
        )
        return result.get("output_validator").get("valid_reply")
