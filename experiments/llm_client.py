"""Interchangeable LLM client and interaction log.  Owner: Person 5.

The notebook calls only ask_llm(); the provider is chosen with one string, so
the experiment can be repeated with another model without touching the rest.

    from experiments.llm_client import ask_llm
    raw = ask_llm(prompt, id=1, system="llm_zero", provider="manual", model="...")

Providers:
  - "manual":    prints the prompt and waits for you to paste the answer
                 (works with any chat on the web, no API key). Implemented.
  - "anthropic", "openai", "gemini": TODO(P5), only the one the team uses.

API keys: NEVER in the code or the notebook. Put them in a `.env` file at the
root (already in .gitignore) or in an environment variable; api_key() reads them.

Log (docs/gramatica_es.md, 2.6): every call is appended to
results/logs/llm.jsonl, even when the answer is invalid:

    {"id": 1, "sistema": "llm_zero", "modelo": "...", "temperature": 0,
     "prompt": "...", "respuesta_cruda": "...", "fecha": "2026-11-25T14:03:11-06:00"}

Before calling the API, ask_llm() looks for the same id and sistema in the log
and, if found, reuses that answer (no repeated cost, reproducible runs).
"""

import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from evaluation.formats import LLM_LOG_PATH, ROOT

Provider = Callable[[str, str, float], str]   # (prompt, model, temperature) -> raw answer


# ----------------------------------------------------------------------
# Providers
# ----------------------------------------------------------------------
def manual_provider(prompt: str, model: str, temperature: float) -> str:
    """Show the prompt; the person pastes the answer and ends with a line "FIN"."""
    print(prompt)
    print("\n--- Pega la respuesta del modelo y termina con una línea que diga FIN ---")
    lines = []
    while (line := input()) != "FIN":
        lines.append(line)
    return "\n".join(lines)


def anthropic_provider(prompt: str, model: str, temperature: float) -> str:
    # TODO(P5): official SDK `anthropic`; api_key("ANTHROPIC_API_KEY").
    raise NotImplementedError("TODO(P5): anthropic_provider")


def openai_provider(prompt: str, model: str, temperature: float) -> str:
    # TODO(P5): official SDK `openai`; api_key("OPENAI_API_KEY").
    raise NotImplementedError("TODO(P5): openai_provider")


def gemini_provider(prompt: str, model: str, temperature: float) -> str:
    # TODO(P5): official SDK `google-genai`; api_key("GOOGLE_API_KEY").
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
    *,
    id: int,
    system: str,
    provider: str = "manual",
    model: str = "manual",
    temperature: float = 0,
    log_path: Path = LLM_LOG_PATH,
) -> str:
    """Return the raw answer for (id, system), from the log if it is already there.

    - system: "llm_zero" or "llm_few".
    - model:  the EXACT model name (it goes in the log and in the report).
    - temperature: 0 so the experiment can be repeated.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"proveedor desconocido {provider!r}; usa uno de {sorted(PROVIDERS)}")
    cached = find_in_log(id, system, log_path)
    if cached is not None:
        if cached["prompt"] != prompt:
            print(f"Aviso: id {id} ({system}) está en el log con otro prompt; se reutiliza la respuesta "
                  "guardada. Si el prompt cambió a propósito, borra esas líneas del log.")
        return cached["respuesta_cruda"]
    raw = PROVIDERS[provider](prompt, model, temperature)
    append_to_log({
        "id": id,
        "sistema": system,
        "modelo": model,
        "temperature": temperature,
        "prompt": prompt,
        "respuesta_cruda": raw,
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
    }, log_path)
    return raw


def find_in_log(id: int, system: str, log_path: Path = LLM_LOG_PATH) -> dict | None:
    """Last log entry for this id and system, or None."""
    if not log_path.exists():
        return None
    found = None
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            if entry.get("id") == id and entry.get("sistema") == system:
                found = entry
    return found


def append_to_log(record: dict, log_path: Path = LLM_LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
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
