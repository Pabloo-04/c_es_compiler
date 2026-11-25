"""Data formats shared by everyone: the test set and the results files.

PROPOSAL to be confirmed by Person 1 and Person 4 (docs/formato_salida.md).
Code is in English; the JSON keys are in Spanish, like the rest of the data.

Test set (data/test_set.jsonl, one JSON object per line):
    {"id": "S001", "nivel": "simple", "oracion": "el gato come",
     "gramatical": true,   # correct Spanish, according to a native speaker
     "cubierta": true,     # our CFG must accept it
     "arbol": "(O (SN (DET el) (SUST gato)) (SV (V come)))",   # only if cubierta
     "tipo_error": null,   # if not cubierta: "lexico" | "sintactico" | "concordancia"
     "notas": ""}

Results (results/<sistema>.jsonl, one prediction per sentence):
    {"id": "S001", "sistema": "parser",
     "aceptada": true,
     "arbol": "(O ...)" | null,
     "categorias": ["DET", "SUST", "V"] | null,   # one tag per word, our tagset
     "tipo_error": null | "lexico" | "sintactico" | "concordancia" | "otro",
     "detalle": "free text: error message, raw answer...",
     "extra": {}}                                   # anything system-specific
"""

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_SET_PATH = ROOT / "data" / "test_set.jsonl"
RESULTS_DIR = ROOT / "results"

LEVELS = ("simple", "intermedia", "compleja")
SYSTEMS = ("parser", "spacy", "transformers", "llm_zero_shot", "llm_few_shot")
ERROR_TYPES = ("lexico", "sintactico", "concordancia", "otro")


@dataclass(frozen=True)
class TestItem:
    __test__ = False  # the name starts with "Test": tell pytest it is not a test class

    id: str
    level: str
    sentence: str
    grammatical: bool
    covered: bool
    tree: str | None
    error_type: str | None
    notes: str = ""

    @classmethod
    def from_json(cls, d: dict) -> "TestItem":
        item = cls(
            id=d["id"],
            level=d["nivel"],
            sentence=d["oracion"],
            grammatical=d["gramatical"],
            covered=d["cubierta"],
            tree=d.get("arbol"),
            error_type=d.get("tipo_error"),
            notes=d.get("notas", ""),
        )
        item.validate()
        return item

    def validate(self) -> None:
        if self.level not in LEVELS:
            raise ValueError(f"{self.id}: nivel inválido {self.level!r}")
        if self.covered and not self.tree:
            raise ValueError(f"{self.id}: una oración cubierta necesita su árbol esperado")
        if self.covered and self.error_type:
            raise ValueError(f"{self.id}: una oración cubierta no lleva tipo_error")
        if not self.covered and self.error_type not in ERROR_TYPES:
            raise ValueError(f"{self.id}: una oración no cubierta necesita tipo_error")
        if self.covered and not self.grammatical:
            raise ValueError(f"{self.id}: la gramática no debería cubrir español incorrecto")
        if self.tree:
            from spanish.tree import Node

            Node.from_bracketed(self.tree)  # raises ValueError if malformed


@dataclass
class Prediction:
    id: str
    system: str
    accepted: bool
    tree: str | None = None
    categories: list[str] | None = None
    error_type: str | None = None
    detail: str = ""
    extra: dict = field(default_factory=dict)

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "sistema": self.system,
            "aceptada": self.accepted,
            "arbol": self.tree,
            "categorias": self.categories,
            "tipo_error": self.error_type,
            "detalle": self.detail,
            "extra": self.extra,
        }

    @classmethod
    def from_json(cls, d: dict) -> "Prediction":
        return cls(
            id=d["id"],
            system=d["sistema"],
            accepted=d["aceptada"],
            tree=d.get("arbol"),
            categories=d.get("categorias"),
            error_type=d.get("tipo_error"),
            detail=d.get("detalle", ""),
            extra=d.get("extra", {}),
        )


# ----------------------------------------------------------------------
# Reading and writing
# ----------------------------------------------------------------------
def read_jsonl(path: Path | str) -> list[dict]:
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}, línea {number}: JSON inválido ({e})") from e
    return rows


def write_jsonl(path: Path | str, rows: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_test_set(path: Path | str = TEST_SET_PATH) -> list[TestItem]:
    items = [TestItem.from_json(row) for row in read_jsonl(path)]
    ids = [item.id for item in items]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"ids repetidos en el set de prueba: {sorted(duplicates)}")
    return items


def results_path(system: str) -> Path:
    if system not in SYSTEMS:
        raise ValueError(f"sistema desconocido {system!r}; usa uno de {SYSTEMS}")
    return RESULTS_DIR / f"{system}.jsonl"


def save_predictions(system: str, predictions: Iterable[Prediction]) -> Path:
    path = results_path(system)
    write_jsonl(path, (p.to_json() for p in predictions))
    return path


def load_predictions(system: str) -> list[Prediction]:
    return [Prediction.from_json(row) for row in read_jsonl(results_path(system))]

