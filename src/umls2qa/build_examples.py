from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

from .config import Umls2QaConfig
from .parsers import UmlsConcept, UmlsTables


QUESTION_TEMPLATES = [
    "What is {term}?",
    "Explain {term} briefly.",
]


def _pick_terms(concept: UmlsConcept) -> List[str]:
    terms = []
    if concept.pref:
        terms.append(concept.pref)
    for s in concept.synonyms:
        if s not in terms:
            terms.append(s)
    return terms


def build_qa_examples(
    tables: UmlsTables,
    config: Umls2QaConfig,
) -> Iterator[Dict]:
    rng = random.Random(config.seed)
    for cui, concept in tables.concepts.items():
        if not concept.definitions:
            continue
        terms = _pick_terms(concept)
        if not terms:
            continue

        defs = concept.definitions[: config.max_def_per_concept]
        # limit number of questions per concept
        num_q = min(config.max_q_per_concept, len(defs), len(terms))
        if num_q <= 0:
            continue

        for i in range(num_q):
            term = terms[i % len(terms)]
            definition = defs[i % len(defs)]
            template = QUESTION_TEMPLATES[i % len(QUESTION_TEMPLATES)]
            question = template.format(term=term)

            yield {
                "messages": [
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": definition},
                ],
                "meta": {
                    "cui": cui,
                    "source": "UMLS",
                },
            }


def write_qa_jsonl(
    examples: Iterable[Dict],
    out_path: Path,
    flush_every: int = 10_000,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
            count += 1
            if flush_every and count % flush_every == 0:
                f.flush()

