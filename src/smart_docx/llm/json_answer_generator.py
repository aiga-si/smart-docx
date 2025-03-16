import typing

from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from .jsonschema_output_validator import OutputValidator
from .. import settings

_converter_prompt_template = """
Si strokovnjak na področju pretvarjanja teksta v JSON obliko.Spodaj sta navedena vprašanje ter odovor.
Tvoja naloga je pretvoriti dani odgovor v veljaven JSON objekt, ki mora biti popolnoma skladen s podano JSON shemo.

- Upoštevaj strukturo sheme – JSON objekt mora strogo slediti shemi {{schema}}. Vsi zahtevani atributi morajo biti prisotni in pravilno oblikovani.
- Vrni samo JSON – ne dodajaj uvodnih ali zaključnih oznak (npr. ```json), opisov ali razlag
- Primitivne vrednosti – če je shema definirana le s tipom (npr. "type": "string" ali "type": "integer"), vrni samo ustrezno primitivno vrednost in ne JSON objekta.

{% if invalid_reply and error_message %}  
Prejšnji JSON objekt, ki si ga ustvaril, je bil: 
**{{invalid_reply}}**  
in ni ustrezal shemi.

Struktura JSON odgovora je napačna in je povzročila napako: **{{error_message}}**  
Popravi odgovor in poskusi znova. Vrni samo popravljen JSON, brez dodatnih razlag.  
{% endif %}  


Vprašanje:
{{question}}

Odgovor:
{{answer}}
"""


def _init_pipeline(system_prompt: str):
    pipeline = Pipeline(max_loops_allowed=5)
    answer_generator = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN),
                                       system_prompt=system_prompt,
                                       model="gpt-4o")

    converter_prompt_builder = PromptBuilder(template=_converter_prompt_template)
    json_converter = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN),
                                     model="gpt-4o")
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


class JsonAnswerGenerator:
    def __init__(self, system_prompt: str):
        self.pipeline = _init_pipeline(system_prompt)

    def answer(self, question: str, schema: dict) -> typing.Union[dict, str]:
        result = self.pipeline.run(
            {
                "llm": {"prompt": question},
                "converter_prompt": {"schema": schema, "question": question},
                "output_validator": {"schema": schema}}
        )
        return result.get("output_validator").get("valid_reply")
