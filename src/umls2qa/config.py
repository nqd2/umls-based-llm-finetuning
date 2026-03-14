from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence


@dataclass
class Umls2QaConfig:
    umls_dir: Path
    out_path: Path

    sab_include: Optional[Sequence[str]] = None
    max_def_per_concept: int = 2
    max_q_per_concept: int = 2
    seed: int = 42

    # I/O chunking
    flush_every: int = 10_000

    def validate(self) -> None:
        if not self.umls_dir.is_dir():
            raise ValueError(f"UMLS dir not found: {self.umls_dir}")
        if not self.out_path.parent.exists():
            self.out_path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def mrconso_path(self) -> Path:
        return self.umls_dir / "MRCONSO.RRF"

    @property
    def mrdef_path(self) -> Path:
        return self.umls_dir / "MRDEF.RRF"

    @property
    def mrrel_path(self) -> Path:
        return self.umls_dir / "MRREL.RRF"

    @property
    def mrsty_path(self) -> Path:
        return self.umls_dir / "MRSTY.RRF"


def split_csv_like(line: str, sep: str = "|") -> Iterable[str]:
    # UMLS uses '|' as separator, last field ends with '|'
    parts = line.rstrip("\n").split(sep)
    # drop trailing empty after last '|'
    if parts and parts[-1] == "":
        parts = parts[:-1]
    return parts

