"""Download exactly the files a HuggingFace model needs, once, and load from disk.

Why: when a model only publishes pytorch_model.bin, transformers 5 also
downloads an automatic safetensors conversion from another revision of the
Hub, even with use_safetensors=False: a second full copy of the weights
(1.1 GB for XLM-R, 440 MB for BETO). Loading from a local folder that only
contains the files we asked for avoids that.

    path = local_model_path("dccuchile/bert-base-spanish-wwm-cased")
    model = AutoModelForMaskedLM.from_pretrained(path)
"""

# Weights file each model publishes (the only big file we download).
WEIGHTS = {
    "wietsedv/xlm-roberta-base-ft-udpos28-es": "pytorch_model.bin",
    "mrm8488/bert-spanish-cased-finetuned-pos-16-tags": "model.safetensors",
    "dccuchile/bert-base-spanish-wwm-cased": "pytorch_model.bin",
}

# Small files: configuration and tokenizer.
SMALL_FILES = ["*.json", "*.txt", "*.model", "*.spm"]


def local_model_path(model_name: str, weights: str | None = None) -> str:
    """Local folder with the config, the tokenizer and ONE weights file.

    Uses the cache if the files are already there (works offline); downloads
    them otherwise. `weights` defaults to WEIGHTS[model_name].
    """
    from huggingface_hub import snapshot_download

    weights = weights or WEIGHTS.get(model_name)
    if weights is None:
        raise ValueError(f"no sé qué archivo de pesos usar para {model_name}; agrégalo a WEIGHTS")
    patterns = SMALL_FILES + [weights]
    try:
        return snapshot_download(model_name, allow_patterns=patterns, local_files_only=True)
    except Exception:  # not in the cache yet (or incomplete): download only these files
        return snapshot_download(model_name, allow_patterns=patterns)
