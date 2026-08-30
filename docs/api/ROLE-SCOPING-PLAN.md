# ROLE-SCOPING-PLAN — how each endpoint will be scoped in Phase 7

CLAUDE.md invariant 10: *role scoping is enforced server-side, in the query.
Never by hiding rows in the UI. A District Authority token must not be able to
fetch another district's cases by editing a URL.*

Phase 5 built the API layer. Phase 7 adds authentication. This document is the
commitment made in between: it names, endpoint by endpoint, the exact predicate
that will be added to each query, so that adding auth is a filter and not a
rewrite. The authority for what each role may see is
`docs/domain/DOMAIN-MODEL.md` §(k).

**Nothing here is implemented yet, and the code says so.** Every router in
`backend/app/routers/` reads today as if the caller were the Ministry role,
which is the widest scope, so no endpoint is currently narrower than it will
be — adding auth can only remove rows, never add them. That direction matters:
a scope that had to be widened later would mean the demo had been showing
officers less than they are entitled to, and a scope that has to be narrowed is
the ordinary case.

---

## The four scopes

Let `S` = the user's state id, `D` = the user's district, `M` = the user's MP
id, taken from the authenticated token and never from a query parameter.

| Role | Scope | Write? |
| --- | --- | --- |
| `ministry` | everything | rulebook, notes, recompute, escalation |
| `state_nodal` | `works.state_id == S` | notes, recompute, escalation |
| `district_authority` | `works.district == D` | notes, recompute, escalation |
| `member_of_parliament` | `works.mp_id == M` | **nothing. Read-only** |

The MP role is read-only everywhere. The scheme's subject does not adjudicate
the scheme's findings.

---

## Where the predicate goes, endpoint by endpoint

Every case-bearing query in `routers/` already goes through one helper,
`routers/cases.scoped_cases(db)`, which today returns the unfiltered select.
Phase 7 changes that one function and the four endpoints below inherit it.

| Endpoint | Predicate added in Phase 7 | Where |
| --- | --- | --- |
| `GET /api/cases` | `Work.state_id == S` · `Work.district == D` · `Work.mp_id == M` | `cases.scoped_cases()`, before the severity/state/district/agency filters are applied, so a query parameter can only narrow the scope further and never widen it |
| `GET /api/cases/{case_id}` | the same predicate, applied to the single-row select | `cases.get_case()` — the lookup becomes `scoped_cases(db).where(Case.case_id == case_id)`. A case outside the scope returns **404, not 403**: an officer must not be able to learn that another district's case exists by reading a status code |
| `POST /api/cases/{case_id}/notes` | the same predicate, plus `role != member_of_parliament` | `cases.add_note()` — the case is fetched through `scoped_cases` before anything is written, so an out-of-scope note cannot reach `audit_log` |
| `POST /api/cases/{case_id}/recompute` | the same predicate, plus `role != member_of_parliament` | `cases.recompute_case()` — same fetch, same 404 |
| `GET /api/works/{work_id}` | `Work.state_id == S` · `Work.district == D` · `Work.mp_id == M` | `works.get_work()` — the work select, not a post-filter |
| `GET /api/audit/{case_id}` | the case is fetched through `scoped_cases` first; the trail is then read for that case id. For the MP role, `NOTE_ADDED` rows have their `payload.text` removed — an MP sees that a note was added, by which role and when; the text is the administration's working record (DOMAIN-MODEL.md §(k)) | `audit.get_trail()` |
| `GET /api/analytics/national` | Ministry only. Every other role is redirected to its own grain | `analytics.national()` |
| `GET /api/analytics/state/{state}` | `state == S` for `state_nodal`; Ministry unrestricted; District and MP roles do not reach this grain | `analytics.state_analytics()` |
| `GET /api/analytics/district/{district}` | `district == D` for `district_authority`; `district` must lie in `S` for `state_nodal` | `analytics.district_analytics()` |
| `GET /api/analytics/mp/{mp_id}` | `mp_id == M` for the MP role. **Invisible to `district_authority` entirely** — a district officer has no business seeing an MP's aggregate account position, and the one derived value they need, `mp_utilisation_pct`, reaches them through the case trace where it is already scoped to that case's MP | `analytics.mp_analytics()` |
| `GET /api/rulebook` | readable by all four roles. `PUT` (Phase 7) is Ministry-only | `rulebook.get_rulebook()` |
| `GET /api/ablation/report` | Ministry-only. It is a report about MoSPI's own publishing, not a finding about any state, district or member | `ablation.get_report()` |

## Three things this plan deliberately does not do

**It does not scope by filtering a result list in Python.** Every predicate
above is a `WHERE` clause on the select that fetches the rows. A list
comprehension after `.all()` would be scoping in the application, and the row
would already have left the database — which is the failure invariant 10 names.

**It does not add a `role` query parameter.** The role comes from the token
and nothing else. An endpoint that accepted `?role=ministry` would be an
endpoint with no scoping at all.

**It does not make the pre-aggregated rollups role-aware.** `rollup_state`,
`rollup_district`, `rollup_agency` and `rollup_mp` (`app/derive_all.py`) are
aggregates over the whole corpus, and a role reads the rows of the grain it is
entitled to rather than a differently-computed aggregate. A State Nodal officer
reading `rollup_district WHERE state_id = S` sees exactly the districts in
their state, computed the same way the Ministry's copy was — so two officers
can never be shown two different numbers for the same district.

## The one thing Phase 7 must add that is not a filter

`audit_log` for the MP role. Every other scope is a `WHERE` clause; this one is
a redaction of a payload field on rows that are otherwise visible. It is called
out here because it is the only place where the shape of a response changes by
role, and a change of shape is the kind of thing that gets forgotten until a
frontend renders `undefined`.
