"""The lexicon: words with their categories and features.  Owner: Person 3.

The data lives in data/lexicon.json, in the format of docs/gramatica_es.md (1.3):

    "niña":  {"cat": "Noun", "gen": "f", "num": "sg"},
    "mató":  {"cat": "Verb", "tiempo": "pret", "pers": 3, "num": "sg"},

An ambiguous word has a LIST of entries instead of one:

    "bajo":  [{"cat": "Adj", "gen": "m", "num": "sg"}, {"cat": "Prep"}],

Keys are lowercase; "lema" is optional (defaults to the word). Loading and
lookup are implemented; building the word list is P3's job.
"""

import json
from pathlib import Path

from .tokens import CATEGORY_BY_LABEL, Category, Features, Reading

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "lexicon.json"


def reading_from_json(word: str, entry: dict) -> Reading:
    """{"cat": "Noun", "gen": "f", "num": "sg"} -> Reading."""
    label = entry.get("cat")
    if label not in CATEGORY_BY_LABEL or label == Category.X.value:
        raise ValueError(f"'{word}': categoría inválida o ausente en {entry}")
    features = Features(
        gender=entry.get("gen"),
        number=entry.get("num"),
        person=entry.get("pers"),
        tense=entry.get("tiempo"),
    )
    return Reading(CATEGORY_BY_LABEL[label], entry.get("lema", word), features)


class Lexicon:
    def __init__(self, entries: dict[str, list[Reading]]) -> None:
        self._entries = {word.lower(): tuple(readings) for word, readings in entries.items()}

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> "Lexicon":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = {}
        for word, value in raw.items():
            if word.startswith("_"):      # "_comentario" and similar keys are ignored
                continue
            items = value if isinstance(value, list) else [value]
            entries[word] = [reading_from_json(word, item) for item in items]
        return cls(entries)

    def lookup(self, word: str) -> tuple[Reading, ...]:
        """All readings of a word (case-insensitive). Empty tuple if unknown."""
        return self._entries.get(word.lower(), ())

    def __contains__(self, word: str) -> bool:
        return word.lower() in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def words(self) -> list[str]:
        return sorted(self._entries)

    def words_by_category(self, category: Category) -> list[str]:
        """Words that can be this category (for docs, the LLM prompt and the test set)."""
        return sorted(w for w, rs in self._entries.items() if any(r.category is category for r in rs))
