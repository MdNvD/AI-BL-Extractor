import re
import time

from google import genai

from app.core.config import GEMINI_API_KEY
from app.utils.prompt_manager import load_prompt
from app.utils.json_parser import parse_json


class GeminiService:

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    # --------------------------------------------------
    # Generate Gemini Response
    # --------------------------------------------------

    def _generate(self, prompt: str, text: str):

        models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite"
        ]

        last_error = None

        for model in models:

            for attempt in range(3):

                try:

                    print(f"\nUsing {model} (Attempt {attempt + 1}/3)")

                    response = self.client.models.generate_content(
                        model=model,
                        contents=f"{prompt}\n\n{text}"
                    )

                    return parse_json(response.text)

                except Exception as e:

                    last_error = e
                    print(f"{model} failed: {e}")

                    if attempt < 2:
                        print("Retrying in 5 seconds...")
                        time.sleep(5)

            print("Switching to next model...")

        raise last_error

    # --------------------------------------------------
    # Header Extraction
    # --------------------------------------------------

    def extract_header(self, text: str):

        prompt = load_prompt("header_prompt.txt")

        header = self._generate(prompt, text)

        if not isinstance(header, dict):
            return {}

        # Normalize voyage
        if header.get("voyage"):
            header["voyage"] = (
                str(header["voyage"])
                .replace(" ", "")
                .upper()
            )

        # Normalize strings
        for key, value in list(header.items()):

            if isinstance(value, str):

                value = value.strip()

                if value.upper() in {"", "-", "N/A", "NULL", "NONE"}:
                    header[key] = None
                else:
                    header[key] = value

        return header

    # --------------------------------------------------
    # Container Extraction
    # --------------------------------------------------

    def extract_containers(self, text: str):

        prompt = load_prompt("container_prompt.txt")

        result = self._generate(prompt, text)

        if not isinstance(result, dict):
            return {"containers": []}

        containers = result.get("containers", [])

        for container in containers:

            # Container Number
            if container.get("container_number"):
                container["container_number"] = (
                    str(container["container_number"])
                    .strip()
                    .upper()
                )

            # Seal Number
            if container.get("seal_number"):

                seal = (
                    str(container["seal_number"])
                    .strip()
                    .upper()
                )

                # OCR correction
                #seal = re.sub(r"^HLC1L", "HLC11", seal)

                container["seal_number"] = seal

            # Size
            if container.get("size"):
                container["size"] = (
                    str(container["size"])
                    .strip()
                    .upper()
                )

            # Convert numeric fields safely
            for field in ("cartons", "weight_kg", "cbm"):
                if container.get(field) is None:
                    continue

                try:
                    if field == "cartons":
                        container[field] = int(float(container[field]))
                    else:
                        container[field] = float(container[field])
                except (ValueError, TypeError):
                    pass

        result["containers"] = containers
        return result

    # --------------------------------------------------
    # Summary Extraction
    # --------------------------------------------------

    def extract_summary(self, text: str):

        prompt = load_prompt("summary_prompt.txt")

        summary = self._generate(prompt, text)

        if not isinstance(summary, dict):
            return {}

        for field in (
            "total_containers",
            "total_cartons",
            "total_weight",
            "total_cbm",
        ):
            if summary.get(field) is None:
                continue

            try:
                summary[field] = float(summary[field])
                if summary[field].is_integer():
                    summary[field] = int(summary[field])
            except (ValueError, TypeError):
                pass

        return summary