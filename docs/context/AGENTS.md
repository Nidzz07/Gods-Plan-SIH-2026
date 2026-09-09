# AGENTS.md — Antigravity Agent Guidelines

This repository implements NIGRANI, an explainable fund-oversight system for MPLADS.
Read `CLAUDE.md` and `docs/domain/DOMAIN-MODEL.md` for full project architecture and conventions.

## Key Invariants

1. **Rulebook only scores**: The composite score comes strictly from the rulebook and corroboration bonus; ML models (anomaly, forecast, graph) are badges worth zero points.
2. **Missing data is skipped**: Skipped rules lower `coverage_pct` and never silently pass or redistribute weights.
3. **Declared hops/lags are computed**: Every hop/lag named in schemas or ladders has an active derivation function.
4. **Append-only audit trail**: `audit_log` allows no UPDATE or DELETE anywhere in the backend codebase.
7. **No UI redesign**: Government-oversight visual language is locked (`docs/design/REDESIGN-SPEC.md`). No arbitrary styling or unsolicited animations.

## Deployment & Database Artifact Rule

- Production deploys the prebuilt database artifact `backend/nigrani.db.gz` to Render Free (512 MB ceiling) rather than rebuilding from raw CSVs.
- **Rule**: Re-derive and re-compress `backend/nigrani.db.gz` whenever `rules.yaml`, data ingestion, or feature derivation logic changes. An un-regenerated artifact will cause the live deployment to serve scores computed under stale rules, violating reproducibility.
