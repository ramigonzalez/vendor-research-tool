import { describe, it, expect } from 'vitest'
import type { Evidence, ScoreResult } from './types'
import {
  computeSourceCount,
  computeSourceAuthority,
  computeSourceRecency,
  computeConsistency,
  computeConfidenceBreakdown,
  computeScoreBreakdown,
  CAPABILITY_SCORES,
  MATURITY_SCORES,
  AUTHORITY_WEIGHTS,
  PRIORITY_WEIGHTS,
} from './scoring'

function makeEvidence(overrides: Partial<Evidence> = {}): Evidence {
  return {
    claim: 'Test claim',
    source_url: 'https://example.com',
    source_name: 'Example',
    source_type: 'official_docs',
    content_date: null,
    relevance: 0.8,
    supports_requirement: true,
    ...overrides,
  }
}

function makeScoreResult(overrides: Partial<ScoreResult> = {}): ScoreResult {
  return {
    score: 7.0,
    confidence: 0.8,
    capability_level: 'full',
    maturity: 'ga',
    justification: 'Test justification',
    limitations: [],
    evidence: [makeEvidence()],
    ...overrides,
  }
}

// --- Lookup Table Parity with engine.py ---

describe('CAPABILITY_SCORES', () => {
  it('matches engine.py values', () => {
    expect(CAPABILITY_SCORES.full).toBe(10.0)
    expect(CAPABILITY_SCORES.partial).toBe(7.0)
    expect(CAPABILITY_SCORES.minimal).toBe(3.0)
    expect(CAPABILITY_SCORES.none).toBe(0.0)
    expect(CAPABILITY_SCORES.unknown).toBe(2.0)
  })
})

describe('MATURITY_SCORES', () => {
  it('matches engine.py values', () => {
    expect(MATURITY_SCORES.ga).toBe(10.0)
    expect(MATURITY_SCORES.beta).toBe(7.0)
    expect(MATURITY_SCORES.experimental).toBe(4.0)
    expect(MATURITY_SCORES.planned).toBe(2.0)
    expect(MATURITY_SCORES.unknown).toBe(3.0)
  })
})

describe('AUTHORITY_WEIGHTS', () => {
  it('matches engine.py values', () => {
    expect(AUTHORITY_WEIGHTS.official_docs).toBe(1.0)
    expect(AUTHORITY_WEIGHTS.github).toBe(0.8)
    expect(AUTHORITY_WEIGHTS.comparison).toBe(0.6)
    expect(AUTHORITY_WEIGHTS.blog).toBe(0.4)
    expect(AUTHORITY_WEIGHTS.community).toBe(0.3)
  })
})

describe('PRIORITY_WEIGHTS', () => {
  it('has correct weights', () => {
    expect(PRIORITY_WEIGHTS.high).toBe(3.0)
    expect(PRIORITY_WEIGHTS.medium).toBe(2.0)
    expect(PRIORITY_WEIGHTS.low).toBe(1.0)
  })
})

// --- Confidence Components ---

describe('computeSourceCount', () => {
  it('returns 0 for empty evidence', () => {
    expect(computeSourceCount([])).toBe(0)
  })

  it('returns proportional value for < 5 sources', () => {
    const evidence = [makeEvidence(), makeEvidence(), makeEvidence()]
    expect(computeSourceCount(evidence)).toBeCloseTo(0.6)
  })

  it('caps at 1.0 for >= 5 sources', () => {
    const evidence = Array.from({ length: 7 }, () => makeEvidence())
    expect(computeSourceCount(evidence)).toBe(1.0)
  })
})

describe('computeSourceAuthority', () => {
  it('returns 0 for empty evidence', () => {
    expect(computeSourceAuthority([])).toBe(0)
  })

  it('returns 1.0 for all official_docs', () => {
    const evidence = [makeEvidence({ source_type: 'official_docs' })]
    expect(computeSourceAuthority(evidence)).toBe(1.0)
  })

  it('returns mean of mixed types', () => {
    const evidence = [
      makeEvidence({ source_type: 'official_docs' }), // 1.0
      makeEvidence({ source_type: 'community' }),      // 0.3
    ]
    expect(computeSourceAuthority(evidence)).toBeCloseTo(0.65)
  })
})

describe('computeSourceRecency', () => {
  it('returns 0 for empty evidence', () => {
    expect(computeSourceRecency([])).toBe(0)
  })

  it('returns 0.3 for null content_date', () => {
    const evidence = [makeEvidence({ content_date: null })]
    expect(computeSourceRecency(evidence)).toBeCloseTo(0.3)
  })

  it('returns 1.0 for recent date (within 180 days)', () => {
    const recent = new Date()
    recent.setDate(recent.getDate() - 30)
    const evidence = [makeEvidence({ content_date: recent.toISOString() })]
    expect(computeSourceRecency(evidence)).toBeCloseTo(1.0)
  })

  it('returns 0.7 for date 200 days ago', () => {
    const older = new Date()
    older.setDate(older.getDate() - 200)
    const evidence = [makeEvidence({ content_date: older.toISOString() })]
    expect(computeSourceRecency(evidence)).toBeCloseTo(0.7)
  })

  it('returns 0.3 for date > 365 days ago', () => {
    const old = new Date()
    old.setDate(old.getDate() - 400)
    const evidence = [makeEvidence({ content_date: old.toISOString() })]
    expect(computeSourceRecency(evidence)).toBeCloseTo(0.3)
  })
})

describe('computeConsistency', () => {
  it('returns 0 for empty evidence', () => {
    expect(computeConsistency([])).toBe(0)
  })

  it('returns 1.0 when all support', () => {
    const evidence = [
      makeEvidence({ supports_requirement: true }),
      makeEvidence({ supports_requirement: true }),
    ]
    expect(computeConsistency(evidence)).toBe(1.0)
  })

  it('returns 0.5 when half support', () => {
    const evidence = [
      makeEvidence({ supports_requirement: true }),
      makeEvidence({ supports_requirement: false }),
    ]
    expect(computeConsistency(evidence)).toBe(0.5)
  })
})

// --- Confidence Breakdown ---

describe('computeConfidenceBreakdown', () => {
  it('returns all zeros for empty evidence', () => {
    const result = computeConfidenceBreakdown([])
    expect(result.sourceCount).toBe(0)
    expect(result.authority).toBe(0)
    expect(result.recency).toBe(0)
    expect(result.consistency).toBe(0)
    expect(result.total).toBe(0)
  })

  it('clamps total between 0 and 1', () => {
    const evidence = Array.from({ length: 5 }, () =>
      makeEvidence({
        source_type: 'official_docs',
        content_date: new Date().toISOString(),
        supports_requirement: true,
      })
    )
    const result = computeConfidenceBreakdown(evidence)
    expect(result.total).toBeGreaterThanOrEqual(0)
    expect(result.total).toBeLessThanOrEqual(1)
  })

  it('computes correct weighted total', () => {
    // Single official_docs, no date, supports = true
    const evidence = [makeEvidence({ content_date: null, supports_requirement: true })]
    const result = computeConfidenceBreakdown(evidence)
    // sourceCount: min(1,5)/5 = 0.2
    // authority: 1.0 (official_docs)
    // recency: 0.3 (null date)
    // consistency: 1.0 (all support)
    const expected = 0.30 * 0.2 + 0.30 * 1.0 + 0.25 * 0.3 + 0.15 * 1.0
    expect(result.total).toBeCloseTo(expected)
  })
})

// --- Score Breakdown ---

describe('computeScoreBreakdown', () => {
  it('computes full capability + GA maturity + no limitations', () => {
    const sr = makeScoreResult({
      capability_level: 'full',
      maturity: 'ga',
      limitations: [],
      evidence: Array.from({ length: 5 }, () =>
        makeEvidence({ supports_requirement: true })
      ),
    })
    const result = computeScoreBreakdown(sr)
    expect(result.capabilityScore).toBe(10.0)
    expect(result.maturityScore).toBe(10.0)
    expect(result.limitationsScore).toBe(10.0)
    expect(result.evidenceScore).toBe(10.0)
    // 0.40*10 + 0.30*10 + 0.20*10 + 0.10*10 = 10.0
    expect(result.total).toBeCloseTo(10.0)
  })

  it('computes partial capability + beta maturity + 2 limitations', () => {
    const sr = makeScoreResult({
      capability_level: 'partial',
      maturity: 'beta',
      limitations: ['limit1', 'limit2'],
      evidence: [
        makeEvidence({ supports_requirement: true }),
        makeEvidence({ supports_requirement: true }),
        makeEvidence({ supports_requirement: false }),
      ],
    })
    const result = computeScoreBreakdown(sr)
    expect(result.capabilityScore).toBe(7.0) // partial
    expect(result.maturityScore).toBe(7.0) // beta
    expect(result.limitationsScore).toBe(6.0) // 10 - 2*2
    expect(result.evidenceScore).toBeCloseTo(4.0) // min(2,5)/5 * 10
    // 0.40*7.0 + 0.30*4.0 + 0.20*7.0 + 0.10*6.0 = 2.8+1.2+1.4+0.6 = 6.0
    expect(result.total).toBeCloseTo(6.0)
  })

  it('clamps total between 0 and 10', () => {
    const sr = makeScoreResult({
      capability_level: 'none',
      maturity: 'planned',
      limitations: ['a', 'b', 'c', 'd', 'e', 'f'],
      evidence: [],
    })
    const result = computeScoreBreakdown(sr)
    expect(result.total).toBeGreaterThanOrEqual(0)
    expect(result.total).toBeLessThanOrEqual(10)
  })

  it('limits limitations score to 0 (no negative)', () => {
    const sr = makeScoreResult({
      limitations: ['a', 'b', 'c', 'd', 'e', 'f'], // 6 limitations -> 10 - 12 = -2 -> clamped to 0
    })
    const result = computeScoreBreakdown(sr)
    expect(result.limitationsScore).toBe(0)
  })
})
