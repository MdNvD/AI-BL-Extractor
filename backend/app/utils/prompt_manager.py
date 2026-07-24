from pathlib import Path

# app/prompts directory
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt(filename: str) -> str:
    """
    Load a prompt file from the prompts folder.
    """

    file_path = PROMPTS_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()