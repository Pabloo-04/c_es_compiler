"""Data formats shared by everyone: the test set and the results files.

Executable copy of docs/gramatica_es.md, Part 2. Code is in English; the
column and key names are in Spanish, exactly as in the document, because
everybody (and metrics.py) reads them.

Files (section 2.1, all UTF-8):
    data/test_set.csv            test set with the expected output (P4)
    results/<sistema>.jsonl      one line per sentence for each system
    results/metrics.csv          computed metrics (P4)
    results/logs/llm.jsonl       every LLM prompt and raw answer (P5)

Loading validates every row against the rules of the document, so a typo in
the test set shows up as a clear error instead of a wrong metric.
"""

import csv
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEST_SET_PATH = ROOT / "data" / "test_set.csv"
RESULTS_DIR = ROOT / "results"
METRICS_PATH = RESULTS_DIR / "metrics.csv"
LLM_LOG_PATH = RESULTS_DIR / "logs" / "llm.jsonl"

SYSTEMS = ("parser", "spacy", "transformers", "llm_zero", "llm_few")
LEVELS = (1, 2, 3)
CATEGORIES = ("Prn", "Det", "Pos", "Noun", "Adj", "Intens", "Adv", "Verb", "Prep", "X")
ERROR_TYPES = ("sintactico", "concordancia")
PP_ATTACHMENTS = ("sustantivo", "verbo", "ambigua")
PHENOMENA = (
    "svo", "intransitivo", "adjetivo", "adverbio", "intensificador", "pp", "posesivo",
    "preterito", "ambiguedad", "concordancia_np", "concordancia_sv", "sujeto_omitido",
    "subordinada", "coordinacion", "orden_libre", "fuera_lexico",
)
TEST_SET_COLUMNS = (
    "id", "nivel", "oracion", "en_gramatica", "espanol_valido", "tipo_error",
    "fenomeno", "etiquetas", "sujeto", "verbo", "objeto", "pp_adjunta",
)


def sentence_words(sentence: str) -> list[str]:
    """Words of a test sentence, lowercase and without the final period."""
    return sentence.rstrip().rstrip(".").lower().split()


# ----------------------------------------------------------------------
# Test set (section 2.3)
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class TestItem:
    __test__ = False  # the name starts with "Test": tell pytest it is not a test class

    id: int
    level: int
    sentence: str
    in_grammar: bool          # en_gramatica: what the parser and the LLM must answer
    valid_spanish: bool       # espanol_valido: correct Spanish, regardless of our grammar
    error_type: str | None    # None for "ninguno"
    phenomena: tuple[str, ...]
    tags: tuple[tuple[str, str], ...]   # (("ella", "Prn"), ("come", "Verb"), ...)
    subject: str              # "" if there is no explicit subject
    verb: str
    object: str               # "" if there is no direct object
    pp_attachment: str | None = None   # first PP: "sustantivo" | "verbo" | "ambigua"; None = no PP

    @property
    def words(self) -> list[str]:
        return sentence_words(self.sentence)

    @classmethod
    def from_row(cls, row: dict[str, str], line: int | None = None) -> "TestItem":
        where = f"conjunto de prueba, id {row.get('id', '?')}" + (f" (línea {line})" if line else "")
        try:
            item = cls(
                id=int(row["id"]),
                level=int(row["nivel"]),
                sentence=row["oracion"].strip(),
                in_grammar=_yes_no(row["en_gramatica"], "en_gramatica"),
                valid_spanish=_yes_no(row["espanol_valido"], "espanol_valido"),
                error_type=None if row["tipo_error"].strip() == "ninguno" else row["tipo_error"].strip(),
                phenomena=tuple(p.strip() for p in row["fenomeno"].split(";") if p.strip()),
                tags=tuple(_tag(pair) for pair in row["etiquetas"].split()),
                subject=row["sujeto"].strip().lower(),
                verb=row["verbo"].strip().lower(),
                object=row["objeto"].strip().lower(),
                pp_attachment=row["pp_adjunta"].strip() or None,
            )
            item.validate()
        except (KeyError, ValueError) as e:
            raise ValueError(f"{where}: {e}") from None
        return item

    def validate(self) -> None:
        """The rules of docs/gramatica_es.md, 2.3."""
        if self.level not in LEVELS:
            raise ValueError(f"nivel {self.level} inválido (1, 2 o 3)")
        if self.in_grammar and self.error_type is not None:
            raise ValueError("una oración en la gramática lleva tipo_error 'ninguno'")
        if not self.in_grammar and self.error_type not in ERROR_TYPES:
            raise ValueError(f"tipo_error debe ser uno de {ERROR_TYPES}")
        if self.in_grammar and not self.valid_spanish:
            raise ValueError("la gramática no debería aceptar español incorrecto")
        unknown = [p for p in self.phenomena if p not in PHENOMENA]
        if unknown or not self.phenomena:
            raise ValueError(f"fenómeno inválido o vacío: {unknown}")
        if not self.sentence[:1].isupper() or not self.sentence.endswith("."):
            raise ValueError("la oración va con mayúscula inicial y punto final")
        body = self.sentence[:-1]
        if any(not (c.isalpha() or c == " ") for c in body):
            raise ValueError("solo se permite el punto final como signo de puntuación")
        words = self.words
        if [w for w, _ in self.tags] != words:
            raise ValueError(f"las etiquetas no coinciden con las palabras de la oración: {words}")
        bad = [c for _, c in self.tags if c not in CATEGORIES]
        if bad:
            raise ValueError(f"categorías inválidas en etiquetas: {bad}")
        for name, value in (("sujeto", self.subject), ("verbo", self.verb), ("objeto", self.object)):
            if value and value not in words:
                raise ValueError(f"{name} '{value}' no es una palabra de la oración")
        if not self.verb:
            raise ValueError("falta el verbo")
        has_pp = any(category == "Prep" for _, category in self.tags)
        if self.pp_attachment is not None and self.pp_attachment not in PP_ATTACHMENTS:
            raise ValueError(f"pp_adjunta debe ser uno de {PP_ATTACHMENTS} o vacío")
        if has_pp and self.pp_attachment is None:
            raise ValueError("la oración tiene una preposición: falta pp_adjunta")
        if not has_pp and self.pp_attachment is not None:
            raise ValueError("pp_adjunta va vacío si la oración no tiene preposición")


def _yes_no(value: str, column: str) -> bool:
    value = value.strip().lower()
    if value not in ("si", "no"):
        raise ValueError(f"{column} debe ser 'si' o 'no', no {value!r}")
    return value == "si"


def _tag(pair: str) -> tuple[str, str]:
    word, sep, category = pair.rpartition("/")
    if not sep or not word:
        raise ValueError(f"etiqueta mal escrita {pair!r} (debe ser palabra/Cat)")
    return word.lower(), category


def load_test_set(path: Path | str = TEST_SET_PATH) -> list[TestItem]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != TEST_SET_COLUMNS:
            raise ValueError(f"{path}: las columnas deben ser {', '.join(TEST_SET_COLUMNS)}")
        items = [TestItem.from_row(row, line) for line, row in enumerate(reader, start=2)]
    ids = [item.id for item in items]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"ids repetidos en el conjunto de prueba: {duplicates}")
    return items


# ----------------------------------------------------------------------
# Results of each system (section 2.4)
# ----------------------------------------------------------------------
@dataclass
class Prediction:
    id: int
    system: str
    accepts: bool | None                 # None: the system does not decide (spaCy, Transformers)
    error_type: str | None = None
    tags: list[list[str]] | None = None  # [["ella", "Prn"], ...], lowercase, no period
    subject: str | None = None           # "" = no subject detected; None = not computed
    verb: str | None = None
    object: str | None = None
    pp_attachment: str | None = None     # "sustantivo" | "verbo" | "ambigua" | None
    tree: str | None = None
    num_trees: int | None = None
    time_ms: float = 0.0
    run_error: str | None = None         # the system crashed on this sentence

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "sistema": self.system,
            "acepta": self.accepts,
            "tipo_error": self.error_type,
            "etiquetas": self.tags,
            "sujeto": self.subject,
            "verbo": self.verb,
            "objeto": self.object,
            "pp_adjunta": self.pp_attachment,
            "arbol": self.tree,
            "num_arboles": self.num_trees,
            "tiempo_ms": round(self.time_ms, 3),
            "error_ejecucion": self.run_error,
        }

    @classmethod
    def from_json(cls, d: dict) -> "Prediction":
        return cls(
            id=d["id"],
            system=d["sistema"],
            accepts=d["acepta"],
            error_type=d.get("tipo_error"),
            tags=d.get("etiquetas"),
            subject=d.get("sujeto"),
            verb=d.get("verbo"),
            object=d.get("objeto"),
            pp_attachment=d.get("pp_adjunta"),
            tree=d.get("arbol"),
            num_trees=d.get("num_arboles"),
            time_ms=d.get("tiempo_ms", 0.0),
            run_error=d.get("error_ejecucion"),
        )

    def validate(self) -> None:
        """Structural checks only. Values outside the agreed sets (an LLM that
        answers "DET" or tipo_error "lexico") are saved as given and simply
        count as wrong in the metrics: they are part of what is measured."""
        if self.system not in SYSTEMS:
            raise ValueError(f"sistema desconocido {self.system!r}; usa uno de {SYSTEMS}")
        if self.accepts is not False and self.error_type is not None:
            raise ValueError(f"id {self.id}: tipo_error solo si el sistema rechaza")
        if self.tags is not None and any(len(pair) != 2 for pair in self.tags):
            raise ValueError(f"id {self.id}: cada etiqueta es [palabra, categoría]")


def read_jsonl(path: Path | str) -> list[dict]:
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}, línea {number}: JSON inválido ({e})") from e
    return rows


def write_jsonl(path: Path | str, rows: Iterable[dict], append: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a" if append else "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def results_path(system: str) -> Path:
    if system not in SYSTEMS:
        raise ValueError(f"sistema desconocido {system!r}; usa uno de {SYSTEMS}")
    return RESULTS_DIR / f"{system}.jsonl"


def save_predictions(system: str, predictions: list[Prediction], items: list[TestItem] | None = None) -> Path:
    """Write results/<system>.jsonl after checking the rule of 2.4: one line per
    sentence of the test set, in the same order and with the same id."""
    items = load_test_set() if items is None else items
    expected = [i.id for i in items]
    got = [p.id for p in predictions]
    if got != expected:
        raise ValueError(f"{system}: los ids deben ser los del conjunto de prueba y en el mismo orden")
    for p in predictions:
        if p.system != system:
            raise ValueError(f"id {p.id}: sistema {p.system!r} en el archivo de {system!r}")
        p.validate()
    path = results_path(system)
    write_jsonl(path, (p.to_json() for p in predictions))
    return path


def load_predictions(system: str) -> list[Prediction]:
    return [Prediction.from_json(row) for row in read_jsonl(results_path(system))]
