import json


def parse_json(text: str):
    """
    Remove markdown code fences from Gemini output
    and convert it into a Python object.
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    return json.loads(text)