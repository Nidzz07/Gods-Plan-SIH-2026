"""The NIGRANI detection engine.

    derive.py    F1  the two ladders and the derived feature dictionary
    rulebook.py  F2  the YAML rulebook, loaded from disk on every evaluation
    score.py     F3 + F5  composite score, reasoning trace, coverage
    memo.py          the plain-language memo - a TEMPLATE, never a model
    audit.py     F6  the append-only, hash-chained trail and true recompute

F4's corroboration bonus lives in `score.corroboration`, fed a count the caller
resolves over the corpus. The ML tier (F7) is Phase 4 and lands in `app/ml/`;
nothing it produces can reach the score (CLAUDE.md invariant 1).
"""
