"""Word-level POS tagging with a HuggingFace token-classification model.  Owner: Person 1.

Why not transformers.pipeline(..., aggregation_strategy=...)? Its entity
grouping can merge NEIGHBOURING words with the same tag (two ADV in a row
become one "entity"), which breaks the word-by-word comparison. Here the
words are given already split, and each word takes the label of its FIRST
subword token: exactly one tag per word, always.

    tagger = HFTagger("wietsedv/xlm-roberta-base-ft-udpos28-es")
    tagger.tag(["Ella", "come", "una", "manzana"])   # ['PRON', 'VERB', 'DET', 'NOUN']

The model is downloaded once to ~/.cache/huggingface. Runs on CPU; call
close() (or `del tagger`) before loading another model to free memory.
"""

import gc
import time


class HFTagger:
    def __init__(self, model_name: str, use_safetensors: bool | None = None) -> None:
        """use_safetensors=False for models that only publish pytorch_model.bin
        (e.g. wietsedv/xlm-roberta-base-ft-udpos28-es). Otherwise transformers
        ALSO downloads an automatic safetensors conversion from another revision
        of the Hub: a second copy of the weights (1 GB for that model)."""
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        from transformers.utils import logging as hf_logging

        # Keep the notebook output readable: no progress bars or load reports.
        hf_logging.set_verbosity_error()
        hf_logging.disable_progress_bar()

        self.model_name = model_name
        self._torch = torch
        start = time.perf_counter()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name, use_safetensors=use_safetensors)
        self.model.eval()
        self.load_seconds = time.perf_counter() - start
        self.labels = self.model.config.id2label

    @property
    def parameters(self) -> int:
        return sum(p.numel() for p in self.model.parameters())

    def tag(self, words: list[str]) -> list[str]:
        """One label per word, in the model's own tagset (UPOS for the models we use)."""
        encoding = self.tokenizer(words, is_split_into_words=True, return_tensors="pt", truncation=True)
        with self._torch.no_grad():
            logits = self.model(**encoding).logits[0]
        predicted = logits.argmax(dim=-1).tolist()
        tags: list[str | None] = [None] * len(words)
        for position, word_index in enumerate(encoding.word_ids()):
            if word_index is not None and tags[word_index] is None:   # first subword of each word
                tags[word_index] = self.labels[predicted[position]]
        return [t if t is not None else "X" for t in tags]

    def close(self) -> None:
        del self.model, self.tokenizer
        gc.collect()
