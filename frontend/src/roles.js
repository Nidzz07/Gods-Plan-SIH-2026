// The role model, in one place so the sign-in screen, the top bar and the
// sidebar cannot disagree about what a role is or where it lands.
//
// WHAT CHANGED, and it is the whole of Phase 6 arriving on the client. The
// inherited version opened with a warning that its roles were "wayfinding...
// not access control", that "the API answers the same rows whichever role is
// set", and that "the role itself is picked from a list with no password".
// None of that is true here. There is a login, passwords are bcrypt digests,
// sessions carry a signed token, and every predicate deciding which rows exist
// is a WHERE clause in the server's query (invariant 10) — a District
// Authority editing a URL gets a 404, not another district's case.
//
// WHAT IS STILL ONLY WAYFINDING, so nobody reads more into this file than it
// does: which links get drawn and which screen a person lands on. Nothing here
// protects anything. A person who edits `user.role` in the devtools gets a
// differently-shaped menu over exactly the same rows, because the rows were
// decided before they ever left the database.
//
// The four ids are the server's own strings, from backend/app/constants.py.
// They are not re-spelled prettily here: the value that arrives in
// `user.role`, the value in the `users.role` CHECK constraint and the value
// this file keys on have to be one string, or a role will silently match
// nothing and land on a blank menu.

export const MINISTRY = 'ministry'
export const STATE_NODAL = 'state_nodal'
export const DISTRICT_AUTHORITY = 'district_authority'
export const MEMBER_OF_PARLIAMENT = 'member_of_parliament'

export const ROLES = [MINISTRY, STATE_NODAL, DISTRICT_AUTHORITY, MEMBER_OF_PARLIAMENT]

// How a role is written when a person reads it. The server sends
// `district_authority`; a heading says "District Authority".
export const ROLE_LABEL = {
  [MINISTRY]: 'Ministry',
  [STATE_NODAL]: 'State Nodal Authority',
  [DISTRICT_AUTHORITY]: 'District Authority',
  [MEMBER_OF_PARLIAMENT]: 'Member of Parliament',
}

// Where each role starts. Four roles, four distinct landing routes, and none
// of them is `/` — a shared index would mean one screen guessing which of four
// dashboards it was, which is the guess the router should be making.
export const ROLE_HOME = {
  [MINISTRY]: '/ministry',
  [STATE_NODAL]: '/state',
  [DISTRICT_AUTHORITY]: '/district',
  [MEMBER_OF_PARLIAMENT]: '/member',
}

// The nav, per role. Case Detail is deliberately NOT on any of these lists any
// more: the inherited nav carried a hardcoded `/cases/C-0041` so the shell
// could be walked before the list was real, and a link to one fixed case id is
// exactly the kind of thing that survives into a demo and 404s in front of a
// judge — a case id is reachable from a queue, not from a menu.
//
// The rulebook is on all four lists, and that is a decision from the scoping
// matrix rather than an oversight: everyone judged by a rule is entitled to
// read the rule. Writing it is Ministry-only, and the server enforces that.
export const ROLE_NAV = {
  [MINISTRY]: [{ to: '/ministry', label: 'National overview', end: true }],
  [STATE_NODAL]: [{ to: '/state', label: 'State overview', end: true }],
  [DISTRICT_AUTHORITY]: [{ to: '/district', label: 'Case queue', end: true }],
  [MEMBER_OF_PARLIAMENT]: [{ to: '/member', label: 'My account', end: true }],
}

// Which role owns each landing route. A role standing on another role's
// landing screen is sent to its own; everything absent from this map — a case
// sheet, the 404 — belongs to no role and nobody is moved off it.
//
// This is not what stops a State Nodal officer reading the Ministry's national
// rollup. `GET /api/analytics/national` is behind require_role(ministry) and
// answers 403 whoever asks; this map only means they do not arrive at a screen
// whose only content is going to be that 403.
const OWNER = Object.fromEntries(Object.entries(ROLE_HOME).map(([role, path]) => [path, role]))

// Returns the path to send this role to, or null to leave them where they are.
export function redirectFor(role, pathname) {
  const owner = OWNER[pathname]
  return owner && owner !== role ? ROLE_HOME[role] : null
}
