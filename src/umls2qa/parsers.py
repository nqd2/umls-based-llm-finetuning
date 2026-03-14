from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from .config import split_csv_like


@dataclass
class UmlsConcept:
    cui: str
    pref: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    definitions: List[str] = field(default_factory=list)
    semantic_types: List[str] = field(default_factory=list)
    parents: Set[str] = field(default_factory=set)
    children: Set[str] = field(default_factory=set)
    related: Set[str] = field(default_factory=set)


@dataclass
class UmlsTables:
    concepts: Dict[str, UmlsConcept]


def _iter_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip():
                yield line


def parse_mrconso(
    path: Path,
    sab_include: Optional[Set[str]] = None,
    lang_filter: str = "ENG",
) -> Dict[str, UmlsConcept]:
    """
    Parse MRCONSO.RRF to build basic concept vocabulary.

    Columns (simplified):
    CUI|LAT|TS|LUI|STT|SUI|ISPREF|AUI|SAUI|SCUI|SDUI|SAB|TTY|CODE|STR|...
    """
    concepts: Dict[str, UmlsConcept] = {}
    for line in _iter_lines(path):
        parts = list(split_csv_like(line))
        if len(parts) < 15:
            continue
        cui = parts[0]
        lat = parts[1]
        sab = parts[11]
        tty = parts[12]
        term = parts[14]

        if lang_filter and lat != lang_filter:
            continue
        if sab_include is not None and sab not in sab_include:
            continue

        c = concepts.get(cui)
        if c is None:
            c = UmlsConcept(cui=cui)
            concepts[cui] = c

        # preferred term: take first PT or first seen term
        if tty == "PT":
            if c.pref is None:
                c.pref = term
        if term not in c.synonyms:
            c.synonyms.append(term)

    return concepts


def parse_mrdef(
    path: Path,
    concepts: Dict[str, UmlsConcept],
    sab_include: Optional[Set[str]] = None,
) -> None:
    """
    Parse MRDEF.RRF and attach definitions to existing concepts.

    Columns (simplified):
    CUI|AUI|ATUI|SATUI|SAB|DEF|...
    """
    for line in _iter_lines(path):
        parts = list(split_csv_like(line))
        if len(parts) < 6:
            continue
        cui = parts[0]
        sab = parts[4]
        definition = parts[5]

        if sab_include is not None and sab not in sab_include:
            continue

        c = concepts.get(cui)
        if c is None:
            continue
        c.definitions.append(definition)


def parse_mrrel(path: Path, concepts: Dict[str, UmlsConcept]) -> None:
    """
    Parse MRREL.RRF and attach simple parent/child/related relationships.

    Columns (simplified):
    CUI1|AUI1|CUI2|AUI2|CUI3|AUI3|REL|RELA|...  (schema varies by release)
    We primarily use CUI1, CUI2, REL.
    """
    for line in _iter_lines(path):
        parts = list(split_csv_like(line))
        if len(parts) < 7:
            continue
        cui1 = parts[0]
        cui2 = parts[2]
        rel = parts[6]

        c1 = concepts.get(cui1)
        c2 = concepts.get(cui2)
        if c1 is None or c2 is None:
            continue

        if rel in {"PAR"}:
            c1.parents.add(cui2)
            c2.children.add(cui1)
        elif rel in {"CHD"}:
            c1.children.add(cui2)
            c2.parents.add(cui1)
        else:
            c1.related.add(cui2)
            c2.related.add(cui1)


def parse_mrsty(path: Path, concepts: Dict[str, UmlsConcept]) -> None:
    """
    Parse MRSTY.RRF and attach semantic types.

    Columns (simplified):
    CUI|TUI|STN|STY|ATUI|CVF
    """
    for line in _iter_lines(path):
        parts = list(split_csv_like(line))
        if len(parts) < 4:
            continue
        cui = parts[0]
        sty = parts[3]
        c = concepts.get(cui)
        if c is None:
            continue
        c.semantic_types.append(sty)


def load_umls_tables(
    mrconso_path: Path,
    mrdef_path: Optional[Path] = None,
    mrrel_path: Optional[Path] = None,
    mrsty_path: Optional[Path] = None,
    sab_include: Optional[Iterable[str]] = None,
    lang_filter: str = "ENG",
) -> UmlsTables:
    sab_set = set(sab_include) if sab_include is not None else None
    concepts = parse_mrconso(mrconso_path, sab_include=sab_set, lang_filter=lang_filter)

    if mrdef_path is not None and mrdef_path.exists():
        parse_mrdef(mrdef_path, concepts, sab_include=sab_set)
    if mrrel_path is not None and mrrel_path.exists():
        parse_mrrel(mrrel_path, concepts)
    if mrsty_path is not None and mrsty_path.exists():
        parse_mrsty(mrsty_path, concepts)

    return UmlsTables(concepts=concepts)

