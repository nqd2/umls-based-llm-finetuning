from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .config import Umls2QaConfig
from .parsers import load_umls_tables
from .build_examples import build_qa_examples, write_qa_jsonl


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert UMLS RRF files into an instruction-style QA dataset (English) for LLM finetuning.",
    )
    parser.add_argument(
        "--umls-dir",
        type=Path,
        required=True,
        help="Directory containing UMLS .RRF files (MRCONSO.RRF, MRDEF.RRF, MRREL.RRF, MRSTY.RRF).",
    )
    parser.add_argument(
        "--out-path",
        type=Path,
        required=True,
        help="Output JSONL file path for QA dataset.",
    )
    parser.add_argument(
        "--sab-include",
        type=str,
        default=None,
        help="Comma-separated list of source vocabularies (SAB) to include, e.g. 'SNOMEDCT_US,ICD10CM'.",
    )
    parser.add_argument(
        "--max-def-per-concept",
        type=int,
        default=2,
        help="Maximum number of definitions to use per concept.",
    )
    parser.add_argument(
        "--max-q-per-concept",
        type=int,
        default=2,
        help="Maximum number of QA pairs to generate per concept.",
    )
    parser.add_argument(
        "--flush-every",
        type=int,
        default=10_000,
        help="Flush to disk every N examples.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)

    sab_include = (
        [s.strip() for s in args.sab_include.split(",") if s.strip()]
        if args.sab_include
        else None
    )

    config = Umls2QaConfig(
        umls_dir=args.umls_dir,
        out_path=args.out_path,
        sab_include=sab_include,
        max_def_per_concept=args.max_def_per_concept,
        max_q_per_concept=args.max_q_per_concept,
        seed=args.seed,
        flush_every=args.flush_every,
    )
    config.validate()

    tables = load_umls_tables(
        mrconso_path=config.mrconso_path,
        mrdef_path=config.mrdef_path,
        mrrel_path=config.mrrel_path,
        mrsty_path=config.mrsty_path,
        sab_include=config.sab_include,
        lang_filter="ENG",
    )

    examples = build_qa_examples(tables, config)
    write_qa_jsonl(examples, config.out_path, flush_every=config.flush_every)


if __name__ == "__main__":
    main()

