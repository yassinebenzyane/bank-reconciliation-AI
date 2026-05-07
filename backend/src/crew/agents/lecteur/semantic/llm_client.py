"""Wrapper OpenAI avec retry, cache JSON et batch.

Le LLM ne reçoit JAMAIS de montants — uniquement du texte libre.
"""
from __future__ import annotations
import json, os, hashlib
from pathlib import Path


class LLMClient:
    def __init__(self, cache_dir: str | None = None):
        self._cache_dir = Path(cache_dir or os.path.join(os.path.dirname(__file__), "..", "cache"))
        self._cache_dir.mkdir(exist_ok=True)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        return self._client

    def _cache_key(self, prompt: str) -> str:
        return hashlib.md5(prompt.encode()).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"

    def call(self, system: str, user: str, *, max_retries: int = 3) -> str:
        """Appel avec cache sur le hash du prompt complet."""
        cache_key  = self._cache_key(system + user)
        cache_file = self._cache_path(cache_key)

        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")

        for attempt in range(max_retries):
            try:
                resp = self._get_client().chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    temperature=0,
                )
                content = resp.choices[0].message.content
                cache_file.write_text(content, encoding="utf-8")
                return content
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                import time; time.sleep(2 ** attempt)

        raise RuntimeError("LLM call failed after retries")

    def call_json(self, system: str, user: str, **kwargs) -> list | dict:
        raw = self.call(system, user, **kwargs)
        # Extraire le JSON si enveloppé dans ```json
        if "```json" in raw:
            raw = raw.split("```json", 1)[1].rsplit("```", 1)[0]
        elif "```" in raw:
            raw = raw.split("```", 1)[1].rsplit("```", 1)[0]
        return json.loads(raw.strip())
