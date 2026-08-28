"""The reject ledger. Nothing leaves ingestion without a row in here.

CLAUDE.md invariant 11: ingestion never silently drops a row. For all twelve
files, `loaded + rejected` must equal the rows in the file, and `run.py`
asserts it rather than printing it hopefully.

The reason is a closed enum (`app.constants.RejectReason`). A new failure mode
gets a new member and a line in the profile; it never gets a free-text string,
because a reason nobody can count is a reason nobody will fix.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime

from app.constants import RejectReason


class RejectCollector:
    """Accumulates rejects in memory, then writes them in one insert.

    Held in memory rather than written row by row because the two Recommended
    files alone contribute over two thousand rejects, and a per-row insert
    would dominate the run.
    """

    def __init__(self) -> None:
        self._rows: list[dict] = []
        self._per_file: dict[str, Counter] = defaultdict(Counter)

    def add(
        self,
        source_file: str,
        row_number: int,
        raw_row: dict,
        reason: RejectReason,
        detail: str | None = None,
    ) -> None:
        """Record one refused row, with the source line kept verbatim."""
        self._rows.append(
            {
                "source_file": source_file,
                "row_number": int(row_number),
                # JSON so the original text survives commas, quotes and the
                # portal's own digit grouping without being re-parsed.
                "raw_row": json.dumps(raw_row, ensure_ascii=False, default=str),
                "reason": reason.value,
                "detail": detail,
                "at": datetime.utcnow(),
            }
        )
        self._per_file[source_file][reason.value] += 1

    def rows(self) -> list[dict]:
        return self._rows

    def count_for_file(self, source_file: str) -> int:
        return sum(self._per_file[source_file].values())

    def reasons_for_file(self, source_file: str) -> Counter:
        return self._per_file[source_file]

    def totals_by_reason(self) -> Counter:
        totals: Counter = Counter()
        for counts in self._per_file.values():
            totals.update(counts)
        return totals

    def __len__(self) -> int:
        return len(self._rows)


def raw_row_of(row) -> dict:
    """The source row as a plain dict, without the loader's bookkeeping columns."""
    return {
        key: value
        for key, value in dict(row).items()
        if not str(key).startswith("_")
    }
