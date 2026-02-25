/**
 * Client-side scoring formulas — mirrors vendor-research-tool-backend/app/scoring/engine.py
 * Update this file when the Python scoring logic changes.
 */

import type { CapabilityLevel, Evidence, MaturityLevel, ScoreResult } from './types'

// --- Capability Scores ---
export const CAPABILITY_SCORES: Record<CapabilityLevel, number> = {
  full: 10.0,
  partial: 7.0,
  minimal: 3.0,
  none: 0.0,
  unknown: 2.0,
}

// --- Maturity Scores ---
export const MATURITY_SCORES: Record<MaturityLevel, number> = {
  ga: 10.0,
  beta: 7.0,
  experimental: 4.0,
  planned: 2.0,
  unknown: 3.0,
}

// --- Authority Weights ---
export const AUTHORITY_WEIGHTS: Record<string, number> = {
  official_docs: 1.0,
  github: 0.8,
  comparison: 0.6,
  blog: 0.4,
  community: 0.3,
}

// --- Confidence Component Weights ---
const WEIGHT_SOURCE_COUNT = 0.30
const WEIGHT_SOURCE_AUTHORITY = 0.30
const WEIGHT_SOURCE_RECENCY = 0.25
const WEIGHT_CONSISTENCY = 0.15

export function computeSourceCount(evidence: Evidence[]): number {
  return Math.min(evidence.length, 5) / 5
}

export function computeSourceAuthority(evidence: Evidence[]): number {
  if (evidence.length === 0) return 0
  const total = evidence.reduce((sum, e) => sum + (AUTHORITY_WEIGHTS[e.source_type] ?? 0.3), 0)
  return total / evidence.length
}

function computeRecencyScore(contentDate: string | null): number {
  if (!contentDate) return 0.3
  try {
    const parsed = new Date(contentDate)
    const ageDays = (Date.now() - parsed.getTime()) / (1000 * 60 * 60 * 24)
    if (ageDays <= 180) return 1.0
    if (ageDays <= 365) return 0.7
    return 0.3
  } catch {
    return 0.3
  }
}

export function computeSourceRecency(evidence: Evidence[]): number {
  if (evidence.length === 0) return 0
  const total = evidence.reduce((sum, e) => sum + computeRecencyScore(e.content_date), 0)
  return total / evidence.length
}

export function computeConsistency(evidence: Evidence[]): number {
  if (evidence.length === 0) return 0
  const supporting = evidence.filter(e => e.supports_requirement).length
  return supporting / evidence.length
}

export interface ConfidenceBreakdownResult {
  sourceCount: number
  authority: number
  recency: number
  consistency: number
  total: number
}

export function computeConfidenceBreakdown(evidence: Evidence[]): ConfidenceBreakdownResult {
  if (evidence.length === 0) {
    return { sourceCount: 0, authority: 0, recency: 0, consistency: 0, total: 0 }
  }
  const sourceCount = computeSourceCount(evidence)
  const authority = computeSourceAuthority(evidence)
  const recency = computeSourceRecency(evidence)
  const consistency = computeConsistency(evidence)
  const total = Math.max(0, Math.min(1,
    WEIGHT_SOURCE_COUNT * sourceCount +
    WEIGHT_SOURCE_AUTHORITY * authority +
    WEIGHT_SOURCE_RECENCY * recency +
    WEIGHT_CONSISTENCY * consistency
  ))
  return { sourceCount, authority, recency, consistency, total }
}

export interface ScoreBreakdownResult {
  capabilityScore: number
  evidenceScore: number
  maturityScore: number
  limitationsScore: number
  total: number
}

export function computeScoreBreakdown(scoreResult: ScoreResult): ScoreBreakdownResult {
  const capabilityScore = CAPABILITY_SCORES[scoreResult.capability_level] ?? 2.0
  const supportingCount = scoreResult.evidence.filter(e => e.supports_requirement).length
  const evidenceScore = (Math.min(supportingCount, 5) / 5) * 10
  const maturityScore = MATURITY_SCORES[scoreResult.maturity] ?? 3.0
  const limitationsScore = Math.max(0, 10 - scoreResult.limitations.length * 2)

  const total = Math.max(0, Math.min(10,
    0.40 * capabilityScore +
    0.30 * evidenceScore +
    0.20 * maturityScore +
    0.10 * limitationsScore
  ))

  return { capabilityScore, evidenceScore, maturityScore, limitationsScore, total }
}

// --- Priority Weights ---
export const PRIORITY_WEIGHTS: Record<string, number> = {
  high: 3.0,
  medium: 2.0,
  low: 1.0,
}
