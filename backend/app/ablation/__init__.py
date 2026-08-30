"""F9 - the data-gap ablation module.

A tier of its own, beside `engine/` and `ml/` rather than inside either. The
arrow points one way and a test enforces it: `ablation/` reads `engine/`, and
neither `engine/` nor `ml/` may read `ablation/`. Nothing in this package can
reach `engine.score.compute`'s addition, which is the same structural
guarantee CLAUDE.md invariant 1 already has against the ML tier.

What it does: measure what NIGRANI cannot see, and turn that into a ranked,
sourced reporting recommendation addressed to MoSPI's DIID.

What it must never do: invent a value for a field MoSPI does not publish and
score a work as if the field existed. See `measure.py`'s module docstring for
the method that exists to prevent exactly that.
"""
