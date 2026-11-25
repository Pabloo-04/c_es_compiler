"""Interchangeable LLM client and interaction log.  Owner: Person 5.

The notebook calls only ask_llm(); the provider is chosen with one string, so
the experiment can be repeated with another model without touching the rest.

    from experiments.llm_client import ask_llm
    answer = ask_llm(prompt, provider="manual")

Providers:
  - "manual":    prints the prompt and waits for you to paste the answer
                 (works with any chat on the web, no API key). Implemented.
  - "anthropic", "openai", "gemini": TODO(P5), only the one the team uses.

API keys: NEVER in the code or the notebook. Put them in a `.env` file at the
root (already in .gitignore) or in an environment variable, and read them
with os.environ.

Every call is appended to results/logs/llm_log.jsonl (the assignment asks
to keep ALL prompts and answers).
"""

import json
import os
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "results" / "logs" / "llm_log.jsonl"

Provider = Callable[[str, dict], str]


# ----------------------------------------------------------------------
# Providers
# ----------------------------------------------------------------------
def manual_provider(prompt: str, options: dict) -> str:
    """Show the prompt; the person pastes the answer and ends with a line "FIN"."""
    print(prompt)
    print("\n--- Pega la respuesta del modelo y termina con una línea que diga FIN ---")
    lines = []
    while (line := input()) != "FIN":
        lines.append(line)
    return "\n".join(lines)


def anthropic_provider(prompt: str, options: dict) -> str:
    # TODO(P5): official SDK `anthropic`; key in os.environ["ANTHROPIC_API_KEY"];
    #           model and temperature from `options`.
    raise NotImplementedError("TODO(P5): anthropic_provider")


def openai_provider(prompt: str, options: dict) -> str:
    # TODO(P5): official SDK `openai`; key in os.environ["OPENAI_API_KEY"].
    raise NotImplementedError("TODO(P5): openai_provider")


def gemini_provider(prompt: str, options: dict) -> str:
    # TODO(P5): official SDK `google-genai`; key in os.environ["GOOGLE_API_KEY"].
    raise NotImplementedError("TODO(P5): gemini_provider")


PROVIDERS: dict[str, Provider] = {
    "manual": manual_provider,
    "anthropic": anthropic_provider,
    "openai": openai_provider,
    "gemini": gemini_provider,
}


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def ask_llm(
    prompt: str,
    provider: str = "manual",
    *,
    log: bool = True,
    metadata: dict | None = None,
    **options,
) -> str:
    """Send `prompt` and return the answer text.

    - options:  provider settings, e.g. model="...", temperature=0.
                Use temperature 0 so the experiment can be repeated.
    - metadata: saved in the log, e.g. {"id": "S001", "modo": "zero_shot"}.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"proveedor desconocido {provider!r}; usa uno de {sorted(PROVIDERS)}")
    start = time.perf_counter()
    answer = PROVIDERS[provider](prompt, options)
    seconds = time.perf_counter() - start
    if log:
        log_interaction({
            "proveedor": provider,
            "opciones": options,
            **(metadata or {}),
            "prompt": prompt,
            "respuesta": answer,
            "segundos": round(seconds, 3),
        })
    return answer


def log_interaction(record: dict, path: Path = LOG_PATH) -> None:
    """Append one JSON line with a UTC timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def api_key(name: str) -> str:
    """Read a key from the environment or from .env at the root; never hard-code it."""
    if name in os.environ:
        return os.environ[name]
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    raise KeyError(f"falta la variable {name} (en el entorno o en .env)")
