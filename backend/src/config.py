import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mistral_api")

DATA_INPUT_DIR: str = os.getenv("DATA_INPUT_DIR", "data/input")
DATA_OUTPUT_DIR: str = os.getenv("DATA_OUTPUT_DIR", "data/output")
HISTORY_PATH: str = os.getenv("HISTORY_PATH", "data/history.json")


def get_llm(size: str = "large") -> str:
    """Retourne l'identifiant LiteLLM selon LLM_PROVIDER et la taille souhaitée.

    Swap entre Mistral API et Ollama local sans toucher aux agents :
    - mistral_api → mistral/mistral-large-latest  ou  mistral/mistral-small-latest
    - ollama      → ollama/mistral-small (unique modèle local disponible en POC)
    """
    if LLM_PROVIDER == "ollama":
        return "ollama/mistral-small"
    if size == "small":
        return "mistral/mistral-small-latest"
    return "mistral/mistral-large-latest"
