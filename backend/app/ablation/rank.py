"""Ranking the fields. One criterion, named, and no composite score.

**The criterion: total unrealised rulebook weight, measured.**

For each field, the sum over the corpus of the weights of every rule that is
skipped because that field is absent. It is a count of points, produced by
adding up trace rows the engine actually wrote. Nothing in it is estimated,
weighted, normalised or combined with anything else.

**Why this one and not the other two candidates.**

*Against works affected.* A works count treats every affected work the same
whether the field costs it 10 points of evidence or 50. On this corpus that is
not a hypothetical difference: `expenditure_linkage` affects 23,549 works and
`asset_image_publication_scope` affects 14,104, a ratio of 1.7 - but the first
leaves 1,177,450 points of rulebook weight unrealised against the second's
141,040, a ratio of 8.3. Ranking on works would understate the first gap by a
factor of five, because it counts how many cases were touched rather than how
much of the case was lost.

*Against coverage uplift.* Coverage uplift is the same quantity divided by
`RULE_WEIGHT_TOTAL x corpus works`, so it is a monotone transform of the
criterion and produces an identical ordering - up to `engine.score.coverage_pct`
rounding each case to a whole percent, which moves the corpus mean by a few
hundredths of a point and no ordering at all. It is reported beside every field
because it is the number an officer reads on a case sheet. It is not a second
criterion, because dividing by a constant is not a second opinion.

*And why the criterion is denominated in rulebook points.* The question MoSPI
is actually being asked is "if we publish this, how much more of your rulebook
can you run?". Points are the unit that question is asked in, and the unit
every case in the product already displays.

**The criterion does not separate seven of the nine fields, and this module
does not invent a separator.**

Seven fields measure exactly zero, because rulebook v1.0.0 contains no rule
that reads them: a rule that was never written cannot be skipped
(`fields.py`). They are therefore TIED, and they are reported as tied - listed
in the order `DATA-PROFILE.md` section 8 lists them, which carries no implied
priority, and each carrying its own measured corroborating figures.

Those corroborating figures are real, and they are deliberately NOT folded into
a tiebreak. They are not commensurable: 8,481 works whose asset-evidence pass
rests on an unverifiable binary, 3,240 works inside an exact-repetition
cluster, and 14,831 works with no second cost figure are three different
quantities counted over three different populations, and any formula that
ordered them against one another would be arithmetic invented for the purpose
of producing a ranking. A tie honestly reported is worth more to MoSPI than an
ordering nobody can re-derive, which is the same standard CLAUDE.md invariant 6
holds every threshold in this project to.

A tie among fields with a NON-zero measurement would be reported the same way,
and the code below does not special-case zero to reach that behaviour. On this
corpus no such tie occurs.
"""

from __future__ import annotations

from dataclasses import dataclass

RANKING_CRITERION = "total unrealised rulebook weight, measured"

RANKING_CRITERION_DETAIL = (
    "The sum over the corpus of the weight of every rulebook rule that is skipped because "
    "this field is absent. Counted from the skip reasons the engine recorded, not "
    "estimated. Coverage uplift is this quantity divided by a constant and gives the same "
    "ordering; works affected gives a different and worse one, because it counts cases "
    "touched rather than evidence lost."
)

TIE_NOTE_NO_RULE = (
    "Unranked. This field's absence leaves zero points of the current rulebook "
    "unrealised, because no rule in rulebook v1.0.0 reads it - a rule that was never "
    "written cannot be skipped. The criterion does not separate the fields in this group "
    "and no substitute criterion is invented to do so."
)

TIE_NOTE_EQUAL = (
    "Tied on the ranking criterion with the other fields sharing this rank. The criterion "
    "does not separate them and no substitute criterion is invented to do so."
)


@dataclass(frozen=True)
class RankedField:
    """One measurement with its place in the order, or with none.

    `position` is None exactly when the field is unranked - either because it
    measures zero on the criterion, or because it ties with another field. The
    `note` says which, so a null is never read as a missing measurement.
    """

    measurement: object
    position: int | None
    note: str

    @property
    def key(self) -> str:
        return self.measurement.field.key


def criterion(measurement) -> int:
    """The single ranking quantity. One line, so it cannot hide a blend."""
    return measurement.unrealised_weight


def rank(measurements) -> tuple:
    """Order the measurements by the criterion. Ties stay ties.

    Fields measuring zero keep their declaration order, which is
    `DATA-PROFILE.md` section 8's own order, so the listing implies no priority
    the measurement did not find.
    """
    scored = [m for m in measurements if criterion(m) > 0]
    unscored = [m for m in measurements if criterion(m) == 0]

    ranked = []
    position = 0
    index = 0
    ordered = sorted(scored, key=criterion, reverse=True)
    while index < len(ordered):
        value = criterion(ordered[index])
        tied = [m for m in ordered[index:] if criterion(m) == value]
        position += 1
        for measurement in tied:
            ranked.append(
                RankedField(
                    measurement=measurement,
                    position=position if len(tied) == 1 else None,
                    note="" if len(tied) == 1 else TIE_NOTE_EQUAL,
                )
            )
        index += len(tied)

    ranked.extend(
        RankedField(measurement=measurement, position=None, note=TIE_NOTE_NO_RULE)
        for measurement in unscored
    )
    return tuple(ranked)
