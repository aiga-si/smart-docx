import typing

from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from .jsonschema_output_validator import OutputValidator
from .. import settings

_converter_prompt_template = """
Na naslednje sledeče vprašanje:
{{question}}

Imamo sledeč odgovor:
{{answer}}

Odgovor pretvori v JSON objekt ki se mora skladati s podano shemo:  
{{schema}}  

Vrni samo JSON objekt (brez dodatnih oznak, kot so ```json),
Če je shema definirana samo s tipom (npr. `"type": "string"`), ne vrni JSON objekta, ampak le primitivno vrednost v skladu s shemo.  

{% if invalid_reply and error_message %}  
Prejšnji odgovor, ki si ga ustvaril, je bil: 
**{{invalid_reply}}**  

Struktura JSON odgovora je napačna in je povzročila napako: **{{error_message}}**  
Popravi odgovor in poskusi znova. Vrni samo popravljen JSON, brez dodatnih razlag.  
{% endif %}  
"""


class JsonAnswerGenerator:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def _init_pipeline(self):
        pipeline = Pipeline(max_loops_allowed=5)
        answer_generator = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN),
                                           system_prompt=self.system_prompt,
                                           model="gpt-4o")

        converter_prompt_builder = PromptBuilder(template=_converter_prompt_template)
        json_converter = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN), model="gpt-4o-mini")
        output_validator = OutputValidator()

        pipeline.add_component(name="llm", instance=answer_generator)
        pipeline.add_component(name="llm_adapter", instance=OutputAdapter(template="{{ replies[0] }}", output_type=str))
        pipeline.add_component(name="converter_prompt", instance=converter_prompt_builder)
        pipeline.add_component(name="json_converter", instance=json_converter)
        pipeline.add_component(name="converter_adapter", instance=OutputAdapter(template="{{ replies[0] }}", output_type=str))
        pipeline.add_component(name="output_validator", instance=output_validator)

        pipeline.connect("llm.replies", "llm_adapter")
        pipeline.connect("llm_adapter", "converter_prompt.answer")

        pipeline.connect("converter_prompt", "json_converter")
        pipeline.connect("json_converter.replies", "converter_adapter")

        pipeline.connect("converter_adapter", "output_validator")
        pipeline.connect("output_validator.invalid_reply", "converter_prompt.invalid_reply")
        pipeline.connect("output_validator.error_message", "converter_prompt.error_message")
        return pipeline

    def answer(self, question: str, schema: dict) -> typing.Union[dict, str]:
        pipeline = self._init_pipeline()
        result = pipeline.run(
            {
                "llm": {"prompt": question},
                "converter_prompt": {"schema": schema, "question": question},
                "output_validator": {"schema": schema}}
        )
        return result.get("output_validator").get("valid_reply")
