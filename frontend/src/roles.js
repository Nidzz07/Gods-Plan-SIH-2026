// The role model, in one place so the sign-in screen, the top bar and the
// sidebar cannot disagree about what a role is or where it lands.

export const MINISTRY = 'ministry'
export const STATE_NODAL = 'state_nodal'
export const DISTRICT_AUTHORITY = 'district_authority'
export const MEMBER_OF_PARLIAMENT = 'member_of_parliament'

export const ROLES = [MINISTRY, STATE_NODAL, DISTRICT_AUTHORITY, MEMBER_OF_PARLIAMENT]

// How a role is written when a person reads it.
export const ROLE_LABEL = {
  [MINISTRY]: 'Ministry',
  [STATE_NODAL]: 'State Nodal Authority',
  [DISTRICT_AUTHORITY]: 'District Authority',
  [MEMBER_OF_PARLIAMENT]: 'Member of Parliament',
}

// Where each role starts.
export const ROLE_HOME = {
  [MINISTRY]: '/ministry',
  [STATE_NODAL]: '/state',
  [DISTRICT_AUTHORITY]: '/district',
  [MEMBER_OF_PARLIAMENT]: '/member',
}

// Structured role nav with primary groups and secondary items (§5.3)
export const ROLE_NAV_CONFIG = {
  [MINISTRY]: {
    primary: [
      { to: '/ministry', label: 'National overview', end: true },
      { to: '/state', label: 'State comparison' },
      { to: '/district', label: 'District queue' },
      { to: '/member', label: 'Member accounts' },
    ],
    secondary: [
      { to: '/rulebook', label: 'Rulebook' },
      { to: '/alerts', label: 'Alerts', showBadge: true },
      { to: '/reports/data-gap', label: 'Data-gap report' },
      { to: '/docs/audit-trail', label: 'Audit trail' },
    ],
  },
  [STATE_NODAL]: {
    primary: [
      { to: '/state', label: 'State overview', end: true },
      { to: '/district', label: 'District queue' },
    ],
    secondary: [
      { to: '/rulebook', label: 'Rulebook' },
      { to: '/alerts', label: 'Alerts', showBadge: true },
    ],
  },
  [DISTRICT_AUTHORITY]: {
    primary: [
      { to: '/district', label: 'District queue', end: true },
    ],
    secondary: [
      { to: '/rulebook', label: 'Rulebook' },
      { to: '/alerts', label: 'Alerts', showBadge: true },
    ],
  },
  [MEMBER_OF_PARLIAMENT]: {
    primary: [
      { to: '/member', label: 'My account', end: true },
    ],
    secondary: [
      { to: '/rulebook', label: 'Rulebook' },
      { to: '/alerts', label: 'Alerts', showBadge: true },
    ],
  },
}

// Flat fallback list for backward compatibility
export const ROLE_NAV = Object.fromEntries(
  Object.entries(ROLE_NAV_CONFIG).map(([role, config]) => [
    role,
    [...config.primary, ...config.secondary],
  ]),
)

const OWNER = Object.fromEntries(Object.entries(ROLE_HOME).map(([role, path]) => [path, role]))

// Returns the path to send this role to, or null to leave them where they are.
export function redirectFor(role, pathname) {
  const owner = OWNER[pathname]
  return owner && owner !== role ? ROLE_HOME[role] : null
}
