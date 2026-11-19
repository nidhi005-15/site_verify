from __future__ import annotations

import re
from typing import Any

NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%?\b")
NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "without", "lack", "lacks", "lacking", "fail", "fails", "failed"}
CONTRAST_WORDS = {"however", "contrary", "contradict", "contradicts", "contradictory", "unlike", "whereas", "refute", "refutes"}
POPULATION_TERMS = {"children", "child", "adults", "adult", "elderly", "patients", "mice", "rats", "in vitro", "in vivo"}


def _extract_numbers(text: str) -> set[str]:
    return set(NUMBER_PATTERN.findall((text or "").lower()))


def analyze_claim_discrepancies(
    claim_text: str,
    evidence_text: str,
    citation_year: int | None = None,
    current_year: int = 2026,
) -> dict[str, Any]:
    claim_l = (claim_text or "").lower()
    ev_l = (evidence_text or "").lower()

    claim_nums = _extract_numbers(claim_l)
    ev_nums = _extract_numbers(ev_l)
    numerical_mismatch = bool(claim_nums and ev_nums and not (claim_nums & ev_nums))

    claim_neg = any(re.search(rf"\b{w}\b", claim_l) for w in NEGATION_WORDS)
    ev_neg = any(re.search(rf"\b{w}\b", ev_l) for w in NEGATION_WORDS)
    has_contrast = any(re.search(rf"\b{w}\b", claim_l) or re.search(rf"\b{w}\b", ev_l) for w in CONTRAST_WORDS)
    contradiction_signal = bool(ev_l and ((claim_neg != ev_neg) or has_contrast))

    claim_pops = {p for p in POPULATION_TERMS if p in claim_l}
    ev_pops = {p for p in POPULATION_TERMS if p in ev_l}
    population_mismatch = bool(claim_pops and ev_pops and not (claim_pops & ev_pops))

    potentially_outdated = bool(citation_year and (current_year - int(citation_year)) >= 10)

    flags: list[str] = []
    if numerical_mismatch:
        flags.append("numerical_discrepancy")
    if contradiction_signal:
        flags.append("potential_contradiction")
    if population_mismatch:
        flags.append("population_or_scope_mismatch")
    if potentially_outdated:
        flags.append("potentially_outdated_source")

    return {
        "flags": flags,
        "numerical_mismatch": numerical_mismatch,
        "claim_numbers": sorted(claim_nums),
        "evidence_numbers": sorted(ev_nums),
        "contradiction_signal": contradiction_signal,
        "population_mismatch": population_mismatch,
        "potentially_outdated": potentially_outdated,
    }
