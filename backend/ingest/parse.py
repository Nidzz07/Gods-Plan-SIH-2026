"""Turning portal strings into work ids, amounts and dates.

Every function here returns the parsed value together with an `Availability`,
because the caller has to be able to tell three things apart:

* the portal published a value                -> `published`
* the portal published the value zero         -> `published_zero`
* the portal published nothing, or `N/A`      -> `not_published`

Collapsing the last two into "null" is the single mistake CLAUDE.md invariant 2
exists to prevent: a work with a real zero payment and a work whose payment was
never exported would look identical, and a reporting gap would read as a clean
record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from app.constants import (
    Availability,
    NULL_TOKENS,
    RAW_DATE_FORMAT,
    WORK_ID_PATTERN,
    canonical_work_id,
)

_WORK_ID_RE = re.compile(WORK_ID_PATTERN)


@dataclass(frozen=True)
class ParsedWorkId:
    """A work id broken into the parts the model needs."""

    canon: str
    mp_code: str
    fy: str
    serial: str


def is_null_token(raw: object) -> bool:
    """True for the strings the portal writes where it has nothing to say."""
    return str(raw).strip().upper() in NULL_TOKENS


def parse_work_id(raw: object) -> ParsedWorkId | None:
    """Extract `WS/MP{code}/{FY}/{serial}` from a `Work` or `Work ID` cell.

    In Recommended, Sanctioned and Completed the id sits at the start of the
    cell and is followed by a hyphen and the category text; in Expenditure it
    has a column to itself. Both are handled by anchoring the pattern at the
    start and ignoring whatever follows.

    All whitespace is stripped before matching, because some Lok Sabha rows
    carry a literal tab inside the id (`WS/<TAB> MP620/2024-2025/133166`), and
    those are the same work as the untabbed spelling. 5.3% of
    Works_Recommended_lok_sabha rows read literally `NA-<category>` and have no
    id at all; they return None and become an `ingest_rejects` row.
    """
    if raw is None:
        return None
    canon = canonical_work_id(raw)
    match = _WORK_ID_RE.match(canon)
    if match is None:
        return None
    return ParsedWorkId(
        canon=match.group(1),
        mp_code=match.group(2),
        fy=match.group(3),
        serial=match.group(4),
    )


def raw_work_id_prefix(raw: object, canon: str) -> str:
    """The published spelling of the id, whitespace and tabs intact.

    The cell reads `WS/<TAB> MP620/2024-2025/133166-Construction of ...`, so the
    id cannot be recovered by splitting on the hyphen - the financial year
    contains two of its own. Instead the raw string is walked until as many
    non-whitespace characters have been consumed as the canonical id has, and
    everything up to that point is returned exactly as published. That is what
    `works.work_id_raw` shows an officer beside the canonical form.
    """
    text = str(raw)
    wanted = len(canon)
    seen = 0
    for index, character in enumerate(text):
        if not character.isspace():
            seen += 1
            if seen == wanted:
                return text[: index + 1]
    return text.strip()


def parse_amount(raw: object) -> tuple[int | None, Availability]:
    """Parse a rupee amount to whole rupees.

    Amounts arrive as plain integer strings, but the allocation export carries
    two decimal places on some rows (`158176083.11`) and the portal's own
    footer rows use Indian digit grouping (`40,79,58,27,851.08`). Commas are
    stripped and the value is rounded to whole rupees: MPLADS is administered
    in rupees, every threshold in the rulebook is a percentage or a count, and
    carrying paise would put a spurious two digits on every figure an officer
    reads.

    A real zero returns `published_zero`, never `not_published`.
    """
    if raw is None or is_null_token(raw):
        return None, Availability.NOT_PUBLISHED
    text = str(raw).strip().replace(",", "")
    try:
        value = int(round(float(text)))
    except ValueError:
        return None, Availability.NOT_PUBLISHED
    if value == 0:
        return 0, Availability.PUBLISHED_ZERO
    return value, Availability.PUBLISHED


def looks_like_amount(raw: object) -> bool:
    """True when a cell holds something numeric.

    Used only to tell a genuinely unparseable amount apart from an absent one,
    so the reject reason is `unparseable_amount` rather than a silent null.
    """
    if raw is None or is_null_token(raw):
        return False
    text = str(raw).strip().replace(",", "")
    try:
        float(text)
    except ValueError:
        return False
    return True


def parse_date(raw: object) -> tuple[date | None, Availability]:
    """Parse `%d-%b-%Y`, e.g. `08-Jul-2024`.

    There is no `published_zero` for a date: a date is either published or it
    is not. Anything that fails to parse returns `not_published` and the caller
    decides whether that warrants a reject row.
    """
    if raw is None or is_null_token(raw):
        return None, Availability.NOT_PUBLISHED
    text = str(raw).strip()
    try:
        return datetime.strptime(text, RAW_DATE_FORMAT).date(), Availability.PUBLISHED
    except ValueError:
        return None, Availability.NOT_PUBLISHED


def looks_like_date(raw: object) -> bool:
    """True when a cell holds text that was meant to be a date but is not one."""
    if raw is None or is_null_token(raw):
        return False
    try:
        datetime.strptime(str(raw).strip(), RAW_DATE_FORMAT)
    except ValueError:
        return True
    return False


def parse_text(raw: object) -> tuple[str | None, Availability]:
    """Trim a free-text field, mapping the portal's null tokens to None.

    There is no zero-valued analogue for free text, so the only two outcomes
    are `published` and `not_published`. The companion is returned anyway so
    that a caller storing a description can record *why* it is missing without
    re-deriving that from the null itself.
    """
    if raw is None or is_null_token(raw):
        return None, Availability.NOT_PUBLISHED
    return str(raw).strip(), Availability.PUBLISHED


def parse_fy_start_year(fy: str) -> int | None:
    """`2024-2025` -> 2024. Used to order financial years without sorting text."""
    match = re.match(r"^(\d{4})-\d{4}$", str(fy).strip())
    return int(match.group(1)) if match else None
