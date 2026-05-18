export type AnalysisMode = 'quick' | 'deep' | 'issue_triage_only';
export type SourceType = 'github' | 'demo' | 'zip';
export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'failed';
export type RiskScore = 'low' | 'medium' | 'high' | 'critical';
export type ObservabilityStatus = 'disabled' | 'sent' | 'failed';

export interface CodeFile {
  id: string;
  path: string;
  language: string;
  size_bytes: number;
  is_entry_point: boolean;
  is_important: boolean;
  summary?: string | null;
}

export interface CodeChunk {
  id: string;
  file_id: string;
  file_path: string;
  language: string;
  redacted_content: string;
  start_line: number;
  end_line: number;
  token_estimate?: number | null;
}

export interface ChatSupportingChunk {
  id: string;
  file_path: string;
  language: string;
  start_line: number;
  end_line: number;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  related_files: string[];
  supporting_chunks: ChatSupportingChunk[];
  mode: 'ai' | 'fallback' | 'ai_fallback' | string;
  source: 'openai' | 'deterministic' | 'deterministic_after_ai_error' | string;
  observability_status: ObservabilityStatus | string;
}

export interface RepositoryAnalysisSummary {
  id: string;
  repository_url?: string | null;
  repository_name: string;
  branch?: string | null;
  source_type: SourceType;
  status: AnalysisStatus;
  analysis_mode: AnalysisMode;
  detected_stack: string[];
  languages: Record<string, number>;
  files_analyzed: number;
  total_files_seen: number;
  risk_score: RiskScore;
  summary?: string | null;
  architecture_summary?: string | null;
  duration_ms?: number | null;
  observability_trace_id?: string | null;
  observability_status: ObservabilityStatus | string;
  created_at: string;
  updated_at: string;
}

export interface RepositoryAnalysisDetail extends RepositoryAnalysisSummary {
  files: CodeFile[];
  chunks: CodeChunk[];
  issues: SuggestedIssue[];
}

export interface SuggestedIssue {
  id: string;
  title: string;
  category: 'bug' | 'security' | 'performance' | 'refactor' | 'testing' | 'docs' | 'architecture' | 'maintainability' | string;
  severity: RiskScore;
  priority: 'p1' | 'p2' | 'p3' | 'p4';
  confidence: number;
  effort: 'small' | 'medium' | 'large';
  description: string;
  evidence: string;
  related_files: string[];
  suggested_fix: string;
  github_issue_markdown: string;
  created_at?: string;
}
