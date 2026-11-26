"""Grammaticality judgements with a Spanish masked language model.  Owner: Person 1.

Gives Transformers a real `acepta` value, so the parser, Transformers and the
LLM can be compared on the same metric.

Method: pseudo-log-likelihood (PLL; Salazar et al., 2020) with the
"word-l2r" correction of Kauf & Ivanova (2023): each subword token is masked
together with the FOLLOWING subwords of the same word, so words split into
several pieces are not over-rewarded. The sentence score is the mean
log-probability per token (length-normalized), and a sentence is accepted
when its score reaches a threshold calibrated on sentences that are NOT in
the test set (data/calibration_acceptability.csv).

    scorer = PLLScorer()                       # BETO, ~440 MB the first time
    scorer.score("Los perros comen.")          # e.g. -1.3 (higher = more acceptable)
    threshold = calibrate_threshold(scores, labels)

A language model only says "how natural is this sentence": it cannot say
WHY a sentence is wrong, so tipo_error stays null for Transformers.
"""

import gc
import math
import time

DEFAULT_MODEL = "dccuchile/bert-base-spanish-wwm-cased"   # BETO; only publishes pytorch_model.bin


class PLLScorer:
    def __init__(self, model_name: str = DEFAULT_MODEL, use_safetensors: bool | None = False) -> None:
        import torch
        from transformers import AutoModelForMaskedLM, AutoTokenizer
        from transformers.utils import logging as hf_logging

        hf_logging.set_verbosity_error()
        hf_logging.disable_progress_bar()
        self._torch = torch
        self.model_name = model_name
        start = time.perf_counter()
        from .hf_loading import local_model_path

        path = local_model_path(model_name)   # only the needed files: no duplicate weights
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForMaskedLM.from_pretrained(path)
        self.model.eval()
        self.load_seconds = time.perf_counter() - start

    def token_log_probs(self, sentence: str) -> list[tuple[str, float]]:
        """(subword, log P(subword | context)) for every subword of the sentence."""
        torch = self._torch
        words = sentence.split()
        encoding = self.tokenizer(words, is_split_into_words=True, return_tensors="pt")
        ids = encoding["input_ids"][0]
        word_ids = encoding.word_ids()
        positions = [i for i, w in enumerate(word_ids) if w is not None]

        # One masked copy of the sentence per subword (word-l2r masking).
        batch = ids.repeat(len(positions), 1)
        for row, i in enumerate(positions):
            for j in range(i, len(word_ids)):
                if word_ids[j] != word_ids[i]:
                    break
                batch[row, j] = self.tokenizer.mask_token_id
        attention = encoding["attention_mask"].repeat(len(positions), 1)
        with torch.no_grad():
            logits = self.model(input_ids=batch, attention_mask=attention).logits
        log_probs = torch.log_softmax(logits, dim=-1)
        return [
            (self.tokenizer.convert_ids_to_tokens(int(ids[i])), float(log_probs[row, i, ids[i]]))
            for row, i in enumerate(positions)
        ]

    def score(self, sentence: str) -> float:
        """Mean log-probability per subword (higher = more acceptable)."""
        values = [lp for _, lp in self.token_log_probs(sentence)]
        return sum(values) / len(values) if values else -math.inf

    def close(self) -> None:
        del self.model, self.tokenizer
        gc.collect()


def calibrate_threshold(scores: list[float], labels: list[bool]) -> tuple[float, float]:
    """Threshold that maximizes accuracy on the calibration sentences.

    Candidates are the midpoints between consecutive sorted scores; ties are
    broken by the largest margin to the nearest score. Returns (threshold,
    calibration accuracy). A sentence is accepted when score >= threshold.
    """
    if not scores or len(scores) != len(labels):
        raise ValueError("hacen falta puntuaciones y etiquetas, en la misma cantidad")
    ordered = sorted(scores)
    candidates = [ordered[0] - 1.0] + [(a + b) / 2 for a, b in zip(ordered, ordered[1:])] + [ordered[-1] + 1.0]

    def accuracy(t: float) -> float:
        return sum((s >= t) == y for s, y in zip(scores, labels)) / len(scores)

    def margin(t: float) -> float:
        return min(abs(s - t) for s in scores)

    best = max(candidates, key=lambda t: (accuracy(t), margin(t)))
    return best, accuracy(best)
