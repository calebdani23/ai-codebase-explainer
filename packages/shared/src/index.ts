export type AnalysisMode = 'quick' | 'deep' | 'issue_triage_only';
export type SourceType = 'github' | 'demo' | 'zip';
export type AnalysisStatus = 'pending' | 'analyzing' | 'completed' | 'failed';
export type RiskScore = 'low' | 'medium' | 'high' | 'critical';

export interface RepositoryAnalysisSummary {
  id: string;
  repositoryName: string;
  repositoryUrl?: string;
  branch?: string;
  sourceType: SourceType;
  status: AnalysisStatus;
  analysisMode: AnalysisMode;
  detectedStack: string[];
  filesAnalyzed: number;
  riskScore: RiskScore;
  createdAt: string;
}

export interface SuggestedIssue {
  id: string;
  title: string;
  category: 'bug' | 'security' | 'performance' | 'refactor' | 'testing' | 'docs' | 'architecture' | 'maintainability';
  severity: RiskScore;
  priority: 'p1' | 'p2' | 'p3' | 'p4';
  confidence: number;
  effort: 'small' | 'medium' | 'large';
  relatedFiles: string[];
  githubIssueMarkdown: string;
}
