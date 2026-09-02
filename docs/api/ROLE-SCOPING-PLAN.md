# ROLE-SCOPING-PLAN — how each endpoint is scoped

CLAUDE.md invariant 10: *role scoping is enforced server-side, in the query.
Never by hiding rows in the UI. A District Authority token must not be able to
fetch another district's cases by editing a URL.*

Phase 5 built the API layer. **Phase 6 added authentication and implemented
every predicate below.** This document was the commitment made in between: it
named, endpoint by endpoint, the exact predicate that would be added to each
query, so that adding auth would be a filter and not a rewrite. The authority
for what each role may see is `docs/domain/DOMAIN-MODEL.md` §(k).

**Status: implemented.** The predicates live in `backend/app/routers/scoping.py`
and `backend/tests/test_role_scoping.py` asserts them — including a test that
compiles each role's select and reads the `WHERE` clause, because every
response-body test in that file could in principle be satisfied by fetching
everything and dropping rows in Python, which is the failure invariant 10 names.

Three things were carried out differently from the plan below, and both are
recorded here rather than left as a diff to notice:

1. **A District Authority is scoped on `state_id AND district`, not on
   `district` alone.** The plan said `Work.district == D`. The corpus refutes
   it: `AGRA`, `KAITHAL`, `PILIBHIT` and `SHAHJAHANPUR` each name a district in
   five different states of `works`, and eight more names appear in three, so
   the plan's predicate would have handed a Uttar Pradesh officer the Madhya
   Pradesh district of the same name. The implemented predicate is strictly
   narrower than the one promised, which is the safe direction.
2. **`GET /api/audit/chain` is Ministry-only**, which the plan did not mention.
   Every other audit read is scoped by a case; the chain walk is over the whole
   84,629-row trail at once and has no case to be scoped by.
3. **`GET /api/analytics/district/{district}` resolves the district by state and
   name together**, which deviation 1 required and the endpoint did not
   originally do. It looked the name up with `WHERE works.district = :district
   LIMIT 1` and filtered its rollups on the bare name, so for the 61 district
   names that belong to more than one state it picked one arbitrarily: a
   District Authority whose district lost that pick was refused their own queue,
   and the Ministry was handed the several same-named districts summed into one
   row. The state now comes from the caller's own scope for the two roles bound
   to one and from a `?state=` parameter for the Ministry, and every query in
   the endpoint carries both terms. `tests/test_district_collision.py` audits
   all 61.

Everything else is as written below. The original wording is kept in the present
tense because it still describes the code.

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

The `district_authority` row is implemented as `works.state_id == S AND
works.district == D`; see the two deviations above.

The MP role is read-only everywhere. The scheme's subject does not adjudicate
the scheme's findings.

---

## Where the predicate goes, endpoint by endpoint

Every case-bearing query in `routers/` goes through one helper. It moved from
`routers/cases.scoped_cases(db)` to `routers/scoping.scoped_cases(user)` when it
gained a predicate, so that the audit question — *where is the filter?* — has one
answer for the whole package rather than one per router. `scope_works(query,
user)` applies the same predicate to the bare work select and to the ranked-list
join; the three `check_*_grain` functions beside it decide which aggregate views
a role may ask for at all.

| Endpoint | Predicate | Where |
| --- | --- | --- |
| `GET /api/cases` | `Work.state_id == S` · `Work.district == D` · `Work.mp_id == M` | `scoping.scoped_cases()`, before the severity/state/district/agency filters are applied, so a query parameter can only narrow the scope further and never widen it |
| `GET /api/cases/{case_id}` | the same predicate, applied to the single-row select | `cases.get_case()` — the lookup is `scoped_cases(user).where(Case.case_id == case_id)`. A case outside the scope returns **404, not 403**: an officer must not be able to learn that another district's case exists by reading a status code |
| `POST /api/cases/{case_id}/notes` | the same predicate, plus `role != member_of_parliament` | `cases.add_note()` — the case is fetched through `scoped_cases` before anything is written, so an out-of-scope note cannot reach `audit_log` |
| `POST /api/cases/{case_id}/recompute` | the same predicate, plus `role != member_of_parliament` | `cases.recompute_case()` — same fetch, same 404 |
| `GET /api/works/{work_id}` | `Work.state_id == S` · `Work.district == D` · `Work.mp_id == M` | `works.get_work()` — the work select, not a post-filter |
| `GET /api/audit/{case_id}` | the case is fetched through `scoped_cases` first; the trail is then read for that case id. For the MP role, `NOTE_ADDED` rows have their `payload.text` removed — an MP sees that a note was added, by which role and when; the text is the administration's working record (DOMAIN-MODEL.md §(k)) | `audit.get_trail()` |
| `GET /api/analytics/national` | Ministry only. Every other role is redirected to its own grain | `analytics.national()` |
| `GET /api/analytics/state/{state}` | `state == S` for `state_nodal`; Ministry unrestricted; District and MP roles do not reach this grain | `analytics.state_analytics()` |
| `GET /api/analytics/district/{district}` | `district == D` **and `state_id == S`** for `district_authority`; `district` must lie in `S` for `state_nodal`. The state is read from the caller's own row for both, never from the request; the Ministry, which has no state of its own, passes `?state=` and is refused with the candidates named if it omits one on a district name that several states carry | `analytics.district_analytics()` |
| `GET /api/analytics/mp/{mp_id}` | `mp_id == M` for the MP role. **Invisible to `district_authority` entirely** — a district officer has no business seeing an MP's aggregate account position, and the one derived value they need, `mp_utilisation_pct`, reaches them through the case trace where it is already scoped to that case's MP | `analytics.mp_analytics()` |
| `GET /api/rulebook` | readable by all four roles — everyone judged by a rule is entitled to read it, and it names no state, district, agency or member. `PUT`, when it lands, is Ministry-only | `rulebook.get_rulebook()` |
| `GET /api/ablation/report` | Ministry-only. It is a report about MoSPI's own publishing, not a finding about any state, district or member | `ablation.get_report()` |
| `GET /api/audit/chain` | Ministry-only. Not in the original plan: every other audit read is scoped by a case, and this one walks the whole trail | `audit.get_chain()` |
| `POST /api/auth/login` | the only unauthenticated route under `/api`. `GET /api/auth/me` returns exactly one row — the caller's own — which is the narrowest scope there is | `auth.login()` |
| `GET /health` | unauthenticated, deliberately. Liveness plus four counts `DATA-PROFILE.md` already publishes; behind a login, an outage and a bad password would look the same from outside | `main.health()` |

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

## The one thing that is not a filter

`audit_log` for the MP role. Every other scope is a `WHERE` clause; this one is
a redaction of a payload field on rows that are otherwise visible. It is called
out here because it is the only place where the shape of a response changes by
role, and a change of shape is the kind of thing that gets forgotten until a
frontend renders `undefined`.
