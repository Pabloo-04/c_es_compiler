"""Interchangeable LLM client and interaction log.  Owner: Person 5.

The notebook calls only ask_llm(); the provider is chosen with one string, so
the experiment can be repeated with another model without touching the rest.

    from experiments.llm_client import ask_llm
    raw = ask_llm(prompt, id=1, system="llm_zero", provider="manual", model="...")

Providers:
  - "manual":    prints the prompt and waits for you to paste the answer
                 (works with any chat on the web, no API key).
  - "gemini":    Google Gemini API, SDK `google-genai`, key GOOGLE_API_KEY.
                 Free tier with requests-per-minute limits: on 429/503 it waits
                 and retries.
  - "anthropic": Claude API, SDK `anthropic`, key ANTHROPIC_API_KEY. Current
                 Claude models do not accept `temperature`, so it is not sent
                 (the log still records the value that was asked for).
  - "openai":    not implemented (the team does not use it).

API keys: NEVER in the code or the notebook. Put them in a `.env` file at the
root (already in .gitignore) or in an environment variable; api_key() reads them.

Log (docs/gramatica_es.md, 2.6): every call is appended to
results/logs/llm.jsonl, even when the answer is invalid:

    {"id": 1, "sistema": "llm_zero", "modelo": "...", "temperature": 0,
     "prompt": "...", "respuesta_cruda": "...", "fecha": "2026-11-25T14:03:11-06:00",
     "tiempo_ms": 812.4, "tokens_entrada": 1290, "tokens_salida": 210}

The last three keys are extra (for the cost analysis): tiempo_ms is the time of
the real call, so a reused answer keeps it; the tokens appear only when the
provider reports them.

Before calling the API, ask_llm() looks for the same id and sistema in the log
and, if found, reuses that answer (no repeated cost, reproducible runs).
"""

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from evaluation.formats import LLM_LOG_PATH, ROOT


@dataclass
class Reply:
    """A raw answer plus the tokens the provider reports (None if it does not say)."""

    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None


# (prompt, model, temperature) -> raw answer. A provider may return a plain
# string (manual, tests) or a Reply with the tokens.
Provider = Callable[[str, str, float], "str | Reply"]


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


def gemini_provider(prompt: str, model: str, temperature: float) -> Reply:
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=api_key("GOOGLE_API_KEY"))
    response = with_retries(
        lambda: client.models.generate_content(
            model=model, contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        ),
        # 429: per-minute limit of the free tier; 500/503: model overloaded.
        is_retryable=lambda e: isinstance(e, errors.APIError) and e.code in (429, 500, 503),
    )
    usage = response.usage_metadata
    output = None
    if usage is not None:
        # Thinking models report their reasoning apart; it is also output (and billed).
        output = (usage.candidates_token_count or 0) + (getattr(usage, "thoughts_token_count", 0) or 0)
    return Reply(response.text or "", usage.prompt_token_count if usage else None, output)


def anthropic_provider(prompt: str, model: str, temperature: float) -> Reply:
    """Claude. `temperature` is not sent: current models reject it.

    No fallback model is configured on purpose: every answer must come from
    the model under study.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=api_key("ANTHROPIC_API_KEY"), max_retries=6)
    response = client.messages.create(
        model=model, max_tokens=16000, messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return Reply(text, response.usage.input_tokens, response.usage.output_tokens)


def openai_provider(prompt: str, model: str, temperature: float) -> str:
    raise NotImplementedError("el equipo no usa OpenAI; implementarlo solo si cambia el proveedor")


PROVIDERS: dict[str, Provider] = {
    "manual": manual_provider,
    "gemini": gemini_provider,
    "anthropic": anthropic_provider,
    "openai": openai_provider,
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
    start = time.perf_counter()
    reply = PROVIDERS[provider](prompt, model, temperature)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if isinstance(reply, str):
        reply = Reply(reply)
    record = {
        "id": id,
        "sistema": system,
        "modelo": model,
        "temperature": temperature,
        "prompt": prompt,
        "respuesta_cruda": reply.text,
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tiempo_ms": round(elapsed_ms, 1),
    }
    if reply.input_tokens is not None:
        record["tokens_entrada"] = reply.input_tokens
    if reply.output_tokens is not None:
        record["tokens_salida"] = reply.output_tokens
    append_to_log(record, log_path)
    return reply.text


def read_log(log_path: Path = LLM_LOG_PATH) -> list[dict]:
    """Every log entry, in order."""
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def with_retries(call: Callable, is_retryable: Callable[[Exception], bool], attempts: int = 6,
                 base_delay: float = 5.0, sleep: Callable[[float], None] = time.sleep):
    """Run call(); on a retryable error wait 5 s, 10 s, 20 s... and try again."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as e:
            if attempt == attempts - 1 or not is_retryable(e):
                raise
            delay = min(base_delay * 2 ** attempt, 120)
            print(f"  límite de uso o modelo saturado ({e}); reintento en {delay:.0f} s")
            sleep(delay)
    raise ValueError("attempts debe ser al menos 1")


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
