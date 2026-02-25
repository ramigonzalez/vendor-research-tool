/** Core domain types matching the backend Pydantic models */

export type SourceType = 'official_docs' | 'github' | 'comparison' | 'blog' | 'community';
export type CapabilityLevel = 'full' | 'partial' | 'minimal' | 'none' | 'unknown';
export type MaturityLevel = 'ga' | 'beta' | 'experimental' | 'planned' | 'unknown';
export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';
export type Priority = 'high' | 'medium' | 'low';

export interface Evidence {
  claim: string;
  source_url: string;
  source_name: string;
  source_type: SourceType;
  content_date: string | null;
  relevance: number;
  supports_requirement: boolean;
}

export interface ScoreResult {
  score: number;
  confidence: number;
  capability_level: CapabilityLevel;
  maturity: MaturityLevel;
  justification: string;
  limitations: string[];
  evidence: Evidence[];
}

export interface Requirement {
  id: string;
  description: string;
  priority: Priority;
}

export interface VendorRanking {
  vendor: string;
  overall_score: number;
  rank: number;
}

export interface ResearchResults {
  vendors: string[];
  requirements: Requirement[];
  matrix: Record<string, Record<string, ScoreResult>>;
  rankings: VendorRanking[];
  summary: string;
}

export interface ResearchJob {
  id: string;
  status: JobStatus;
  created_at: string;
  completed_at: string | null;
  progress_pct: number;
  progress_message: string;
}

/** SSE Event Types */
export type ResearchPhase = 'idle' | 'planning' | 'searching' | 'analyzing' | 'scoring' | 'ranking' | 'writing' | 'complete' | 'error';

export type StepStatus = 'pending' | 'active' | 'complete';

export interface SSEProgressEvent {
  type: 'progress';
  phase: string;
  pct: number;
  message: string;
}

export interface SSEStartedEvent {
  type: 'started';
  job_id: string;
}

export interface SSECompletedEvent {
  type: 'completed';
  results: ResearchResults;
}

export interface SSEErrorEvent {
  type: 'error';
  message: string;
}

export interface SSEPhaseEvent {
  type: 'phase_start' | 'phase_end';
  phase: string;
  timestamp: string;
}

export interface SSEQueryGeneratedEvent {
  type: 'query_generated';
  vendor: string;
  requirement_id: string;
  queries: string[];
}

export interface SSESearchResultEvent {
  type: 'search_result';
  vendor: string;
  requirement_id: string;
  source_url: string;
  source_name: string;
  domain: string;
}

export interface SSEEvidenceExtractedEvent {
  type: 'evidence_extracted';
  vendor: string;
  requirement_id: string;
  count: number;
  claims: string[];
}

export interface SSEScoreComputedEvent {
  type: 'score_computed';
  vendor: string;
  requirement_id: string;
  score: number;
  confidence: number;
}

export interface SSEVendorRankedEvent {
  type: 'vendor_ranked';
  vendor: string;
  rank: number;
  overall_score: number;
}

export interface SSEWarningEvent {
  type: 'warning';
  vendor: string;
  requirement_id: string;
  message: string;
}

export interface SSEIterationStartEvent {
  type: 'iteration_start';
  iteration: number;
  total_searches: number;
  gap_count: number;
}

export type SSEEvent =
  | SSEProgressEvent
  | SSEStartedEvent
  | SSECompletedEvent
  | SSEErrorEvent
  | SSEPhaseEvent
  | SSEQueryGeneratedEvent
  | SSESearchResultEvent
  | SSEEvidenceExtractedEvent
  | SSEScoreComputedEvent
  | SSEVendorRankedEvent
  | SSEWarningEvent
  | SSEIterationStartEvent;
