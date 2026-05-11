import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mistral_api")

DATA_INPUT_DIR: str = os.getenv("DATA_INPUT_DIR", "data/input")
DATA_OUTPUT_DIR: str = os.getenv("DATA_OUTPUT_DIR", "data/output")
HISTORY_PATH: str = os.getenv("HISTORY_PATH", "data/history.json")


def get_llm(size: str = "large") -> str:
    """Retourne l'identifiant LiteLLM selon LLM_PROVIDER.

    Providers supportés :
    - openai      → gpt-4o-mini (small) / gpt-4o (large)
    - mistral_api → mistral-small-latest / mistral-large-latest
    - ollama      → ollama/mistral-small
    """
    if LLM_PROVIDER == "ollama":
        return "ollama/mistral-small"
    if LLM_PROVIDER == "openai":
        return "gpt-4o-mini" if size == "small" else "gpt-4o"
    if size == "small":
        return "mistral/mistral-small-latest"
    return "mistral/mistral-large-latest"
