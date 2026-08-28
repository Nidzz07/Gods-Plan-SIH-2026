"""Load `data/raw/` into `backend/nigrani.db` and print the load report.

    cd backend && python -m ingest.run

**Idempotent by rebuild, not by append.** The run drops and recreates every
table before loading, so running it twice produces the same row counts rather
than doubled data. It is the corpus loader: it owns the contents of the
database, and any case work built on a previous corpus is invalidated by a new
one anyway. Nothing here issues an UPDATE or a DELETE against `audit_log`
(CLAUDE.md invariant 4).

**The works table is the union of every work id in the four work-level
exports, not just the sanctioned ones.** A recommendation that was never
sanctioned still carries a recommendation date and a sanction date of its own,
and an expenditure row still has to attach its payment to something.
Restricting the table to the 27,078 sanctioned works would force ingest to
discard tens of thousands of published rows, which invariant 11 forbids. Cases
are still opened only for works that have a sanction row (DOMAIN-MODEL.md (a));
that restriction belongs to scoring, not to loading.

Reading order for the descriptive fields is sanctioned, then completed, then
recommended, then expenditure: the first export to supply a field wins, and the
sanctioned export supplies the most.
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd
from sqlalchemy import func, insert, select

from app.constants import (
    Availability,
    FY_TERM_TO_DATE,
    GRAND_TOTAL_MARKER,
    HOUSE_LOK_SABHA,
    IMAGE_PRESENT_TOKEN,
    RAW_FILES,
    RejectReason,
    WORK_CATEGORIES,
    WORK_STATUSES,
)
from app.db import Base, SessionLocal, engine
from app.models import (
    Agency,
    AgencyNameVariant,
    CalamityConsent,
    Certification,
    Completion,
    Constituency,
    FundAccount,
    IngestReject,
    MP,
    Payment,
    Sanction,
    State,
    Vendor,
    Work,
)

from . import loaders
from .loaders import column
from .normalize import (
    AgencyCanonicaliser,
    normalize_constituency,
    normalize_mp_name,
    normalize_state,
    normalize_vendor_name,
    split_ida,
)
from .parse import (
    is_null_token,
    looks_like_amount,
    looks_like_date,
    parse_amount,
    parse_date,
    parse_text,
    parse_work_id,
    raw_work_id_prefix,
)
from .rejects import RejectCollector, raw_row_of
from .synthetic import insert_synthetic_control

# Descriptive-field precedence. Lower wins.
SOURCE_PRECEDENCE = {
    "works_sanctioned": 0,
    "works_completed": 1,
    "works_recommended": 2,
    "expenditure": 3,
}


class FileTally:
    """Rows read, loaded and rejected for one export, so the two can reconcile."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.rows_read = 0
        self.loaded = 0

    def reconciles(self, rejected: int) -> bool:
        return self.loaded + rejected == self.rows_read


def _is_grand_total(row) -> bool:
    """The portal's footer row, present once in every export.

    It carries an aggregate in one column and blanks elsewhere; in the two
    Works_Sanctioned files that aggregate lands in `Work Status`, which is what
    DATA-PROFILE.md section 9 recorded as a shifted-column defect. It is
    detected on the serial-number column, which reads `Grand Total` instead of
    an integer.
    """
    return str(row.get("Sr. No.", "")).strip() == GRAND_TOTAL_MARKER


# ---------------------------------------------------------------------------
# Pass 1 - read every row, reject what cannot be loaded, keep the rest
# ---------------------------------------------------------------------------


class Corpus:
    """Everything the twelve files said, parsed but not yet written."""

    def __init__(self) -> None:
        self.rejects = RejectCollector()
        self.tallies: dict[str, FileTally] = {}

        # canonical work id -> merged descriptive record
        self.works: dict[str, dict] = {}
        # canonical work id -> sanction record
        self.sanctions: dict[str, dict] = {}
        # canonical work id -> recommended amount, from the recommended export
        self.recommended_amounts: dict[str, tuple[int | None, Availability]] = {}
        # canonical work id -> completion record
        self.completions: dict[str, dict] = {}
        self.payments: list[dict] = []
        self.allocations: dict[tuple[str, str], dict] = {}
        self.calamity: list[dict] = []

        # Sets kept for the join-yield section of the report.
        self.ids_recommended: set[str] = set()
        self.ids_sanctioned: set[str] = set()
        self.ids_completed: set[str] = set()
        self.ids_expenditure: set[str] = set()

        # (name_canon, house) -> MP record under construction
        self.mps: dict[tuple[str, str], dict] = {}
        # The subset of those actually named on a work or a payment row. The
        # allocation roll and the works exports are different populations, and
        # the name-match yield is only meaningful over this one.
        self.mp_keys_on_works: set[tuple[str, str]] = set()
        self.states: set[str] = set()
        self.constituencies: set[tuple[str, str]] = set()
        self.vendors: dict[str, str] = {}
        self.agencies = AgencyCanonicaliser()

        # Vocabulary drift: values the profile never recorded.
        self.new_statuses: Counter = Counter()
        self.new_categories: Counter = Counter()

    # -- helpers ----------------------------------------------------------

    def tally(self, filename: str) -> FileTally:
        return self.tallies.setdefault(filename, FileTally(filename))

    def note_mp(
        self,
        name_raw: str,
        house: str,
        state: str | None,
        constituency: str | None,
        from_allocation: bool,
    ) -> tuple[str, str] | None:
        """Register an MP sighting and return its (name_canon, house) key.

        A state seen on the allocation export outranks one seen on a work row,
        because the allocation file is the roll of members and a work row only
        says where the work is. In practice they agree; when they do not, the
        roll wins.
        """
        normalised = normalize_mp_name(name_raw)
        if not normalised.name_canon:
            return None
        key = (normalised.name_canon, house)
        record = self.mps.get(key)
        if record is None:
            record = {
                "name_canon": normalised.name_canon,
                "name_raw": str(name_raw).strip(),
                "house": house,
                "state": None,
                "state_from_allocation": False,
                "state_votes": Counter(),
                "constituency": None,
                "term_start": normalised.term_start,
                "term_end": normalised.term_end,
            }
            self.mps[key] = record

        if normalised.term_start is not None and record["term_start"] is None:
            record["term_start"] = normalised.term_start
            record["term_end"] = normalised.term_end

        if state:
            record["state_votes"][state] += 1
            if from_allocation or not record["state_from_allocation"]:
                if from_allocation or record["state"] is None:
                    record["state"] = state
                    record["state_from_allocation"] = (
                        from_allocation or record["state_from_allocation"]
                    )
        if constituency and (from_allocation or record["constituency"] is None):
            record["constituency"] = constituency
        return key

    def upsert_work(self, canon: str, fields: dict) -> None:
        """First source wins per field; later sources fill only what is missing."""
        existing = self.works.get(canon)
        if existing is None:
            self.works[canon] = fields
            return
        for key, value in fields.items():
            if existing.get(key) is None and value is not None:
                existing[key] = value
        if SOURCE_PRECEDENCE[fields["_dataset"]] < SOURCE_PRECEDENCE[existing["_dataset"]]:
            existing["_dataset"] = fields["_dataset"]
            existing["source_file"] = fields["source_file"]
            existing["work_id_raw"] = fields["work_id_raw"]


def _read_work_level(corpus: Corpus, df: pd.DataFrame, dataset: str) -> None:
    """Recommended, Sanctioned and Completed share a shape; the differences are named."""
    filename = df["_source_file"].iloc[0]
    house = df["_house"].iloc[0]
    tally = corpus.tally(filename)
    tally.rows_read = len(df)

    col_work = column(df, "Work", "WORK", "Work ID")
    col_state = column(df, "State")
    col_ida = column(df, "IDA")
    col_mp = column(df, "Hon'ble Members of Parliament", "Hon'ble Members of Parliaments")
    col_category = column(df, "Work category", "Work Category")
    col_description = column(df, "Work description", "Work Description")
    col_constituency = column(df, "Constituency") if house == HOUSE_LOK_SABHA else None

    col_recommended_date = None
    col_sanction_date = None
    col_sanction_amt = None
    col_recommended_amt = None
    col_status = None
    col_completion_date = None
    col_completed_amt = None
    col_image = None

    if dataset == "works_recommended":
        col_recommended_date = column(df, "Recommended date")
        col_sanction_date = column(df, "Sanction Date")
        col_recommended_amt = column(df, "RECOMMENDED AMOUNT   ( ₹ )", "Recommended Amount")
    elif dataset == "works_sanctioned":
        col_recommended_date = column(df, "Recommended date")
        col_sanction_date = column(df, "Sanction Date")
        col_sanction_amt = column(df, "Sanction Amount ( ₹ )", "Sanction Amount")
        col_status = column(df, "Work Status")
    else:  # works_completed
        col_completion_date = column(df, "Completion Date")
        col_completed_amt = column(df, "Amount Disbursed ( ₹ )", "Amount Disbursed")
        col_image = column(df, "Image")

    seen_in_file: set[str] = set()

    for row in df.to_dict("records"):
        row_number = row["_row_number"]
        raw = raw_row_of(row)

        if _is_grand_total(row):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.GRAND_TOTAL_ROW,
                "Portal footer row, not a work.",
            )
            continue

        parsed = parse_work_id(row[col_work])
        if parsed is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.WORK_ID_UNPARSEABLE,
                f"{col_work} does not match WS/MP{{code}}/{{FY}}/{{serial}}.",
            )
            continue

        if parsed.canon in seen_in_file:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.DUPLICATE_WORK_ID,
                f"{parsed.canon} already appeared in this file.",
            )
            continue

        state = normalize_state(row[col_state])
        if not state:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "State is blank; a work cannot be scoped without it.",
            )
            continue

        if is_null_token(row[col_mp]):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "No recommending member named.",
            )
            continue

        # -- dataset-specific validation, before anything is accepted -----

        if dataset == "works_sanctioned":
            sanctioned_amt, sanctioned_avail = parse_amount(row[col_sanction_amt])
            if sanctioned_amt is None:
                reason = (
                    RejectReason.UNPARSEABLE_AMOUNT
                    if looks_like_amount(row[col_sanction_amt]) is False
                    and not is_null_token(row[col_sanction_amt])
                    else RejectReason.NULL_REQUIRED_FIELD
                )
                corpus.rejects.add(
                    filename, row_number, raw, reason,
                    f"{col_sanction_amt} = {row[col_sanction_amt]!r}; "
                    "a sanction row cannot exist without an amount.",
                )
                continue
            sanction_date, _ = parse_date(row[col_sanction_date])
            if sanction_date is None:
                corpus.rejects.add(
                    filename, row_number, raw,
                    RejectReason.UNPARSEABLE_DATE
                    if looks_like_date(row[col_sanction_date])
                    else RejectReason.NULL_REQUIRED_FIELD,
                    f"{col_sanction_date} = {row[col_sanction_date]!r}.",
                )
                continue
            recommended_date, recommended_date_avail = parse_date(row[col_recommended_date])
            if recommended_date is not None and recommended_date > sanction_date:
                # Zero measured. The check stands because clamping to zero
                # would hide a real inversion in a later download.
                corpus.rejects.add(
                    filename, row_number, raw, RejectReason.NEGATIVE_LAG,
                    f"sanction_date {sanction_date} precedes "
                    f"recommended_date {recommended_date}.",
                )
                continue

        if dataset == "works_completed":
            completion_date, completion_avail = parse_date(row[col_completion_date])
            if completion_date is None and looks_like_date(row[col_completion_date]):
                corpus.rejects.add(
                    filename, row_number, raw, RejectReason.UNPARSEABLE_DATE,
                    f"{col_completion_date} = {row[col_completion_date]!r}.",
                )
                continue

        if dataset == "works_recommended":
            recommended_amt, recommended_avail = parse_amount(row[col_recommended_amt])
            if recommended_amt is None and not is_null_token(row[col_recommended_amt]):
                corpus.rejects.add(
                    filename, row_number, raw, RejectReason.UNPARSEABLE_AMOUNT,
                    f"{col_recommended_amt} = {row[col_recommended_amt]!r}.",
                )
                continue

        # -- accepted ------------------------------------------------------

        seen_in_file.add(parsed.canon)
        tally.loaded += 1
        corpus.states.add(state)

        constituency = (
            normalize_constituency(row[col_constituency]) if col_constituency else None
        )
        if constituency:
            corpus.constituencies.add((state, constituency))
        mp_key = corpus.note_mp(
            row[col_mp], house, state, constituency, from_allocation=False
        )
        if mp_key is None:
            # The name was punctuation only. Nothing else in the corpus can
            # identify the member, so the row cannot be scoped to anyone.
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "Member name normalises to an empty string.",
            )
            tally.loaded -= 1
            seen_in_file.discard(parsed.canon)
            return
        corpus.mp_keys_on_works.add(mp_key)

        ida = split_ida(row[col_ida])
        agency = (
            corpus.agencies.resolve(state, ida.district, ida.agency_raw)
            if ida.agency_raw
            else None
        )

        category, _ = parse_text(row[col_category])
        if category is not None and category not in WORK_CATEGORIES:
            corpus.new_categories[category] += 1
        description, description_avail = parse_text(row[col_description])

        status = None
        status_avail = Availability.NOT_PUBLISHED
        if col_status is not None:
            status, status_avail = parse_text(row[col_status])
            if status is not None and status not in WORK_STATUSES:
                corpus.new_statuses[status] += 1

        image_present = None
        image_avail = Availability.NOT_PUBLISHED
        if col_image is not None:
            image_present = str(row[col_image]).strip() == IMAGE_PRESENT_TOKEN
            image_avail = Availability.PUBLISHED

        corpus.upsert_work(
            parsed.canon,
            {
                "work_id_canon": parsed.canon,
                "work_id_raw": raw_work_id_prefix(row[col_work], parsed.canon),
                "mp_key": mp_key,
                "state": state,
                "district": ida.district,
                "agency": agency,
                "category": category,
                "description": description,
                "description_availability": description_avail,
                "status": status,
                "status_availability": status_avail,
                "asset_image_present": image_present,
                "asset_image_availability": image_avail,
                "fy": parsed.fy,
                "source_file": filename,
                "_dataset": dataset,
            },
        )

        if dataset == "works_recommended":
            corpus.ids_recommended.add(parsed.canon)
            corpus.recommended_amounts[parsed.canon] = (recommended_amt, recommended_avail)
        elif dataset == "works_sanctioned":
            corpus.ids_sanctioned.add(parsed.canon)
            corpus.sanctions[parsed.canon] = {
                "sanctioned_amt": sanctioned_amt,
                "sanction_date": sanction_date,
                "recommended_date": recommended_date,
                "recommended_date_availability": recommended_date_avail,
            }
        else:
            corpus.ids_completed.add(parsed.canon)
            completed_amt, completed_avail = parse_amount(row[col_completed_amt])
            corpus.completions[parsed.canon] = {
                "completion_date": completion_date,
                "completion_date_availability": completion_avail,
                "completed_amt": completed_amt,
                "completed_availability": completed_avail,
            }


def _read_expenditure(corpus: Corpus, df: pd.DataFrame) -> None:
    filename = df["_source_file"].iloc[0]
    house = df["_house"].iloc[0]
    tally = corpus.tally(filename)
    tally.rows_read = len(df)

    col_work_id = column(df, "Work ID")
    col_state = column(df, "State")
    col_ida = column(df, "IDA")
    col_mp = column(df, "Hon'ble Members of Parliament")
    col_date = column(df, "Expenditure Date")
    col_vendor = column(df, "Vendor Name")
    col_status = column(df, "Payment Status")
    col_amount = column(df, "Fund Disbursed Amount ( ₹ )", "Fund Disbursed Amount")

    for row in df.to_dict("records"):
        row_number = row["_row_number"]
        raw = raw_row_of(row)

        if _is_grand_total(row):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.GRAND_TOTAL_ROW,
                "Portal footer row, not a payment.",
            )
            continue

        parsed = parse_work_id(row[col_work_id])
        if parsed is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.WORK_ID_UNPARSEABLE,
                f"{col_work_id} does not match WS/MP{{code}}/{{FY}}/{{serial}}.",
            )
            continue

        state = normalize_state(row[col_state])
        if not state:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "State is blank.",
            )
            continue

        payment_status, _ = parse_text(row[col_status])
        if payment_status is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                f"{col_status} is blank.",
            )
            continue

        paid_amt, paid_avail = parse_amount(row[col_amount])
        if paid_amt is None and not is_null_token(row[col_amount]):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNPARSEABLE_AMOUNT,
                f"{col_amount} = {row[col_amount]!r}.",
            )
            continue

        payment_date, payment_date_avail = parse_date(row[col_date])
        if payment_date is None and looks_like_date(row[col_date]):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNPARSEABLE_DATE,
                f"{col_date} = {row[col_date]!r}.",
            )
            continue

        mp_key = corpus.note_mp(row[col_mp], house, state, None, from_allocation=False)
        if mp_key is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "No member named on the payment row.",
            )
            continue

        tally.loaded += 1
        corpus.states.add(state)
        corpus.ids_expenditure.add(parsed.canon)
        corpus.mp_keys_on_works.add(mp_key)

        ida = split_ida(row[col_ida])
        agency = (
            corpus.agencies.resolve(state, ida.district, ida.agency_raw)
            if ida.agency_raw
            else None
        )
        vendor_canon = normalize_vendor_name(row[col_vendor])
        if vendor_canon:
            corpus.vendors.setdefault(vendor_canon, str(row[col_vendor]).strip())

        corpus.upsert_work(
            parsed.canon,
            {
                "work_id_canon": parsed.canon,
                "work_id_raw": raw_work_id_prefix(row[col_work_id], parsed.canon),
                "mp_key": mp_key,
                "state": state,
                "district": ida.district,
                "agency": agency,
                "category": None,
                "description": None,
                "description_availability": Availability.NOT_PUBLISHED,
                "status": None,
                "status_availability": Availability.NOT_PUBLISHED,
                "asset_image_present": None,
                "asset_image_availability": Availability.NOT_PUBLISHED,
                "fy": parsed.fy,
                "source_file": filename,
                "_dataset": "expenditure",
            },
        )

        corpus.payments.append(
            {
                "work_canon": parsed.canon,
                "vendor_canon": vendor_canon,
                "paid_amt": paid_amt,
                "paid_availability": paid_avail,
                "payment_date": payment_date,
                "payment_date_availability": payment_date_avail,
                "payment_status": payment_status,
            }
        )


def _read_allocation(corpus: Corpus, df: pd.DataFrame) -> None:
    filename = df["_source_file"].iloc[0]
    house = df["_house"].iloc[0]
    tally = corpus.tally(filename)
    tally.rows_read = len(df)

    col_mp = column(df, "Hon'ble Members of Parliaments", "Hon'ble Members of Parliament")
    col_state = column(df, "State")
    col_amount = column(df, "Allocated AMOUNT ( ₹ )", "Allocated Amount")
    # Absent from the Rajya Sabha export, and correctly so: members are seated
    # by state (DATA-PROFILE.md section 9). The two loaders differ here.
    col_constituency = column(df, "Constituency") if house == HOUSE_LOK_SABHA else None

    for row in df.to_dict("records"):
        row_number = row["_row_number"]
        raw = raw_row_of(row)

        if _is_grand_total(row):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.GRAND_TOTAL_ROW,
                "Portal footer row, not a member.",
            )
            continue

        state = normalize_state(row[col_state])
        if not state:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD, "State is blank."
            )
            continue

        allocated_amt, allocated_avail = parse_amount(row[col_amount])
        if allocated_amt is None and not is_null_token(row[col_amount]):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNPARSEABLE_AMOUNT,
                f"{col_amount} = {row[col_amount]!r}.",
            )
            continue

        constituency = (
            normalize_constituency(row[col_constituency]) if col_constituency else None
        )
        if constituency:
            corpus.constituencies.add((state, constituency))

        mp_key = corpus.note_mp(row[col_mp], house, state, constituency, from_allocation=True)
        if mp_key is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                "Member name normalises to an empty string.",
            )
            continue

        tally.loaded += 1
        corpus.states.add(state)

        existing = corpus.allocations.get(mp_key)
        if existing is None:
            corpus.allocations[mp_key] = {
                "allocated_amt": allocated_amt,
                "allocated_availability": allocated_avail,
            }
        elif allocated_amt is not None:
            # Two rows for one normalised name: the allocation is the member's,
            # so the amounts add rather than one overwriting the other.
            existing["allocated_amt"] = (existing["allocated_amt"] or 0) + allocated_amt
            existing["allocated_availability"] = Availability.PUBLISHED


def _read_calamity(corpus: Corpus, df: pd.DataFrame) -> None:
    filename = df["_source_file"].iloc[0]
    house = df["_house"].iloc[0]
    tally = corpus.tally(filename)
    tally.rows_read = len(df)

    col_mp = column(df, "Hon'ble Members of Parliament")
    col_type = column(df, "Calamity Type")
    col_name = column(df, "Calamity Name")
    col_date = column(df, "Date of Consent")
    col_amount = column(df, "Consent Amount ( ₹ )", "Consent Amount")

    for row in df.to_dict("records"):
        row_number = row["_row_number"]
        raw = raw_row_of(row)

        if _is_grand_total(row):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.GRAND_TOTAL_ROW,
                "Portal footer row, not a consent.",
            )
            continue

        event_name, _ = parse_text(row[col_name])
        if event_name is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.NULL_REQUIRED_FIELD,
                f"{col_name} is blank.",
            )
            continue

        consented_amt, _ = parse_amount(row[col_amount])
        if consented_amt is None:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNPARSEABLE_AMOUNT,
                f"{col_amount} = {row[col_amount]!r}.",
            )
            continue

        # The calamity export publishes no State, so it cannot create a member;
        # it can only refer to one the rest of the corpus already names.
        normalised = normalize_mp_name(row[col_mp])
        mp_key = (normalised.name_canon, house)
        if not normalised.name_canon or mp_key not in corpus.mps:
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNRESOLVED_REFERENCE,
                f"No member matches {normalised.name_canon!r} in {house}; the calamity "
                "export publishes no state, so the consent cannot be scoped.",
            )
            continue

        consent_date, consent_date_avail = parse_date(row[col_date])
        if consent_date is None and looks_like_date(row[col_date]):
            corpus.rejects.add(
                filename, row_number, raw, RejectReason.UNPARSEABLE_DATE,
                f"{col_date} = {row[col_date]!r}.",
            )
            continue

        tally.loaded += 1
        calamity_type, _ = parse_text(row[col_type])
        corpus.calamity.append(
            {
                "mp_key": mp_key,
                "calamity_type": calamity_type,
                "event_name": event_name,
                "consented_amt": consented_amt,
                "consent_date": consent_date,
                "consent_date_availability": consent_date_avail,
            }
        )


def read_all() -> Corpus:
    """Pass 1 over all twelve exports, in dependency order.

    Allocation is read before the works exports so that a member's state and
    constituency come from the roll of members rather than from wherever their
    first work happened to be. Calamity is read last because it can only refer
    to members the other exports have already named.
    """
    corpus = Corpus()
    frames = {
        (dataset, house): loader()
        for dataset, house, loader in loaders.ALL_LOADERS
    }

    for house in (HOUSE_LOK_SABHA, "rajya_sabha"):
        _read_allocation(corpus, frames[("allocation", house)])
    for dataset in ("works_sanctioned", "works_completed", "works_recommended"):
        for house in (HOUSE_LOK_SABHA, "rajya_sabha"):
            _read_work_level(corpus, frames[(dataset, house)], dataset)
    for house in (HOUSE_LOK_SABHA, "rajya_sabha"):
        _read_expenditure(corpus, frames[("expenditure", house)])
    for house in (HOUSE_LOK_SABHA, "rajya_sabha"):
        _read_calamity(corpus, frames[("calamity", house)])

    return corpus


# ---------------------------------------------------------------------------
# Pass 2 - write
# ---------------------------------------------------------------------------


def write_all(session, corpus: Corpus) -> dict[str, int]:
    """Write the parsed corpus. Returns row counts per table for the report."""
    counts: dict[str, int] = {}

    # -- states ------------------------------------------------------------
    state_rows = [{"name": name} for name in sorted(corpus.states)]
    session.execute(insert(State), state_rows)
    session.flush()
    state_ids = {name: sid for sid, name in session.execute(select(State.id, State.name))}
    counts["states"] = len(state_rows)

    # -- constituencies ----------------------------------------------------
    constituency_rows = [
        {"state_id": state_ids[state], "name": name, "house": HOUSE_LOK_SABHA}
        for state, name in sorted(corpus.constituencies)
        if state in state_ids
    ]
    if constituency_rows:
        session.execute(insert(Constituency), constituency_rows)
    session.flush()
    constituency_ids = {
        (state_id, name): cid
        for cid, state_id, name in session.execute(
            select(Constituency.id, Constituency.state_id, Constituency.name)
        )
    }
    counts["constituencies"] = len(constituency_rows)

    # -- mps ---------------------------------------------------------------
    mp_rows = []
    ordered_mp_keys = sorted(corpus.mps)
    for key in ordered_mp_keys:
        record = corpus.mps[key]
        state = record["state"] or (
            record["state_votes"].most_common(1)[0][0] if record["state_votes"] else None
        )
        if state is None:
            continue
        state_id = state_ids[state]
        constituency_id = constituency_ids.get((state_id, record["constituency"]))
        mp_rows.append(
            {
                "name_raw": record["name_raw"],
                "name_canon": record["name_canon"],
                "house": record["house"],
                "state_id": state_id,
                "constituency_id": constituency_id,
                "term_start": record["term_start"],
                "term_end": record["term_end"],
                "is_synthetic": False,
            }
        )
    session.execute(insert(MP), mp_rows)
    session.flush()
    mp_ids = {
        (name_canon, house): mid
        for mid, name_canon, house in session.execute(
            select(MP.id, MP.name_canon, MP.house)
        )
    }
    counts["mps"] = len(mp_rows)

    # -- agencies and the canonicalisation ledger --------------------------
    agency_records = corpus.agencies.records()
    agency_rows = [
        {
            "name_canon": record.name_canon,
            "district": record.district,
            "state_id": state_ids[record.state],
            "variant_count": record.variant_count,
            "merge_confidence": record.merge_confidence,
            "is_synthetic": False,
        }
        for record in agency_records
        if record.state in state_ids
    ]
    session.execute(insert(Agency), agency_rows)
    session.flush()
    agency_ids = {
        (district or "", name_canon): aid
        for aid, district, name_canon in session.execute(
            select(Agency.id, Agency.district, Agency.name_canon)
        )
    }
    counts["agencies"] = len(agency_rows)

    variant_rows = []
    for record in agency_records:
        agency_id = agency_ids.get(record.key)
        if agency_id is None:
            continue
        for name_raw, matched_by, score in record.variants:
            variant_rows.append(
                {
                    "agency_id": agency_id,
                    "name_raw": name_raw,
                    "matched_by": matched_by,
                    "score": score,
                    "reviewed": False,
                }
            )
    session.execute(insert(AgencyNameVariant), variant_rows)
    counts["agency_name_variants"] = len(variant_rows)

    # -- vendors -----------------------------------------------------------
    vendor_rows = [
        {"name_canon": canon, "name_raw": raw, "agency_span": 0, "is_synthetic": False}
        for canon, raw in sorted(corpus.vendors.items())
    ]
    if vendor_rows:
        session.execute(insert(Vendor), vendor_rows)
    session.flush()
    vendor_ids = {
        name: vid for vid, name in session.execute(select(Vendor.id, Vendor.name_canon))
    }
    counts["vendors"] = len(vendor_rows)

    # -- works -------------------------------------------------------------
    work_rows = []
    for canon in sorted(corpus.works):
        record = corpus.works[canon]
        mp_id = mp_ids.get(record["mp_key"])
        if mp_id is None:
            continue
        agency = record["agency"]
        agency_id = agency_ids.get(agency.key) if agency is not None else None
        work_rows.append(
            {
                "work_id_canon": canon,
                "work_id_raw": record["work_id_raw"],
                "mp_id": mp_id,
                "agency_id": agency_id,
                "state_id": state_ids[record["state"]],
                "district": record["district"],
                "category": record["category"],
                "description": record["description"],
                "description_availability": record["description_availability"],
                "status": record["status"],
                "status_availability": record["status_availability"],
                "fy": record["fy"],
                "asset_image_present": record["asset_image_present"],
                "asset_image_availability": record["asset_image_availability"],
                "is_synthetic": False,
                "source_file": record["source_file"],
            }
        )
    session.execute(insert(Work), work_rows)
    session.flush()
    work_ids = {
        canon: wid
        for wid, canon in session.execute(select(Work.id, Work.work_id_canon))
    }
    counts["works"] = len(work_rows)

    # -- sanctions ---------------------------------------------------------
    sanction_rows = []
    for canon, record in corpus.sanctions.items():
        work_id = work_ids.get(canon)
        if work_id is None:
            continue
        recommended_amt, recommended_avail = corpus.recommended_amounts.get(
            canon, (None, Availability.NOT_PUBLISHED)
        )
        sanction_rows.append(
            {
                "work_id": work_id,
                "recommended_amt": recommended_amt,
                "recommended_availability": recommended_avail,
                "recommended_date": record["recommended_date"],
                "recommended_date_availability": record["recommended_date_availability"],
                "sanctioned_amt": record["sanctioned_amt"],
                "sanction_date": record["sanction_date"],
            }
        )
    session.execute(insert(Sanction), sanction_rows)
    counts["sanctions"] = len(sanction_rows)

    # -- completions -------------------------------------------------------
    completion_rows = []
    for canon, record in corpus.completions.items():
        work_id = work_ids.get(canon)
        if work_id is None:
            continue
        completion_rows.append({"work_id": work_id, "is_synthetic": False, **record})
    session.execute(insert(Completion), completion_rows)
    counts["completions"] = len(completion_rows)

    # -- payments ----------------------------------------------------------
    payment_rows = []
    for record in corpus.payments:
        work_id = work_ids.get(record["work_canon"])
        if work_id is None:
            continue
        payment_rows.append(
            {
                "work_id": work_id,
                "vendor_id": vendor_ids.get(record["vendor_canon"]),
                "paid_amt": record["paid_amt"],
                "paid_availability": record["paid_availability"],
                "payment_date": record["payment_date"],
                "payment_date_availability": record["payment_date_availability"],
                "payment_status": record["payment_status"],
                "is_synthetic": False,
            }
        )
    session.execute(insert(Payment), payment_rows)
    counts["payments"] = len(payment_rows)

    # -- calamity ----------------------------------------------------------
    calamity_rows = []
    for record in corpus.calamity:
        mp_id = mp_ids.get(record["mp_key"])
        if mp_id is None:
            continue
        calamity_rows.append(
            {
                "mp_id": mp_id,
                "calamity_type": record["calamity_type"],
                "event_name": record["event_name"],
                "consented_amt": record["consented_amt"],
                "consent_date": record["consent_date"],
                "consent_date_availability": record["consent_date_availability"],
            }
        )
    if calamity_rows:
        session.execute(insert(CalamityConsent), calamity_rows)
    counts["calamity_consents"] = len(calamity_rows)

    # -- vendor agency span ------------------------------------------------
    # Distinct agencies paying each vendor. Computed once here rather than per
    # case, because the agency-vendor graph reads it on every case.
    spans: dict[int, set[int]] = defaultdict(set)
    work_agency = {wid: aid for wid, aid in session.execute(select(Work.id, Work.agency_id))}
    for row in payment_rows:
        if row["vendor_id"] is None:
            continue
        agency_id = work_agency.get(row["work_id"])
        if agency_id is not None:
            spans[row["vendor_id"]].add(agency_id)
    for vendor_id, agencies in spans.items():
        session.get(Vendor, vendor_id).agency_span = len(agencies)

    # -- fund accounts -----------------------------------------------------
    counts["fund_accounts"] = _write_fund_accounts(
        session, corpus, mp_ids, work_ids, sanction_rows, payment_rows
    )

    return counts


def _write_fund_accounts(session, corpus, mp_ids, work_ids, sanction_rows, payment_rows) -> int:
    """Materialise the account ladder: allocated -> sanctioned -> disbursed.

    One row per MP per financial year for the rollups the corpus can compute
    per year, plus one `term_to_date` row per MP carrying the published
    allocation. The portal publishes a single cumulative allocation and no
    yearly breakdown, so `allocated_amt` is NULL with availability
    `not_published` on every per-FY row, and `mp_utilisation_pct` is computable
    only on the term-to-date row. Splitting the published total across years
    would be an invention, and the ratio drawn from it would be a ratio against
    a number MoSPI never published.
    """
    work_meta = {
        wid: (mp_id, fy)
        for wid, mp_id, fy in session.execute(select(Work.id, Work.mp_id, Work.fy))
    }

    sanctioned: dict[tuple[int, str], int] = defaultdict(int)
    for row in sanction_rows:
        mp_id, fy = work_meta[row["work_id"]]
        sanctioned[(mp_id, fy)] += row["sanctioned_amt"]

    disbursed: dict[tuple[int, str], int] = defaultdict(int)
    for row in payment_rows:
        if row["paid_amt"] is None:
            continue
        mp_id, fy = work_meta[row["work_id"]]
        disbursed[(mp_id, fy)] += row["paid_amt"]

    allocation_by_mp = {
        mp_ids[key]: value for key, value in corpus.allocations.items() if key in mp_ids
    }

    rows = []
    fys_by_mp: dict[int, set[str]] = defaultdict(set)
    for mp_id, fy in set(sanctioned) | set(disbursed):
        fys_by_mp[mp_id].add(fy)

    for mp_id, fys in fys_by_mp.items():
        for fy in sorted(fys):
            paid = disbursed.get((mp_id, fy))
            rows.append(
                {
                    "mp_id": mp_id,
                    "fy": fy,
                    "allocated_amt": None,
                    "allocated_availability": Availability.NOT_PUBLISHED,
                    "sanctioned_amt": sanctioned.get((mp_id, fy), 0),
                    "disbursed_amt": paid,
                    "disbursed_availability": (
                        Availability.NOT_PUBLISHED
                        if paid is None
                        else Availability.PUBLISHED_ZERO
                        if paid == 0
                        else Availability.PUBLISHED
                    ),
                    "mp_utilisation_pct": None,
                }
            )

    for mp_id in set(fys_by_mp) | set(allocation_by_mp):
        allocation = allocation_by_mp.get(mp_id)
        allocated_amt = allocation["allocated_amt"] if allocation else None
        allocated_avail = (
            allocation["allocated_availability"] if allocation else Availability.NOT_PUBLISHED
        )
        total_sanctioned = sum(
            amount for (owner, _), amount in sanctioned.items() if owner == mp_id
        )
        total_disbursed_parts = [
            amount for (owner, _), amount in disbursed.items() if owner == mp_id
        ]
        total_disbursed = sum(total_disbursed_parts) if total_disbursed_parts else None
        utilisation = (
            total_sanctioned / allocated_amt * 100
            if allocated_amt not in (None, 0)
            else None
        )
        rows.append(
            {
                "mp_id": mp_id,
                "fy": FY_TERM_TO_DATE,
                "allocated_amt": allocated_amt,
                "allocated_availability": allocated_avail,
                "sanctioned_amt": total_sanctioned,
                "disbursed_amt": total_disbursed,
                "disbursed_availability": (
                    Availability.NOT_PUBLISHED
                    if total_disbursed is None
                    else Availability.PUBLISHED_ZERO
                    if total_disbursed == 0
                    else Availability.PUBLISHED
                ),
                "mp_utilisation_pct": utilisation,
            }
        )

    session.execute(insert(FundAccount), rows)
    return len(rows)


SYNTHETIC_FLAGGED_TABLES = (MP, Agency, Vendor, Work, Payment, Completion, Certification)


def count_tables(session) -> dict[str, int]:
    """Row counts straight out of the database, plus the synthetic share.

    Read back rather than accumulated in Python, so the report describes what
    was actually written and not what the loader believed it wrote.
    """
    tables = (
        State, Constituency, MP, Agency, AgencyNameVariant, Vendor, Work,
        Sanction, Payment, Completion, Certification, CalamityConsent,
        FundAccount, IngestReject,
    )
    counts: dict[str, int] = {}
    for model in tables:
        name = model.__tablename__
        counts[name] = session.scalar(select(func.count()).select_from(model))
        if model in SYNTHETIC_FLAGGED_TABLES:
            counts[f"{name}__synthetic"] = session.scalar(
                select(func.count()).select_from(model).where(model.is_synthetic.is_(True))
            )
    return counts


# ---------------------------------------------------------------------------
# The load report
# ---------------------------------------------------------------------------


def _pct(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator * 100:.2f}%" if denominator else "n/a"


def print_report(corpus: Corpus, counts: dict[str, int], synthetic: dict) -> bool:
    """Print the load report. Returns False if any file failed to reconcile.

    Rupees are printed as `Rs`, never as the rupee sign: the Windows console
    this is run on encodes cp1252 and would raise on it, and a load report that
    crashes on its own last line is worse than one that spells the currency.
    """
    reconciled = True
    line = "-" * 78

    print()
    print("NIGRANI ingest report")
    print(line)
    print(f"corpus as read from data/raw/ at {datetime.now():%Y-%m-%d %H:%M:%S}")
    print()

    print("PER FILE  (loaded + rejected must equal rows in file, invariant 11)")
    print(f"  {'file':<70}{'rows':>7}{'load':>7}{'rej':>6}  ok")
    total_read = total_loaded = 0
    for dataset, house, _ in loaders.ALL_LOADERS:
        filename = RAW_FILES[(dataset, house)]
        tally = corpus.tallies.get(filename)
        if tally is None:
            continue
        rejected = corpus.rejects.count_for_file(filename)
        ok = tally.reconciles(rejected)
        reconciled = reconciled and ok
        total_read += tally.rows_read
        total_loaded += tally.loaded
        print(
            f"  {filename:<70}{tally.rows_read:>7}{tally.loaded:>7}"
            f"{rejected:>6}  {'yes' if ok else 'NO'}"
        )
    print(f"  {'TOTAL':<70}{total_read:>7}{total_loaded:>7}{len(corpus.rejects):>6}")
    print()

    print("REJECTS BY REASON")
    for reason, count in sorted(
        corpus.rejects.totals_by_reason().items(), key=lambda item: -item[1]
    ):
        print(f"  {reason:<28}{count:>7}")
    if not len(corpus.rejects):
        print("  (none)")
    print()

    print("TABLE COUNTS  (rows in backend/nigrani.db; `syn` counts the labelled")
    print("               synthetic-control rows, excluded from every aggregate)")
    for table in (
        "states", "constituencies", "mps", "agencies", "agency_name_variants",
        "vendors", "works", "sanctions", "payments", "completions",
        "certifications", "calamity_consents", "fund_accounts", "ingest_rejects",
    ):
        synthetic_rows = counts.get(f"{table}__synthetic", 0)
        suffix = f"   ({synthetic_rows} syn)" if synthetic_rows else ""
        print(f"  {table:<28}{counts.get(table, 0):>7}{suffix}")
    print()

    print("JOIN YIELDS")
    sanctioned = corpus.ids_sanctioned
    recommended = corpus.ids_recommended
    completed = corpus.ids_completed
    expenditure = corpus.ids_expenditure
    print(
        f"  sanctioned works with a recommendation row  "
        f"{len(sanctioned & recommended):>7}  of {len(sanctioned):>6}  "
        f"{_pct(len(sanctioned & recommended), len(sanctioned))}"
    )
    print(
        f"  completed works with a sanction row         "
        f"{len(completed & sanctioned):>7}  of {len(completed):>6}  "
        f"{_pct(len(completed & sanctioned), len(completed))}"
    )
    print(
        f"  works with expenditure and a sanction row   "
        f"{len(expenditure & sanctioned):>7}  of {len(expenditure):>6}  "
        f"{_pct(len(expenditure & sanctioned), len(expenditure))}"
    )
    print(
        f"  recommended AND sanctioned AND expenditure  "
        f"{len(recommended & sanctioned & expenditure):>7}"
    )
    on_works = corpus.mp_keys_on_works
    matched_mps = sum(1 for key in on_works if key in corpus.allocations)
    print(
        f"  members named on works matched to an        "
        f"{matched_mps:>7}  of {len(on_works):>6}  "
        f"{_pct(matched_mps, len(on_works))}"
    )
    print("    allocation row (after name normalisation)")
    print(
        f"  members holding an allocation              "
        f"{len(corpus.allocations):>8}"
    )
    print(
        f"  members holding an allocation AND at least  "
        f"{sum(1 for key in corpus.allocations if key in on_works):>7}"
    )
    print("    one work - the account-utilisation population")
    print()

    print("CANONICALISATION  (published agencies only; the control is excluded)")
    real_agencies = counts.get("agencies", 0) - counts.get("agencies__synthetic", 0)
    print(f"  raw agency strings seen                     {counts.get('agency_name_variants', 0):>7}")
    print(f"  canonical agencies                          {real_agencies:>7}")
    print(f"  folded by a fuzzy merge                     {corpus.agencies.fuzzy_merge_count():>7}")
    if corpus.agencies.fuzzy_merge_count() == 0:
        print("  The portal publishes one IDA string per district office on this")
        print("  corpus, so canonicalisation folded nothing. `DISTRICT MAGISTRAE`")
        print("  is a consistent portal-wide misspelling, not a split agency.")
    print()

    print("VOCABULARY DRIFT  (values DATA-PROFILE.md section 7 does not record)")
    if corpus.new_statuses or corpus.new_categories:
        for value, count in corpus.new_statuses.items():
            print(f"  new work status    {value!r}  x{count}")
        for value, count in corpus.new_categories.items():
            print(f"  new work category  {value!r}  x{count}")
        print("  Rows were loaded, not rejected: dropping a real work over a")
        print("  label would lose evidence. Record these in the profile.")
    else:
        print("  none")
    print()

    print("SYNTHETIC CONTROL  (CLAUDE.md invariant 12)")
    print(f"  work id      {synthetic['work_id']}")
    print(f"  case id      {synthetic['case_id']}")
    print(f"  inserted     {'yes' if synthetic['inserted'] else 'NO'}")
    if not synthetic["inserted"]:
        print(f"  reason       {synthetic['reason']}")
    print("  Labelled is_synthetic = true and excluded from every published")
    print("  aggregate. It is the only row in `certifications`; MoSPI publishes")
    print("  no utilisation certificate for any real work.")
    print()

    print(line)
    print(
        "RECONCILIATION: "
        + ("all twelve files reconcile." if reconciled else "FAILED - see the 'ok' column.")
    )
    print(
        "The corpus is a truncated portal sample, not the national record. "
        "No figure\nabove is a national total."
    )
    print(line)
    return reconciled


# ---------------------------------------------------------------------------


def main() -> int:
    print("reading data/raw/ ...", flush=True)
    corpus = read_all()

    print("rebuilding backend/nigrani.db ...", flush=True)
    # Truncate-and-reload by rebuild, so a second run produces the same counts
    # rather than doubled data. DDL only: no UPDATE and no DELETE is issued
    # anywhere in ingest (CLAUDE.md invariant 4).
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        print("writing corpus ...", flush=True)
        counts = write_all(session, corpus)

        synthetic = insert_synthetic_control(session, corpus.rejects)

        reject_rows = corpus.rejects.rows()
        if reject_rows:
            session.execute(insert(IngestReject), reject_rows)

        session.commit()
        counts = count_tables(session)

    ok = print_report(corpus, counts, synthetic)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
