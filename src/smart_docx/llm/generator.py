from haystack import Pipeline
from haystack.components.builders import PromptBuilder
from haystack.components.converters import OutputAdapter
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret

from .jsonschema_output_validator import OutputValidator
from .. import settings

_prompt_template_appendix = """
Vrni samo JSON objekt (brez dodatnih oznak, kot so ```json), ki se mora skladati s podano shemo:  
{{schema}}  

Če je shema definirana samo s tipom (npr. `"type": "string"`), ne vrni JSON objekta, ampak le primitivno vrednost v skladu s shemo.  

{% if invalid_reply and error_message %}  
Prejšnji odgovor, ki si ga ustvaril, je bil: **{{invalid_reply}}**  
Struktura JSON odgovora je napačna in je v Pythonu povzročila to napako: **{{error_message}}**  
Popravi odgovor in poskusi znova. Vrni samo popravljen JSON, brez dodatnih razlag.  
{% endif %}  
"""


class Generator:
    def __init__(self, system_prompt: str, prompt_template: str):
        self.system_prompt = system_prompt
        self.prompt_template = prompt_template + _prompt_template_appendix

    def _init_pipeline(self):
        pipeline = Pipeline(max_loops_allowed=5)
        prompt_builder = PromptBuilder(template=self.prompt_template)
        generator = OpenAIGenerator(api_key=Secret.from_token(settings.OPENAI_API_TOKEN), model="gpt-4o")
        output_validator = OutputValidator()

        pipeline.add_component(name="prompt_builder", instance=prompt_builder)
        pipeline.add_component(name="llm", instance=generator)
        pipeline.add_component(name="replies_adapter", instance=OutputAdapter(template="{{ replies[0] }}", output_type=str))
        pipeline.add_component(name="output_validator", instance=output_validator)

        pipeline.connect("prompt_builder", "llm")
        pipeline.connect("llm.replies", "replies_adapter")
        pipeline.connect("replies_adapter", "output_validator")
        pipeline.connect("output_validator.invalid_reply", "prompt_builder.invalid_reply")
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")
        return pipeline

    def generate_text(self, params: dict, schema: dict):
        pipeline = self._init_pipeline()
        prompt_params = params.copy()
        prompt_params["schema"] = schema
        result = pipeline.run({"prompt_builder": prompt_params, "output_validator": {"schema": schema}}, include_outputs_from={"prompt_builder"})
        return result.get("output_validator").get("valid_reply")
