"""Canonicalising the names the portal spells inconsistently.

Three name problems, three different answers:

* **MP names** carry honorifics and term suffixes (`Dr. Ashok Kumar Mittal
  (2022-28) (2022-2028)`, and in the completed exports sometimes `(NaN-NaN)`).
  Stripping both is deterministic and lossless - the raw spelling is kept on
  the row - so it is done in full, with no fuzzy step.

* **Agency names** carry typos that split one office into several strings
  (`DISTRICT MAGISTRAE BUDAUN` beside `DISTRICT MAGISTRATE BUDAUN`). No rule
  can turn a typo into its correct spelling, so this one is fuzzy, and every
  merge is written to `agency_name_variants` for review rather than made
  silently (declared limitation 9).

* **Vendor names** are normalised for case and spacing only. They are not
  fuzzy-merged: a vendor's share of an agency's disbursement drives a rule that
  contributes points, and merging two similarly-named firms would manufacture
  concentration that does not exist. Splitting one firm across two spellings
  understates a finding; merging two firms invents one. The first error is the
  safe one.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from rapidfuzz import fuzz, process

from app.constants import (
    AGENCY_FUZZY_FLOOR,
    IDA_PATTERN,
    IDA_SUFFIX_PATTERN,
    MP_TERM_SUFFIX_PATTERN,
    MP_TITLE_PREFIXES,
)

_TERM_SUFFIX_RE = re.compile(MP_TERM_SUFFIX_PATTERN, re.IGNORECASE)
_TERM_YEARS_RE = re.compile(r"\(\s*(\d{4})\s*-\s*(\d{2,4})\s*\)")
_TITLE_RE = re.compile(
    r"^(?:" + "|".join(MP_TITLE_PREFIXES) + r")\.?\s+",
    re.IGNORECASE,
)
_IDA_RE = re.compile(IDA_PATTERN, re.DOTALL)
_IDA_SUFFIX_RE = re.compile(IDA_SUFFIX_PATTERN, re.IGNORECASE)
_NON_NAME_RE = re.compile(r"[^A-Za-z ]+")
_WHITESPACE_RE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# MP names
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NormalisedMPName:
    """A published MP name split into its join key and its term."""

    name_canon: str
    term_start: int | None
    term_end: int | None


def normalize_mp_name(raw: object) -> NormalisedMPName:
    """Strip honorifics and term suffixes down to the allocation join key.

    `Dr. Ashok Kumar Mittal (2022-28) (2022-2028)` -> `ASHOK KUMAR MITTAL`,
    term 2022-2028. `Shri Javed Ali Khan (2022-28) (NaN-NaN)` -> the same
    treatment with the `NaN-NaN` suffix discarded and no term recorded, because
    a term the portal declined to state is not a term of zero length.

    Punctuation is dropped rather than kept, because the same member appears as
    `S. Jagathrakshakan` and `S Jagathrakshakan` in different exports.
    """
    text = str(raw).strip()

    term_start: int | None = None
    term_end: int | None = None
    for match in _TERM_YEARS_RE.finditer(text):
        start = int(match.group(1))
        end_text = match.group(2)
        # `(2022-28)` and `(2022-2028)` are the same term written twice; the
        # four-digit spelling is preferred where both appear.
        end = int(end_text) if len(end_text) == 4 else start - start % 100 + int(end_text)
        if term_end is None or len(end_text) == 4:
            term_start, term_end = start, end

    text = _TERM_SUFFIX_RE.sub("", text).strip()

    previous = None
    while previous != text:
        previous = text
        text = _TITLE_RE.sub("", text).strip()

    text = _NON_NAME_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text).strip().upper()
    return NormalisedMPName(name_canon=text, term_start=term_start, term_end=term_end)


# ---------------------------------------------------------------------------
# States, districts, constituencies, vendors
# ---------------------------------------------------------------------------


def normalize_state(raw: object) -> str | None:
    """Title-case spelling with collapsed whitespace, or None if blank."""
    text = _WHITESPACE_RE.sub(" ", str(raw).strip())
    return text or None


def normalize_district(raw: object) -> str | None:
    """Uppercase with collapsed whitespace. The portal writes districts in caps."""
    text = _WHITESPACE_RE.sub(" ", str(raw).strip()).upper()
    return text or None


def normalize_constituency(raw: object) -> str | None:
    text = _WHITESPACE_RE.sub(" ", str(raw).strip()).upper()
    return text or None


def normalize_vendor_name(raw: object) -> str | None:
    """Case and spacing only. Deliberately not fuzzy - see the module docstring."""
    text = _WHITESPACE_RE.sub(" ", str(raw).strip()).upper()
    return text or None


def normalize_description(raw: object) -> str | None:
    """Lowercased, punctuation-free, single-spaced.

    Used as the blocking key for duplicate description clusters. Kept here
    rather than in the ML layer because ingest and the duplicate detector must
    agree on what "the same description" means, and invariant 7 says a shared
    definition lives in one place.
    """
    text = re.sub(r"[^a-z0-9 ]+", " ", str(raw).lower())
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text or None


# ---------------------------------------------------------------------------
# Agencies
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SplitIDA:
    """The `IDA` column parsed into its two published parts."""

    district: str | None
    agency_raw: str | None


def split_ida(raw: object) -> SplitIDA:
    """`GHAZIABAD(DISTRICT MAGISTRAE GHAZIABAD_IDA)` -> district, agency.

    The portal publishes the district outside the bracket and the office inside
    it, with a `_IDA` suffix that is a portal artefact rather than part of the
    office's name. A few rows carry `_5` instead, and a few omit the bracket
    entirely; those keep the whole string as the agency and record no district.
    """
    text = str(raw).strip()
    if not text:
        return SplitIDA(district=None, agency_raw=None)
    match = _IDA_RE.match(text)
    if match is None:
        return SplitIDA(district=None, agency_raw=text)
    district = normalize_district(match.group(1))
    agency = _IDA_SUFFIX_RE.sub("", match.group(2)).strip()
    return SplitIDA(district=district, agency_raw=agency or None)


def normalize_agency_name(raw: object) -> str | None:
    """Uppercase, punctuation-free, single-spaced. The fuzzy comparison key."""
    text = re.sub(r"[^A-Za-z0-9 ]+", " ", str(raw))
    text = _WHITESPACE_RE.sub(" ", text).strip().upper()
    return text or None


@dataclass
class AgencyRecord:
    """One canonical agency, with the raw strings that folded into it."""

    district: str | None
    name_canon: str
    variants: list[tuple[str, str, float]] = field(default_factory=list)
    # Which state the rows referencing this office said they were in. The
    # portal's `State` column describes the work's member, not the office, and
    # on 70 of the 758 published offices it disagrees with itself - `AGRA
    # (DISTRICT MAGISTRAE AGRA_IDA)` is filed under five different states.
    # The office is one office; the column is noisy. Majority wins, and the
    # spread is visible here rather than silently splitting the agency.
    state_votes: Counter = field(default_factory=Counter)

    @property
    def key(self) -> tuple[str, str]:
        return (self.district or "", self.name_canon)

    @property
    def state(self) -> str | None:
        return self.state_votes.most_common(1)[0][0] if self.state_votes else None

    @property
    def variant_count(self) -> int:
        return len(self.variants)

    @property
    def merge_confidence(self) -> float | None:
        """The weakest merged variant's score, or None when nothing was merged.

        None is not the same statement as a low score: it says no fuzzy
        decision was taken at all.
        """
        fuzzy = [score for _, matched_by, score in self.variants if matched_by == "fuzzy"]
        return min(fuzzy) if fuzzy else None


class AgencyCanonicaliser:
    """Folds raw agency strings into canonical agencies, and shows its working.

    Exact match first: two rows whose normalised agency names are identical are
    the same office and no judgement is involved.

    Then fuzzy, blocked on **district**. The district is published separately,
    inside the same IDA column as the office name, so blocking on it costs
    nothing and buys a great deal: the comparison only ever has to separate a
    typo from a genuinely different office *inside one district*, where
    `DISTRICT MAGISTRATE` against `DISTRICT PLANNING OFFICER` is an easy
    rejection and `DISTRICT MAGISTRAE` against `DISTRICT MAGISTRATE` is an easy
    acceptance. Without the block, `DISTRICT MAGISTRATE AGRA` and
    `DISTRICT MAGISTRATE ARA` - two real and different offices - sit above any
    threshold that would still catch the typo.

    The block is district and **not** (state, district), because the `State`
    column is not part of the office's identity and demonstrably disagrees with
    the IDA: one Agra district magistrate is filed under five states across the
    corpus. Blocking on state as well would split that office five ways and
    quietly divide its duplicate clusters and vendor concentration by five.

    The floor is `token_sort_ratio >= AGENCY_FUZZY_FLOOR` (90). At 90 a single
    dropped character in a name of ten or more characters still merges, while
    two offices differing by a whole word do not. Every merge is recorded with
    its score in `agency_name_variants`, marked unreviewed, so an officer who
    disputes one can see exactly what was folded into what.
    """

    def __init__(self, floor: float = AGENCY_FUZZY_FLOOR) -> None:
        self.floor = floor
        self._records: dict[tuple[str, str], AgencyRecord] = {}
        # district -> canonical names already seen in it.
        self._by_block: dict[str, list[str]] = {}
        # (district, raw string) -> the record it resolved to, so a repeated
        # string is resolved once rather than re-scored 30,000 times.
        self._resolved: dict[tuple[str, str], AgencyRecord] = {}

    def resolve(self, state: str | None, district: str | None, agency_raw: str):
        """Return the canonical agency for one raw string, creating it if new."""
        name_canon = normalize_agency_name(agency_raw)
        if not name_canon:
            return None

        block = district or ""
        cache_key = (block, agency_raw)
        cached = self._resolved.get(cache_key)
        if cached is not None:
            if state:
                cached.state_votes[state] += 1
            return cached

        existing = self._by_block.setdefault(block, [])

        record = None
        if name_canon in existing:
            record = self._records[(block, name_canon)]
            self._record_variant(record, agency_raw, "exact", 100.0)
        else:
            match = process.extractOne(
                name_canon, existing, scorer=fuzz.token_sort_ratio, score_cutoff=self.floor
            )
            if match is not None:
                matched_name, score, _ = match
                record = self._records[(block, matched_name)]
                self._record_variant(record, agency_raw, "fuzzy", float(score))
            else:
                record = AgencyRecord(district=district, name_canon=name_canon)
                self._records[record.key] = record
                existing.append(name_canon)
                self._record_variant(record, agency_raw, "exact", 100.0)

        if state:
            record.state_votes[state] += 1
        self._resolved[cache_key] = record
        return record

    @staticmethod
    def _record_variant(
        record: AgencyRecord, name_raw: str, matched_by: str, score: float
    ) -> None:
        """Append the raw string once. `name_raw` is unique within one agency."""
        if any(existing == name_raw for existing, _, _ in record.variants):
            return
        record.variants.append((name_raw, matched_by, score))

    def records(self) -> list[AgencyRecord]:
        return list(self._records.values())

    def fuzzy_merge_count(self) -> int:
        """How many raw strings were folded by a fuzzy decision, not an exact one."""
        return sum(
            1
            for record in self._records.values()
            for _, matched_by, _ in record.variants
            if matched_by == "fuzzy"
        )
