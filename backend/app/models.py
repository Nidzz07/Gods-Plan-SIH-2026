"""The NIGRANI tables, as specified in docs/domain/DOMAIN-MODEL.md section (e).

Column notes worth keeping in mind while reading:

* **Raw inputs are stored; derived numbers are not.** Variances, lags,
  `gap_hop`, `coverage_pct` and `score` are produced by `engine/` at evaluation
  time and persisted only on `cases` / `rule_hits` once a case has been opened.
  One derivation path, one truth.

* **Availability is modelled explicitly.** Wherever a nullable amount, date or
  flag can be null for two different reasons, a companion enum column records
  which (CLAUDE.md invariant 2). `not_published` means the portal supplied no
  value or no row; `published_zero` means it supplied the field with the value
  zero. They are different findings and are never collapsed. This is what makes
  the invariant enforceable at the storage layer rather than only in the
  engine: a real zero payment cannot masquerade as a work with no payment row,
  because the zero carries `published_zero` and the absence carries no row at
  all.

* **`audit_log` is append-only.** Nothing in this file, or anywhere else in
  `backend/`, may offer an update or delete path for it (invariant 4).

* One table here is not in DOMAIN-MODEL.md: `certifications`. See its docstring.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .constants import Availability
from .db import Base

# One shared column type for every availability companion, so the enum cannot
# drift between tables. `native_enum=False` renders a VARCHAR plus a CHECK
# constraint, which SQLite honours and which stays readable if anyone opens the
# file with a generic client.
AvailabilityType = Enum(
    Availability,
    name="availability",
    native_enum=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
    validate_strings=True,
)


# ---------------------------------------------------------------------------
# Geography and people
# ---------------------------------------------------------------------------


class State(Base):
    """A state or union territory, as spelled by the portal."""

    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)

    # Local Government Directory code. Nullable because the portal does not
    # publish it; reserved so a later join to LGD does not need a migration.
    lgd_code: Mapped[str | None] = mapped_column(String(16))

    constituencies: Mapped[list["Constituency"]] = relationship(back_populates="state")


class Constituency(Base):
    """A Lok Sabha constituency.

    Rajya Sabha members are seated by state and have no constituency, so this
    table is `lok_sabha` only. The Rajya Sabha allocation export has no
    `Constituency` column, which is correct rather than a defect
    (DATA-PROFILE.md section 9).
    """

    __tablename__ = "constituencies"
    __table_args__ = (
        UniqueConstraint("state_id", "name", name="uq_constituency_state_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    house: Mapped[str] = mapped_column(String(16), nullable=False)

    state: Mapped["State"] = relationship(back_populates="constituencies")


class MP(Base):
    """A Member of Parliament, identified by normalised name and house.

    The portal publishes no MP identifier that spans the exports: the work id
    embeds a code, the allocation file carries only a name. `name_canon` is
    therefore the join key, and it is built by stripping honorifics and the
    published term suffixes (`(2022-28) (2022-2028)`, `(NaN-NaN)`).
    """

    __tablename__ = "mps"
    __table_args__ = (UniqueConstraint("name_canon", "house", name="uq_mp_name_house"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # As published, suffixes intact, so the officer sees the portal's spelling.
    name_raw: Mapped[str] = mapped_column(String(200), nullable=False)
    # Honorifics and term suffixes stripped. The allocation join key.
    name_canon: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    house: Mapped[str] = mapped_column(String(16), nullable=False)

    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)
    # Null for every Rajya Sabha member: they are seated by state.
    constituency_id: Mapped[int | None] = mapped_column(
        ForeignKey("constituencies.id"), index=True
    )

    # Null when the published suffix was `(NaN-NaN)`, or absent entirely.
    term_start: Mapped[int | None] = mapped_column(Integer)
    term_end: Mapped[int | None] = mapped_column(Integer)

    # CLAUDE.md invariant 12. The labelled synthetic control needs an actor to
    # hang on, and hanging it on a real member, office or firm would put an
    # injected sanction inside that actor's published aggregate. A flagged row
    # of its own keeps real and injected data from mixing silently.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    state: Mapped["State"] = relationship()
    constituency: Mapped["Constituency | None"] = relationship()


# ---------------------------------------------------------------------------
# Implementing agencies and vendors
# ---------------------------------------------------------------------------


class Agency(Base):
    """An implementing agency, after typo variants have been merged into one row.

    The portal publishes the agency inside the `IDA` column as
    `DISTRICT(AGENCY NAME_IDA)`, and the same office appears under several
    spellings (`DISTRICT MAGISTRAE` beside `DISTRICT MAGISTRATE`). Merges are
    blocked on (state, district) and scored with rapidfuzz; every merge is
    recorded in `agency_name_variants` so a disputed one is inspectable in the
    UI rather than lost inside the loader (declared limitation 9).
    """

    __tablename__ = "agencies"
    # Keyed by district and name, NOT by state: the portal's `State` column
    # describes the work's member rather than the office, and files one Agra
    # district magistrate under five different states. Including state in the
    # key would split that office five ways and quietly divide its duplicate
    # clusters and its vendor concentration by five. `state_id` below is the
    # majority of what the referencing rows said.
    __table_args__ = (
        UniqueConstraint("district", "name_canon", name="uq_agency_district_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_canon: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Null when the IDA column carried no district prefix.
    district: Mapped[str | None] = mapped_column(String(120), index=True)
    # The state most of this office's rows were filed under. A majority, not a
    # fact the portal asserts about the office - see the key comment above.
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)

    # How many raw strings merged into this row. 1 means no merge happened.
    variant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # rapidfuzz ratio of the weakest merged variant. Null when nothing was
    # merged, which is a different statement from "merged at a low score".
    merge_confidence: Mapped[float | None] = mapped_column(Float)

    # CLAUDE.md invariant 12. The labelled synthetic control needs an actor to
    # hang on, and hanging it on a real member, office or firm would put an
    # injected sanction inside that actor's published aggregate. A flagged row
    # of its own keeps real and injected data from mixing silently.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    state: Mapped["State"] = relationship()
    variants: Mapped[list["AgencyNameVariant"]] = relationship(back_populates="agency")


class AgencyNameVariant(Base):
    """The canonicalisation ledger: one row per raw agency string ever seen.

    Kept as its own table so an officer can see that
    `DISTRICT MAGISTRAE BUDAUN` was folded into `DISTRICT MAGISTRATE BUDAUN`,
    at what score, and dispute it. A merge NIGRANI cannot show is a merge
    NIGRANI should not make.
    """

    __tablename__ = "agency_name_variants"
    # Unique per agency rather than globally: `DEPUTY COMMISSIONER` is a
    # different office in every district that has one, so the same raw string
    # legitimately appears against several agencies.
    __table_args__ = (
        UniqueConstraint("agency_id", "name_raw", name="uq_variant_agency_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agency_id: Mapped[int] = mapped_column(ForeignKey("agencies.id"), nullable=False, index=True)

    # The string exactly as it appeared inside the IDA column's bracket.
    name_raw: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # `exact` when the normalised strings were identical, `fuzzy` when
    # rapidfuzz cleared AGENCY_FUZZY_FLOOR. The two are never shown as the same
    # kind of claim.
    matched_by: Mapped[str] = mapped_column(String(8), nullable=False)
    # 100.0 for an exact match; the rapidfuzz ratio for a fuzzy one.
    score: Mapped[float] = mapped_column(Float, nullable=False)

    # Set when a human has looked at the merge and accepted or rejected it.
    # False is the honest default: nobody has looked yet.
    reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    agency: Mapped["Agency"] = relationship(back_populates="variants")


class Vendor(Base):
    """A payee named on an expenditure row."""

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_canon: Mapped[str] = mapped_column(String(240), nullable=False, unique=True)
    name_raw: Mapped[str] = mapped_column(String(240), nullable=False)

    # Distinct agencies paying this vendor. A rollup rather than a derivation
    # because the agency-vendor graph reads it on every case and recomputing it
    # per case would scan the payment table each time.
    agency_span: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # CLAUDE.md invariant 12. The labelled synthetic control needs an actor to
    # hang on, and hanging it on a real member, office or firm would put an
    # injected sanction inside that actor's published aggregate. A flagged row
    # of its own keeps real and injected data from mixing silently.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)


# ---------------------------------------------------------------------------
# The account ladder
# ---------------------------------------------------------------------------


class FundAccount(Base):
    """The account ladder, materialised: allocated -> sanctioned -> disbursed.

    Grain is one MP by one financial year, plus one row per MP under the
    `term_to_date` sentinel.

    The sentinel exists because the portal publishes a single cumulative
    allocation per MP and no per-year breakdown. Sanction and disbursement
    rollups are genuinely per-FY and are stored that way; the allocation is
    not, so on every per-FY row `allocated_amt` is NULL with availability
    `not_published`. Writing an invented per-year share would be a fabrication
    dressed as a measurement, and `mp_utilisation_pct` would then be a ratio
    against a number MoSPI never published.
    """

    __tablename__ = "fund_accounts"
    __table_args__ = (UniqueConstraint("mp_id", "fy", name="uq_fund_account_mp_fy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mps.id"), nullable=False, index=True)

    # `2024-2025`, or the FY_TERM_TO_DATE sentinel.
    fy: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # Whole rupees. Null on every per-FY row: see the class docstring.
    allocated_amt: Mapped[int | None] = mapped_column(Integer)
    allocated_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # A rollup over sanctions, so zero sanctions is a real zero, not a gap.
    sanctioned_amt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Null when no expenditure row joins to any of this MP's works. That is a
    # truncation artefact of the export as often as it is a real absence of
    # payment, so it must not read as zero.
    disbursed_amt: Mapped[int | None] = mapped_column(Integer)
    disbursed_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # sanctioned / allocated * 100. Null when allocated_amt is null or zero -
    # a ratio against nothing is not zero utilisation, it is no measurement.
    mp_utilisation_pct: Mapped[float | None] = mapped_column(Float)

    mp: Mapped["MP"] = relationship()


# ---------------------------------------------------------------------------
# The work and its journey
# ---------------------------------------------------------------------------


class Work(Base):
    """One work: the case unit (DOMAIN-MODEL.md (a)).

    A row exists for every work id seen in any of the four work-level exports,
    not only for sanctioned works. A recommendation that was never sanctioned
    has no fund journey and never becomes a case, but it does carry a
    recommendation date and a sanction date of its own and so belongs in the
    sanction-lag distribution; an expenditure row whose work id never appears
    in the sanctioned export still has to attach its payment to something.
    Restricting this table to sanctioned works would force ingest to discard
    tens of thousands of published rows, which invariant 11 forbids.
    """

    __tablename__ = "works"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Whitespace-stripped and uppercased. The natural key.
    work_id_canon: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # Exactly as published, embedded tabs intact, so the trace can show the
    # officer the string the portal actually printed.
    work_id_raw: Mapped[str] = mapped_column(String(80), nullable=False)

    mp_id: Mapped[int] = mapped_column(ForeignKey("mps.id"), nullable=False, index=True)
    # Null when the IDA column was blank or unparseable.
    agency_id: Mapped[int | None] = mapped_column(ForeignKey("agencies.id"), index=True)
    state_id: Mapped[int] = mapped_column(ForeignKey("states.id"), nullable=False, index=True)
    # Null when the IDA column carried no district prefix.
    district: Mapped[str | None] = mapped_column(String(120), index=True)

    # One of WORK_CATEGORIES. Null where the export printed `N/A`.
    category: Mapped[str | None] = mapped_column(String(48))

    # Null where the export printed `N/A`. Two rules read it, and both are
    # skipped rather than passed when it is missing, so the companion records
    # whether it was absent or supplied empty.
    description: Mapped[str | None] = mapped_column(Text)
    description_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # One of WORK_STATUSES. Published only in the sanctioned export, so a work
    # known solely from a payment row has no status at all - which is not the
    # same as a work reported as not started.
    status: Mapped[str | None] = mapped_column(String(48), index=True)
    status_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # Parsed from the work id, so it is present on every row.
    fy: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # `Image == 'Images'`. NULLABLE, against DOMAIN-MODEL.md (e), because the
    # `Image` column is published only in the completed export: a sanctioned
    # work that has not completed has no image field at all. Storing False
    # there would make `asset_evidence_missing` fire on a reporting gap, which
    # is exactly the confusion invariant 2 exists to prevent. Absent means the
    # rule is skipped with `not_published`, never that no photograph was filed.
    asset_image_present: Mapped[bool | None] = mapped_column(Boolean)
    asset_image_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # CLAUDE.md invariant 12. Labelled in the UI and excluded from every
    # published aggregate. Real and injected data are never mixed silently.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Which of the twelve exports supplied this row's descriptive fields. A
    # work seen in several files records the richest source, in the order
    # sanctioned > completed > recommended > expenditure.
    source_file: Mapped[str] = mapped_column(String(120), nullable=False)

    mp: Mapped["MP"] = relationship()
    agency: Mapped["Agency | None"] = relationship()
    state: Mapped["State"] = relationship()
    sanction: Mapped["Sanction | None"] = relationship(back_populates="work", uselist=False)
    completion: Mapped["Completion | None"] = relationship(back_populates="work", uselist=False)
    certification: Mapped["Certification | None"] = relationship(
        back_populates="work", uselist=False
    )
    payments: Mapped[list["Payment"]] = relationship(back_populates="work")


class Sanction(Base):
    """The sanction record: what was recommended, what was sanctioned, and when.

    Both amount columns are kept even though recommended equals sanctioned in
    every matched work in the corpus (DATA-PROFILE.md section 5). That identity
    is itself the finding that removed the `cost_overrun` rule, and a future
    download may break it.
    """

    __tablename__ = "sanctions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id"), nullable=False, unique=True, index=True
    )

    # Null when the recommended export has no row for this work. `published_zero`
    # would mean the portal recommended nothing, which is a different claim.
    recommended_amt: Mapped[int | None] = mapped_column(Integer)
    recommended_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # Null when the sanctioned export left the recommendation date blank. The
    # sanction-lag rule is then skipped, never passed.
    recommended_date: Mapped[date | None] = mapped_column(Date)
    recommended_date_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # Non-null: a sanction row exists only because the portal published both.
    sanctioned_amt: Mapped[int] = mapped_column(Integer, nullable=False)
    sanction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    work: Mapped["Work"] = relationship(back_populates="sanction")


class Payment(Base):
    """One expenditure row: money leaving the agency towards a vendor."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id"), nullable=False, index=True)
    # Null when the export named no vendor.
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), index=True)

    # Whole rupees. A published zero carries `published_zero` and is a fact
    # about the payment; a work with no payment row at all has no row here and
    # is a different finding entirely.
    paid_amt: Mapped[int | None] = mapped_column(Integer)
    paid_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    payment_date: Mapped[date | None] = mapped_column(Date, index=True)
    payment_date_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # One of PAYMENT_STATUSES.
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False)

    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    work: Mapped["Work"] = relationship(back_populates="payments")
    vendor: Mapped["Vendor | None"] = relationship()


class Completion(Base):
    """The completion record: the work was reported finished on this date."""

    __tablename__ = "completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id"), nullable=False, unique=True, index=True
    )

    completion_date: Mapped[date | None] = mapped_column(Date, index=True)
    completion_date_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # The amount the completed export reports as disbursed. It is the agency's
    # own figure, not the sum of the expenditure rows, and the two disagree on
    # a tenth of matched works - which is why both are stored.
    completed_amt: Mapped[int | None] = mapped_column(Integer)
    completed_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    work: Mapped["Work"] = relationship(back_populates="completion")


class Certification(Base):
    """The utilisation certificate: fund-ladder hop 2.

    **This table is empty for every real work, and that is the point.** MoSPI
    publishes no utilisation certificate date and no certified amount, so
    ingest never writes a row here from `data/raw/` - the count of real rows in
    this table is the headline entry in the ablation report
    (DOMAIN-MODEL.md (i), entry 1).

    It exists because `variance_disbursement_to_certification` must have a
    derivation that actually runs at least once (CLAUDE.md invariant 3), and
    the only row that can make it run is the labelled synthetic control,
    fixture C. DOMAIN-MODEL.md (e) says no certified column appears on any
    table; keeping the rung in a table of its own honours that - no real work's
    record gains a column MoSPI never filled - while still letting the control
    be queried through the same models as real data.
    """

    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id"), nullable=False, unique=True, index=True
    )

    certified_amt: Mapped[int | None] = mapped_column(Integer)
    certified_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    certification_date: Mapped[date | None] = mapped_column(Date)
    certification_date_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    # True on every row this table will ever hold on public MPLADS data.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    work: Mapped["Work"] = relationship(back_populates="certification")


class CalamityConsent(Base):
    """An MP's consent to divert allocation to a declared calamity.

    Context only: no rule in rulebook v1.0.0 reads this table. It is carried
    because an account that looks underutilised may simply have had its money
    consented elsewhere, and an officer should be able to see that.
    """

    __tablename__ = "calamity_consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mp_id: Mapped[int] = mapped_column(ForeignKey("mps.id"), nullable=False, index=True)

    calamity_type: Mapped[str | None] = mapped_column(String(48))
    event_name: Mapped[str] = mapped_column(String(160), nullable=False)
    consented_amt: Mapped[int] = mapped_column(Integer, nullable=False)

    consent_date: Mapped[date | None] = mapped_column(Date)
    consent_date_availability: Mapped[Availability] = mapped_column(
        AvailabilityType, nullable=False, default=Availability.NOT_PUBLISHED
    )

    mp: Mapped["MP"] = relationship()


# ---------------------------------------------------------------------------
# Cases, the trace and the audit trail
# ---------------------------------------------------------------------------


class Case(Base):
    """A scored, openable case. One sanctioned work, evaluated once."""

    __tablename__ = "cases"

    # `NG-` + 10 hex, derived from the canonical work id, never from row order
    # (invariant 8). Re-running ingest on the same corpus reproduces it.
    case_id: Mapped[str] = mapped_column(String(16), primary_key=True)
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id"), nullable=False, unique=True, index=True
    )

    # Display score, capped at 100. The cap is not renormalisation: weights are
    # never divided, because an officer re-deriving the trace on paper must be
    # able to add the printed weights and reach `raw_score`.
    score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # Uncapped, 0-154. Both numbers are stored and both are shown.
    raw_score: Mapped[int] = mapped_column(Integer, nullable=False)

    severity: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open", index=True)

    # (144 - weight of skipped rules) / 144. Weight-based, not rule-count
    # based: a case at 65% coverage scoring 50 is a different object from one
    # at 100% coverage scoring 50, and skipped weight is never redistributed.
    coverage_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # First open hop walking down the fund ladder; null when none is open.
    gap_hop: Mapped[str | None] = mapped_column(String(48))
    # Largest computable lifecycle lag; null when none is computable.
    slowest_lag: Mapped[str | None] = mapped_column(String(48))

    # The snapshot this case was scored under. A recompute re-derives against
    # this row's YAML, not against today's rules.yaml (invariant 5).
    rulebook_version_id: Mapped[int] = mapped_column(
        ForeignKey("rulebook_versions.id"), nullable=False
    )

    # 0 or CORROBORATION_WEIGHT. The only non-rule source of score.
    corroboration_bonus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Mirrors works.is_synthetic so a list query can exclude controls from a
    # published aggregate without joining (invariant 12).
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    work: Mapped["Work"] = relationship()
    rule_hits: Mapped[list["RuleHit"]] = relationship(back_populates="case")


class RuleHit(Base):
    """One row of the reasoning trace: what was checked and what happened.

    One row per rule per case, always ten rows, including the passes and the
    skips. A trace that omitted the passes would not be re-derivable.
    """

    __tablename__ = "rule_hits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), nullable=False, index=True)

    rule_id: Mapped[str] = mapped_column(String(48), nullable=False)
    # As snapshotted, not as currently worded in rules.yaml, so an old trace
    # still reads the way the officer read it.
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    # The feature the rule read, from the derived feature dictionary.
    field: Mapped[str] = mapped_column(String(64), nullable=False)

    # Stringified so numbers, booleans and nulls share one column and the value
    # an auditor sees is the value that was rendered on the day.
    raw_value: Mapped[str | None] = mapped_column(String(64))
    threshold: Mapped[str] = mapped_column(String(64), nullable=False)
    operator: Mapped[str] = mapped_column(String(8), nullable=False)

    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    # The rule's full undivided weight if fired, else 0. Never a scaled share.
    contribution: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    severity: Mapped[str] = mapped_column(String(8), nullable=False)

    # fired | passed | skipped.
    status: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    # One of SKIP_REASONS. Non-null exactly when status is `skipped`; a skipped
    # rule without a reason is a bug, not a degraded row.
    skip_reason: Mapped[str | None] = mapped_column(String(24))

    # Mandatory and non-null on a fired `duplicate_work`, null everywhere else.
    # The similarity model is allowed into the score only because this column
    # hands the officer the records the number came from (DOMAIN-MODEL.md (h)).
    citation_json: Mapped[str | None] = mapped_column(Text)

    # Travels with the flag and is displayed beside it, never in a footnote -
    # e.g. the truncation caveat on `status_payment_mismatch`.
    caveat: Mapped[str | None] = mapped_column(Text)

    case: Mapped["Case"] = relationship(back_populates="rule_hits")


class AuditLog(Base):
    """Append-only, hash-chained event trail (CLAUDE.md invariant 4).

    INSERT only. No UPDATE, no DELETE, and no helper capable of either, here or
    anywhere else in `backend/`. The hash chain makes a tamper visible even to
    someone who reaches the SQLite file directly: `row_hash` covers this row's
    contents together with `prev_hash`, so altering any earlier row breaks
    every hash after it.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    actor_role: Mapped[str] = mapped_column(String(24), nullable=False)
    # Null for events written by ingest or scoring rather than by a person.
    actor_id: Mapped[int | None] = mapped_column(Integer)

    # One of AUDIT_EVENTS.
    event: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # Null on corpus-level events such as INGEST_COMPLETED.
    case_id: Mapped[str | None] = mapped_column(ForeignKey("cases.case_id"), index=True)

    # JSON text, kept as text so an old row stays readable if the payload shape
    # of that event type later changes. On SCORE_RECOMPUTED it carries the full
    # before and after trace, not only the scalar score.
    payload_json: Mapped[str | None] = mapped_column(Text)

    # Null on the first row only.
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class RulebookVersion(Base):
    """A snapshot of rules.yaml. An edit creates a version; it never mutates one."""

    __tablename__ = "rulebook_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)

    # The complete rulebook text, verbatim, plus its digest - so "same version,
    # edited file" is detectable rather than silently accepted.
    yaml_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    yaml_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by_role: Mapped[str] = mapped_column(String(24), nullable=False)
    # Why the officer changed it. Null on the seeded first version.
    note: Mapped[str | None] = mapped_column(Text)


class MLFinding(Base):
    """A tier-3 or tier-4 model output. Badge only, worth zero points.

    `contributes_to_score` is false for every kind except `duplicate`, and the
    test for CLAUDE.md invariant 1 asserts that the scored contribution summed
    over rows where it is false is exactly zero.
    """

    __tablename__ = "ml_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id"), nullable=False, index=True)

    # duplicate | anomaly | forecast | graph.
    kind: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    value: Mapped[float | None] = mapped_column(Float)
    # Matched ids, similarity components, feature attributions.
    payload_json: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)

    contributes_to_score: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    work: Mapped["Work"] = relationship()


class IngestReject(Base):
    """Every source row ingestion refused, with the original line and a reason.

    Ingestion never silently drops a row (CLAUDE.md invariant 11): for all
    twelve files, loaded + rejected must equal the rows in the file. Ministry
    only - this table holds raw source text and is a data-quality artefact, not
    a finding about anyone (DOMAIN-MODEL.md (k)).
    """

    __tablename__ = "ingest_rejects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_file: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    # 1-based, excluding the header, so it matches what a spreadsheet shows.
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # The row as read, JSON-encoded field by field. Kept verbatim so a Ministry
    # user can see exactly what the portal published.
    raw_row: Mapped[str] = mapped_column(Text, nullable=False)

    # One of RejectReason. The enum is closed: a new failure mode gets a new
    # member, never a free-text string.
    reason: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # What specifically failed, e.g. which column held the unparseable value.
    detail: Mapped[str | None] = mapped_column(Text)

    at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
