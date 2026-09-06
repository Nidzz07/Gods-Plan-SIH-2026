// Measured from the twelve published exports of the MPLADS portal.
// See NIGRANI-FRONTEND-PLAN.md §12 and docs/data/DATA-PROFILE.md.
export const CORPUS = {
  worksScored: 27078, // real cases; 27,079 including the labelled control
  rowsIngested: 118704,
  datasets: 12,
  agencies: 638,
  vendors: 15245,
  members: 766,
  states: 31,
  sanctionedCrore: 2107.5,
  allocatedCrore: 23242,
  bands: { high: 37, medium: 1006, low: 26035 },
  corroborated: 191,
  meanCoverage: 58.47,
  rules: 10,
  ruleWeight: 144,
  bonusWeight: 10,
  auditRows: 84666,
  tests: 645,
  duplicateClusters: 447,
  duplicateWorks: 3584,
  duplicateCrore: 157.12,
  degeneracy: { matched: 14831, identical: 14831 },
  ablation: {
    expenditureLinkage: { skips: 70647, works: 23549, coverageTo: 88.91, deltaPp: 30.44 },
    assetEvidence: { skips: 14104, works: 14104, deltaPp: 3.65 },
    zeroFields: 7,
  },
}
