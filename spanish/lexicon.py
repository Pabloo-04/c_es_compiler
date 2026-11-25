"""The lexicon: words with their categories and features.  Owner: Person 3.

The data lives in data/lexicon.json (one entry per written form):

    "gatos": [{"categoria": "SUST", "lema": "gato", "genero": "masc", "numero": "pl"}],
    "bajo":  [{"categoria": "ADJ",  "lema": "bajo", "genero": "masc", "numero": "sg"},
              {"categoria": "PREP", "lema": "bajo"}],

Keys are lowercase. A word with several entries is ambiguous; the parser
chooses. Loading and lookup are implemented; building the word list is P3's job.
"""

import json
from pathlib import Path

from .tokens import Category, Features, Reading

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "lexicon.json"

_CATEGORY_BY_LABEL = {c.value: c for c in Category}


def reading_from_json(entry: dict) -> Reading:
    """{"categoria": "SUST", "lema": "gato", "genero": "masc", "numero": "sg"} -> Reading."""
    try:
        category = _CATEGORY_BY_LABEL[entry["categoria"]]
    except KeyError as e:
        raise ValueError(f"categoría inválida o ausente en {entry}") from e
    features = Features(
        gender=entry.get("genero"),
        number=entry.get("numero"),
        person=entry.get("persona"),
        tense=entry.get("tiempo"),
    )
    return Reading(category, entry["lema"], features)


class Lexicon:
    def __init__(self, entries: dict[str, list[Reading]]) -> None:
        self._entries = {word.lower(): tuple(readings) for word, readings in entries.items()}

    @classmethod
    def load(cls, path: Path | str = DEFAULT_PATH) -> "Lexicon":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        entries = {}
        for word, readings in raw.items():
            if word.startswith("_"):      # "_comentario" and similar keys are ignored
                continue
            entries[word] = [reading_from_json(r) for r in readings]
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

    # TODO(P3): words_by_category(category) -> list[str]: useful for the docs
    #           and for P4 when building sentences for the test set.
