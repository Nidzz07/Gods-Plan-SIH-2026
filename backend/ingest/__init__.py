"""Loading the twelve committed MPLADS exports into backend/nigrani.db.

Four modules, in the order the data moves through them:

* `loaders`   - one function per CSV. Reads the file, nothing else.
* `parse`     - work ids, amounts and dates out of portal strings.
* `normalize` - MP names, agency canonicalisation, vendor and state spelling.
* `rejects`   - the closed-enum reject ledger.
* `run`       - orchestration and the load report.

Run it with `python -m ingest.run` from `backend/`.
"""
