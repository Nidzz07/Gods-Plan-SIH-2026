"""One loader per CSV. Twelve functions, and nothing but reading.

Two format facts shape every function here (data/raw/README.md):

* The files are UTF-8 **with** a byte-order mark. Read any other way and the
  first column name arrives with a BOM glued to the front of it, so the header
  lookup for `Sr. No.` silently fails on exactly one column per file.

* Column headers embed the rupee sign with irregular spacing -
  `RECOMMENDED AMOUNT   ( ₹ )` has three spaces before the bracket - and the
  same field is spelled `WORK`, `Work` and `Work ID` across the six datasets.
  Headers are therefore matched loosely, never by string equality. `column()`
  strips everything that is not a letter or a digit and lowercases the rest, so
  `RECOMMENDED AMOUNT   ( ₹ )` and `Recommended Amount (Rs)` both resolve.

Every loader returns the DataFrame exactly as read, with two columns added:
`_row_number` (1-based, excluding the header, so it matches what a spreadsheet
shows an officer) and `_source_file`. Nothing is dropped here - not even the
portal's "Grand Total" footer - because a row dropped in a loader is a row
`ingest_rejects` never hears about (CLAUDE.md invariant 11).
"""

from __future__ import annotations

import re

import pandas as pd

from app.constants import (
    DATASET_ALLOCATION,
    DATASET_CALAMITY,
    DATASET_COMPLETED,
    DATASET_EXPENDITURE,
    DATASET_RECOMMENDED,
    DATASET_SANCTIONED,
    HOUSE_LOK_SABHA,
    HOUSE_RAJYA_SABHA,
    RAW_DATA_DIR,
    RAW_ENCODING,
    RAW_FILES,
)

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def loose_key(header: str) -> str:
    """`RECOMMENDED AMOUNT   ( ₹ )` -> `recommendedamount`."""
    return _NON_ALNUM.sub("", str(header).lower())


def column(df: pd.DataFrame, *candidates: str) -> str:
    """Resolve one of `candidates` to a real column name, loosely.

    Exact loose match first, then a containment match, so `Hon'ble Members of
    Parliament` finds `Hon'ble Members of Parliaments` in the Lok Sabha
    allocation file without either spelling being hard-coded twice.
    """
    keyed = {loose_key(col): col for col in df.columns}
    for candidate in candidates:
        key = loose_key(candidate)
        if key in keyed:
            return keyed[key]
    for candidate in candidates:
        key = loose_key(candidate)
        for actual_key, actual in keyed.items():
            if key and (key in actual_key or actual_key in key):
                return actual
    raise KeyError(
        f"none of {candidates!r} matched any column in {list(df.columns)!r}"
    )


def _read(dataset: str, house: str) -> pd.DataFrame:
    """Read one export as strings, with no NA coercion.

    `dtype=str` and `keep_default_na=False` together mean the loader hands on
    exactly what the portal printed. Letting pandas turn `N/A` into a float NaN
    would erase the difference between a field the portal left blank and a
    field it filled with a literal `N/A`, and that difference is what
    `availability` records.
    """
    filename = RAW_FILES[(dataset, house)]
    path = RAW_DATA_DIR / filename
    df = pd.read_csv(path, encoding=RAW_ENCODING, dtype=str, keep_default_na=False)
    df = df.reset_index(drop=True)
    df["_row_number"] = df.index + 1
    df["_source_file"] = filename
    df["_house"] = house
    return df


# --- Works_Recommended -----------------------------------------------------


def load_works_recommended_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_RECOMMENDED, HOUSE_LOK_SABHA)


def load_works_recommended_rajya_sabha() -> pd.DataFrame:
    return _read(DATASET_RECOMMENDED, HOUSE_RAJYA_SABHA)


# --- Works_Sanctioned ------------------------------------------------------


def load_works_sanctioned_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_SANCTIONED, HOUSE_LOK_SABHA)


def load_works_sanctioned_rajya_sabha() -> pd.DataFrame:
    return _read(DATASET_SANCTIONED, HOUSE_RAJYA_SABHA)


# --- Works_Completed -------------------------------------------------------


def load_works_completed_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_COMPLETED, HOUSE_LOK_SABHA)


def load_works_completed_rajya_sabha() -> pd.DataFrame:
    return _read(DATASET_COMPLETED, HOUSE_RAJYA_SABHA)


# --- Expenditure -----------------------------------------------------------


def load_expenditure_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_EXPENDITURE, HOUSE_LOK_SABHA)


def load_expenditure_rajya_sabha() -> pd.DataFrame:
    return _read(DATASET_EXPENDITURE, HOUSE_RAJYA_SABHA)


# --- Allocated_Limit_for_Honble_MPs ----------------------------------------


def load_allocation_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_ALLOCATION, HOUSE_LOK_SABHA)


def load_allocation_rajya_sabha() -> pd.DataFrame:
    """The Rajya Sabha allocation export has no `Constituency` column.

    That is correct rather than a defect: Rajya Sabha members are seated by
    state (DATA-PROFILE.md section 9). The two allocation loaders differ for
    exactly this reason and must not be merged into one.
    """
    return _read(DATASET_ALLOCATION, HOUSE_RAJYA_SABHA)


# --- Amount_consented_for_Calamity -----------------------------------------


def load_calamity_lok_sabha() -> pd.DataFrame:
    return _read(DATASET_CALAMITY, HOUSE_LOK_SABHA)


def load_calamity_rajya_sabha() -> pd.DataFrame:
    return _read(DATASET_CALAMITY, HOUSE_RAJYA_SABHA)


# The twelve, in the order the load report prints them.
ALL_LOADERS = (
    (DATASET_RECOMMENDED, HOUSE_LOK_SABHA, load_works_recommended_lok_sabha),
    (DATASET_RECOMMENDED, HOUSE_RAJYA_SABHA, load_works_recommended_rajya_sabha),
    (DATASET_SANCTIONED, HOUSE_LOK_SABHA, load_works_sanctioned_lok_sabha),
    (DATASET_SANCTIONED, HOUSE_RAJYA_SABHA, load_works_sanctioned_rajya_sabha),
    (DATASET_COMPLETED, HOUSE_LOK_SABHA, load_works_completed_lok_sabha),
    (DATASET_COMPLETED, HOUSE_RAJYA_SABHA, load_works_completed_rajya_sabha),
    (DATASET_EXPENDITURE, HOUSE_LOK_SABHA, load_expenditure_lok_sabha),
    (DATASET_EXPENDITURE, HOUSE_RAJYA_SABHA, load_expenditure_rajya_sabha),
    (DATASET_ALLOCATION, HOUSE_LOK_SABHA, load_allocation_lok_sabha),
    (DATASET_ALLOCATION, HOUSE_RAJYA_SABHA, load_allocation_rajya_sabha),
    (DATASET_CALAMITY, HOUSE_LOK_SABHA, load_calamity_lok_sabha),
    (DATASET_CALAMITY, HOUSE_RAJYA_SABHA, load_calamity_rajya_sabha),
)
