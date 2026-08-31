"""Every shared literal in NIGRANI, defined once (CLAUDE.md invariant 7).

Nothing in `ingest/`, `engine/` or `derive.py` may restate a value that lives
here. If a number appears in two modules it belongs in this one.

The measured figures quoted in comments come from `docs/data/DATA-PROFILE.md`,
which is the authority for every threshold and every claim about the data.
"""

from __future__ import annotations

import enum
import hashlib
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

# backend/app/constants.py -> repo root
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"

# --------------------------------------------------------------------------
# Corpus
# --------------------------------------------------------------------------

# The maximum payment date in the committed corpus (DATA-PROFILE.md section 4).
# Every "days since" feature is measured against this and never against
# `today`, so a case re-derived months from now reproduces the number the
# officer acted on. Changing this without re-downloading the corpus silently
# rewrites history.
DATA_AS_OF = date(2026, 8, 24)

# The portal appends a "Grand Total" footer row to every export. It is not a
# data row: it carries an aggregate in one column and blanks elsewhere, and in
# the two Works_Sanctioned files that aggregate lands in `Work Status`.
# Detected on the serial-number column, which reads this literal instead of an
# integer.
GRAND_TOTAL_MARKER = "Grand Total"

HOUSE_LOK_SABHA = "lok_sabha"
HOUSE_RAJYA_SABHA = "rajya_sabha"
HOUSES = (HOUSE_LOK_SABHA, HOUSE_RAJYA_SABHA)

DATASET_RECOMMENDED = "works_recommended"
DATASET_SANCTIONED = "works_sanctioned"
DATASET_COMPLETED = "works_completed"
DATASET_EXPENDITURE = "expenditure"
DATASET_ALLOCATION = "allocation"
DATASET_CALAMITY = "calamity"

# The twelve committed exports, keyed by (dataset, house) so no loader spells a
# filename out for itself. File names on disk use underscores; the portal's
# originals used spaces (DATA-PROFILE.md section 9).
RAW_FILES: dict[tuple[str, str], str] = {
    (DATASET_RECOMMENDED, HOUSE_LOK_SABHA): "Works_Recommended_lok_sabha.csv",
    (DATASET_RECOMMENDED, HOUSE_RAJYA_SABHA): "Works_Recommended_rajya_sabha.csv",
    (DATASET_SANCTIONED, HOUSE_LOK_SABHA): "Works_Sanctioned_lok_sabha.csv",
    (DATASET_SANCTIONED, HOUSE_RAJYA_SABHA): "Works_Sanctioned_rajya_sabha.csv",
    (DATASET_COMPLETED, HOUSE_LOK_SABHA): "Works_Completed_lok_sabha.csv",
    (DATASET_COMPLETED, HOUSE_RAJYA_SABHA): "Works_Completed_rajya_sabha.csv",
    (DATASET_EXPENDITURE, HOUSE_LOK_SABHA): (
        "Expenditure_on_Completed_and_On-going_Works_as_on_Date_lok_sabha.csv"
    ),
    (DATASET_EXPENDITURE, HOUSE_RAJYA_SABHA): (
        "Expenditure_on_Completed_and_On-going_Works_as_on_Date_rajya_sabha.csv"
    ),
    (DATASET_ALLOCATION, HOUSE_LOK_SABHA): "Allocated_Limit_for_Honble_MPs_lok_sabha.csv",
    (DATASET_ALLOCATION, HOUSE_RAJYA_SABHA): "Allocated_Limit_for_Honble_MPs_rajya_sabha.csv",
    (DATASET_CALAMITY, HOUSE_LOK_SABHA): "Amount_consented_for_Calamity_lok_sabha.csv",
    (DATASET_CALAMITY, HOUSE_RAJYA_SABHA): "Amount_consented_for_Calamity_rajya_sabha.csv",
}

# Files are UTF-8 with a byte-order mark; without this the first column name
# arrives with a BOM glued to it (data/raw/README.md).
RAW_ENCODING = "utf-8-sig"

# Portal date format, e.g. 08-Jul-2024.
RAW_DATE_FORMAT = "%d-%b-%Y"

# --------------------------------------------------------------------------
# Work id
# --------------------------------------------------------------------------

# Pattern WS/MP{code}/{FY}/{serial}. Some Lok Sabha rows carry a literal tab
# inside the id, so all whitespace is stripped before the match is attempted
# (DATA-PROFILE.md section 2).
WORK_ID_PATTERN = r"^(WS/MP(\d+)/(\d{4}-\d{4})/(\d+))"

CASE_ID_PREFIX = "NG-"
# Ten hex characters give 2^40 values against ~27K works. Ingest asserts
# uniqueness anyway; a collision is an ingest_rejects row, never an overwrite.
CASE_ID_HEX_LEN = 10


def canonical_work_id(work_id_raw: str) -> str:
    """Uppercase, with all whitespace including embedded tabs removed."""
    return "".join(str(work_id_raw).split()).upper()


def case_id_for(work_id_raw: str) -> str:
    """Deterministic from the work id, never from row order (invariant 8)."""
    canon = canonical_work_id(work_id_raw)
    digest = hashlib.sha256(canon.encode()).hexdigest()
    return CASE_ID_PREFIX + digest[:CASE_ID_HEX_LEN].upper()


# --------------------------------------------------------------------------
# Availability - the three-valued distinction invariant 2 exists to protect
# --------------------------------------------------------------------------


class Availability(str, enum.Enum):
    """Why a nullable field is null, recorded next to the field itself.

    `not_published` and `published_zero` are different findings and must stay
    distinguishable end to end (CLAUDE.md invariant 2). A reporting gap must
    never be able to masquerade as a clean record.

    `not_applicable` is written by the derivation layer, not by ingest: it
    means the work has not reached the stage the field describes, which is a
    judgement over the lifecycle rather than a fact any export states. It is
    declared here so the storage layer and the rule trace share one vocabulary.
    """

    PUBLISHED = "published"
    NOT_PUBLISHED = "not_published"
    PUBLISHED_ZERO = "published_zero"
    NOT_APPLICABLE = "not_applicable"


# The subset ingest may write. Anything else is a derivation-layer decision.
INGEST_AVAILABILITIES = (
    Availability.PUBLISHED,
    Availability.NOT_PUBLISHED,
    Availability.PUBLISHED_ZERO,
)

# `rule_hits.skip_reason` draws from the same vocabulary, minus `published`:
# a rule that read a value is never skipped.
SKIP_REASONS = (
    Availability.NOT_PUBLISHED.value,
    Availability.PUBLISHED_ZERO.value,
    Availability.NOT_APPLICABLE.value,
)

# --------------------------------------------------------------------------
# Ingest rejects - a closed enum (CLAUDE.md invariant 11)
# --------------------------------------------------------------------------


class RejectReason(str, enum.Enum):
    """Why a source row, or a part of one, was not loaded.

    Ingestion never silently drops a row. Every value here is written with the
    source file, the 1-based row number and the raw line, so a Ministry user
    can read the original text of anything NIGRANI refused.
    """

    # The portal's "Grand Total" footer, one per export. Twelve rows in all.
    GRAND_TOTAL_ROW = "grand_total_row"
    # `Work` / `Work ID` does not match WS/MP{code}/{FY}/{serial}. In
    # Works_Recommended_lok_sabha these rows read literally "NA-<category>".
    WORK_ID_UNPARSEABLE = "work_id_unparseable"
    # An amount column held something other than a number.
    UNPARSEABLE_AMOUNT = "unparseable_amount"
    # A date column held something other than %d-%b-%Y.
    UNPARSEABLE_DATE = "unparseable_date"
    # A column the row cannot exist without (state, sanctioned amount) was blank.
    NULL_REQUIRED_FIELD = "null_required_field"
    # The same canonical work id appeared twice in one work-level export.
    DUPLICATE_WORK_ID = "duplicate_work_id"
    # A reserved id - currently only the synthetic control - already exists.
    CASE_ID_COLLISION = "case_id_collision"
    # The row names a person or a work that no export in the corpus
    # identifies - a calamity consent against an MP who holds no allocation
    # and recommends no work. The consent is real; the corpus cannot say whose
    # it is, and inventing an MP row to hang it on would invent a person.
    UNRESOLVED_REFERENCE = "unresolved_reference"
    # Declared in DOMAIN-MODEL.md (e) and retained. Currently emitted zero
    # times: the two shifted-amount rows the profile recorded turned out to be
    # Grand Total footers and are classified as such.
    COLUMN_SHIFT = "column_shift"
    # sanction_date earlier than recommended_date. Zero measured; the check
    # stands because clamping to zero would hide it.
    NEGATIVE_LAG = "negative_lag"
    # Declared in DOMAIN-MODEL.md (e) and retained, but never emitted: an
    # unrecognised category label is reported as vocabulary drift and the work
    # is still loaded. Dropping a real work over a label would lose evidence.
    UNKNOWN_CATEGORY = "unknown_category"


# --------------------------------------------------------------------------
# Categorical vocabularies (DATA-PROFILE.md section 7)
# --------------------------------------------------------------------------

# Recorded in full so an unseen value in a later download is detected as new
# rather than silently bucketed.
WORK_STATUSES = (
    "Physical Inspection",
    "Sanction",
    "Vendor Identification",
    "Work partially Completed",
    "Work Completed",
    "Time Estimation",
)
WORK_CATEGORIES = (
    "Normal/Others",
    "Repair and Renovation",
    "Trust and Society",
    "Bar and Associations",
)
PAYMENT_STATUSES = ("Payment Success", "Payment In-Progress")

# The portal writes these where it has nothing to say. They are absences, not
# values, and become NULL with availability `not_published`.
NULL_TOKENS = ("", "N/A", "NA", "-", "NULL", "NONE", "NAN")

# `Image` is binary presence only: no geotag, no timestamp, no URL.
IMAGE_PRESENT_TOKEN = "Images"

# The status that `completed_without_payment` reads.
STATUS_WORK_COMPLETED = "Work Completed"

# --------------------------------------------------------------------------
# Canonicalisation
# --------------------------------------------------------------------------

# `DISTRICT MAGISTRAE BUDAUN` and `DISTRICT MAGISTRATE BUDAUN` are one office.
# Merges are blocked on (state, district) - both published separately in the
# IDA column - and then compared on the agency name alone, so this floor only
# has to separate typos from genuinely different offices inside one district.
# 90 admits a single-character slip in a short name and rejects
# `DISTRICT MAGISTRATE` against `DISTRICT PLANNING OFFICER`. Every merge is
# written to `agency_name_variants` for review; none is silent (declared
# limitation 9).
AGENCY_FUZZY_FLOOR = 90.0

# Term suffixes on published MP names: `(2022-28) (2022-2028)`, `(NaN-NaN)`.
MP_TERM_SUFFIX_PATTERN = r"\s*\(\s*(?:\d{4}\s*-\s*\d{2,4}|NaN\s*-\s*NaN)\s*\)"
# Honorifics stripped before the allocation join. Applied repeatedly, because
# names such as `Dr. Shri X` carry two.
MP_TITLE_PREFIXES = (
    "shri",
    "shrimati",
    "smt",
    "sh",
    "dr",
    "mr",
    "mrs",
    "ms",
    "miss",
    "prof",
    "professor",
    "adv",
    "advocate",
    "km",
    "kumari",
    "kum",
    "maulana",
    "sardar",
    "col",
    "capt",
    "gen",
    "justice",
)

# The IDA column reads DISTRICT(AGENCY NAME_IDA). The `_IDA` suffix is a portal
# artefact and not part of the office's name; a few rows omit it, and a few
# carry `_<digit>` instead.
IDA_PATTERN = r"^\s*(.*?)\s*\((.*)\)\s*$"
IDA_SUFFIX_PATTERN = r"_(?:IDA|\d+)\s*$"

# --------------------------------------------------------------------------
# Account ladder
# --------------------------------------------------------------------------

# The portal publishes ONE allocation figure per MP, cumulative over the term,
# and no financial-year breakdown. `fund_accounts` therefore carries one row
# per MP per FY for the sanction and disbursement rollups, which are genuinely
# per-FY, plus one row under this sentinel carrying the published allocation
# and the term-to-date rollups. `mp_utilisation_pct` is computable only on the
# sentinel row; on every per-FY row `allocated_amt` is NULL with availability
# `not_published`, because it is.
FY_TERM_TO_DATE = "term_to_date"

# --------------------------------------------------------------------------
# Scoring (read by engine/, defined here so no module restates them)
# --------------------------------------------------------------------------

RULE_WEIGHT_TOTAL = 144
CORROBORATION_WEIGHT = 10
CORROBORATION_MIN_HIGH_CASES = 3
SCORE_CAP = 100
SEVERITY_HIGH_MIN = 75
SEVERITY_MEDIUM_MIN = 50

SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"

RULE_STATUS_FIRED = "fired"
RULE_STATUS_PASSED = "passed"
RULE_STATUS_SKIPPED = "skipped"

CASE_STATUSES = ("open", "under_review", "escalated", "resolved")

# An agency's total disbursement must clear this floor before
# `vendor_concentration` may fire, so a small agency with one work does not
# read as concentrated. Rs 50 lakh (DOMAIN-MODEL.md (g) rule 6).
VENDOR_CONCENTRATION_AGENCY_FLOOR = 5_000_000

# --------------------------------------------------------------------------
# The two ladders (DOMAIN-MODEL.md (b) and (c))
# --------------------------------------------------------------------------

# Fund ladder, two hops. Hop 2 is permanently unavailable on public MPLADS
# data and is retained deliberately: it has a derivation function and a test,
# it returns None with reason `not_published` on every real row, and it is the
# headline entry in the ablation report.
HOP_SANCTION_TO_DISBURSEMENT = "sanction_to_disbursement"
HOP_DISBURSEMENT_TO_CERTIFICATION = "disbursement_to_certification"
FUND_HOPS = (HOP_SANCTION_TO_DISBURSEMENT, HOP_DISBURSEMENT_TO_CERTIFICATION)

# A hop is open when its variance is below the tolerance the rulebook sets for
# it, which is the threshold of the rule that reads that hop's variance. Hop 2
# has no rule, because there is no public data to calibrate one against, so it
# falls back to this figure purely so the ladder can still show a state on the
# synthetic control. An open hop 2 contributes exactly zero points, and that
# is the whole point of fixture C.
FUND_HOP_DEFAULT_TOLERANCE_PCT = -15

# Lifecycle ladder, three lags. `execution_days` is NOT one of them: it is
# completion_date - sanction_date and is computable on works that have no
# payment row at all (DOMAIN-MODEL.md (c)).
LAG_RECOMMEND_TO_SANCTION = "recommend_to_sanction"
LAG_SANCTION_TO_FIRST_PAYMENT = "sanction_to_first_payment"
LAG_FIRST_PAYMENT_TO_COMPLETION = "first_payment_to_completion"
LIFECYCLE_LAGS = (
    LAG_RECOMMEND_TO_SANCTION,
    LAG_SANCTION_TO_FIRST_PAYMENT,
    LAG_FIRST_PAYMENT_TO_COMPLETION,
)

# How many peer works a fired duplicate_work hit cites, and how many peer HIGH
# cases the corroboration block names. Citation is what makes the one
# model-fed rule admissible (DOMAIN-MODEL.md (h)): an officer is handed the
# records, not asked to trust the number. Two is enough to open in two tabs;
# the full cluster size travels alongside.
DUPLICATE_CITATION_LIMIT = 2
CORROBORATION_CITATION_LIMIT = CORROBORATION_MIN_HIGH_CASES

AUDIT_EVENTS = (
    "CASE_OPENED",
    "RULE_FIRED",
    "DUPLICATE_LINKED",
    "PATTERN_LINKED",
    "NOTE_ADDED",
    "SCORE_RECOMPUTED",
    "ALERT_RAISED",
    "ALERT_ESCALATED",
    "RULEBOOK_UPDATED",
    "INGEST_COMPLETED",
)

# --------------------------------------------------------------------------
# Roles (F-auth, DOMAIN-MODEL.md (k))
# --------------------------------------------------------------------------

# The four personas, spelled once. `schemas.py` types itself off these, the
# `users.role` CHECK constraint is built from these, and `audit_log.actor_role`
# is validated against these - so a fifth role is one edit here and nowhere
# else (invariant 7).
ROLE_MINISTRY = "ministry"
ROLE_STATE_NODAL = "state_nodal"
ROLE_DISTRICT_AUTHORITY = "district_authority"
ROLE_MEMBER_OF_PARLIAMENT = "member_of_parliament"

ROLES = (
    ROLE_MINISTRY,
    ROLE_STATE_NODAL,
    ROLE_DISTRICT_AUTHORITY,
    ROLE_MEMBER_OF_PARLIAMENT,
)

# The roles that may write. The member is read-only everywhere: the scheme's
# subject does not adjudicate the scheme's findings (DOMAIN-MODEL.md (k)).
WRITE_ROLES = (ROLE_MINISTRY, ROLE_STATE_NODAL, ROLE_DISTRICT_AUTHORITY)

# How long an issued access token stays valid.
#
# TWELVE HOURS, and that is a demo figure rather than a security one. There is
# no refresh flow, no revocation list and no session store in this prototype,
# so the expiry is the only thing that ends a session: a 30-minute production
# token would put a re-login in the middle of a judging walkthrough, and a
# 30-day one would be indefensible even for a demo. Twelve hours covers one
# working day of the walkthrough and expires before the next.
#
# PROJECT-BRIEF.md already declares the login as a demo over seeded accounts
# rather than an identity provider. This constant is the same statement in a
# number, and it is stated rather than oversold.
TOKEN_TTL_HOURS = 12

# HS256, not RS256. One process signs and the same process verifies; an
# asymmetric pair would add a key-distribution story with no second verifier to
# tell it to.
JWT_ALGORITHM = "HS256"

# The environment variable the signing secret is read from. There is a
# development fallback in `app/auth.py` and it is labelled there, loudly: a
# deployment that does not set this is signing with a value that is in the
# repository, which is a demo posture and is never described as anything else.
JWT_SECRET_ENV = "NIGRANI_JWT_SECRET"

# --------------------------------------------------------------------------
# The synthetic control (docs/contract/fixtures.md, fixture C)
# --------------------------------------------------------------------------

# No real MPLADS row can populate the certification rung, so the only way to
# exercise fund-ladder hop 2 is an injected, labelled row (invariant 12). This
# id is reserved; ingest rejects it with `case_id_collision` if the portal ever
# publishes it (fixtures.md caveat 3).
SYNTHETIC_CONTROL_WORK_ID = "WS/MP503/2025-2026/140882"


# --------------------------------------------------------------------------
# The ML tier (F7) - tiers 3 and 4, badges worth ZERO points
# --------------------------------------------------------------------------

# `ml_findings.kind`. Four kinds, and only the first feeds a rulebook rule:
# `duplicate_work` reads `duplicate_similarity`, and it is admissible only
# because its trace row cites the records the number came from
# (DOMAIN-MODEL.md (h)). The other three are badges. They confirm, or fail to
# confirm, what the rulebook already found; they never move the number
# (CLAUDE.md invariant 1).
ML_KIND_DUPLICATE = "duplicate"
ML_KIND_ANOMALY = "anomaly"
ML_KIND_FORECAST = "forecast"
ML_KIND_GRAPH = "graph"
ML_KINDS = (ML_KIND_DUPLICATE, ML_KIND_ANOMALY, ML_KIND_FORECAST, ML_KIND_GRAPH)

# Fixed so every fit is reproducible: a badge an auditor cannot reproduce is
# worth less than no badge. The number is the date this calibration pass was
# made, carrying no meaning beyond being written down once.
ML_RANDOM_SEED = 20260830

# IsolationForest's expected outlier share.
#
# MEASURED, not defaulted. The forest is fitted on the 3,380 real sanctioned
# works that carry a complete vector over `ml.anomaly.ANOMALY_FEATURES`; on
# that same population the rulebook places 37 in HIGH and 338 in MEDIUM, so
# 375 of 3,380 - 11.09% - sit above the LOW band. Setting the forest's
# flagging rate to the rulebook's own non-LOW rate on the same population is
# what makes a "confirms" badge informative: a detector that flagged 50% of
# the corpus would agree with the rulebook by arithmetic, and one that flagged
# 0.1% would never agree at all. scikit-learn's 'auto' and the conventional
# 0.1 were both rejected as unexamined.
ANOMALY_CONTAMINATION = 0.11

# The smallest peer group in which "unusual among its peers" carries content.
# Peer group is (category, state, financial year) - the group the frozen
# contract already names in its `statistical` block. Measured over the 3,380
# complete vectors: 125 groups, median size 6, largest 439. A floor of 5 sits
# just below that median, keeps 3,261 of the 3,380 works (96.5%) in 67 groups,
# and reports the remaining 119 as `not_applicable` rather than calling a work
# an outlier among two.
ANOMALY_MIN_PEER_GROUP = 5

# Share of the labelled works held out to report the forecast's accuracy.
# The split is GROUPED BY IMPLEMENTING AGENCY, never random: works sanctioned
# by one office in one batch share their features and their fate, so a random
# split puts siblings on both sides and reports a number the model has not
# earned. Measured both ways on this corpus - random holdout AUC 0.962,
# agency-grouped holdout AUC 0.759 - and the grouped figure is the one
# NIGRANI quotes (see `ml/forecast.py`).
FORECAST_HOLDOUT_FRACTION = 0.25
