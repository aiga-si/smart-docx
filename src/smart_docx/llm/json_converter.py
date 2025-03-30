import re
import typing

from haystack import component
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from jinja2 import Template


def clean_json_string(json_string: str) -> str:
    match = re.search(r'```json\n?(.*?)\n?```', json_string, re.DOTALL)
    return match.group(1).strip() if match else json_string.strip()


@component
class JsonConverter:
    def __init__(self, api_key: Secret, model: str = "gpt-4o"):
        self.generator = OpenAIGenerator(api_key=api_key, model=model)
        self.prompt_template = Template("""
               Si strokovnjak na področju pretvarjanja teksta v JSON obliko.Spodaj sta navedena vprašanje ter odovor.
               Tvoja naloga je pretvoriti dani odgovor v veljaven JSON objekt, ki mora biti popolnoma skladen s podano JSON shemo.

               - Upoštevaj strukturo sheme – JSON objekt mora strogo slediti shemi {{ schema | tojson }}. Vsi zahtevani atributi morajo biti prisotni in pravilno oblikovani.
               - Vrni samo JSON – ne dodajaj uvodnih ali zaključnih oznak (npr. ```json), opisov ali razlag
               - Primitivne vrednosti – če je shema definirana le s tipom (npr. "type": "string" ali "type": "integer"), vrni samo ustrezno primitivno vrednost in ne JSON objekta.

               {% if invalid_reply and error_message %}  
               Prejšnji JSON objekt, ki si ga ustvaril, je bil: 
               **{{ invalid_reply }}**  
               in ni ustrezal shemi.

               Struktura JSON odgovora je napačna in je povzročila napako: **{{ error_message }}**  
               Popravi odgovor in poskusi znova. Vrni samo popravljen JSON, brez dodatnih razlag.  

               {% else %}
               Vprašanje:
               {{ question }}

               Odgovor:
               {{ answer }}
               {% endif %} 
               """)

    @component.output_types(json_str=str)
    def run(self, question: str, answer: str, schema: dict, invalid_reply: typing.Optional[str] = None, error_message: typing.Optional[str] = None):
        prompt = self.prompt_template.render(
            schema=schema,
            question=question,
            answer=answer,
            invalid_reply=invalid_reply,
            error_message=error_message)

        run_result = self.generator.run(prompt)
        json_str = run_result.get("replies")[0]
        return {"json_str": clean_json_string(json_str)}
