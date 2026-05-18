import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';

import type { AnalysisMode } from '@ai-codebase-explainer/shared';

const browserHost = typeof window !== 'undefined' ? window.location.hostname : '';
const isLocalBrowser = browserHost === 'localhost' || browserHost === '127.0.0.1';
const apiUrl = (import.meta.env.VITE_API_URL || (isLocalBrowser ? 'http://localhost:8000' : '')).replace(/\/$/, '');
const apiTimeoutMs = Number(import.meta.env.VITE_API_TIMEOUT_MS || 15000);
const repoUrl = import.meta.env.VITE_REPO_URL || 'https://github.com/YOUR_USERNAME/ai-codebase-explainer';
const dashboardUrl = import.meta.env.VITE_OBSERVABILITY_DASHBOARD_URL || 'https://calebdani23.github.io/ai-agent-observability-dashboard/';
const frontendDemoMode = import.meta.env.VITE_DEMO_MODE !== 'false';

type RiskScore = 'low' | 'medium' | 'high' | 'critical';

type CodeFile = {
  id: string;
  path: string;
  language: string;
  size_bytes: number;
  is_entry_point: boolean;
  is_important: boolean;
  summary?: string | null;
};

type CodeChunk = {
  id: string;
  file_id: string;
  file_path: string;
  language: string;
  redacted_content: string;
  start_line: number;
  end_line: number;
  token_estimate?: number | null;
};

type SuggestedIssue = {
  id: string;
  title: string;
  category: string;
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
};

type AnalysisDetail = {
  id: string;
  repository_url?: string | null;
  repository_name: string;
  branch?: string | null;
  source_type: 'github' | 'demo' | 'zip';
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
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
  observability_status: 'disabled' | 'sent' | 'failed' | string;
  observability_operations?: string[];
  observability_steps?: Record<string, unknown>[];
  observability_error?: string | null;
  created_at: string;
  updated_at: string;
  files: CodeFile[];
  chunks: CodeChunk[];
  issues: SuggestedIssue[];
};

type PublicConfig = {
  demo_mode?: boolean;
  observability_enabled?: boolean;
  service?: string;
};

type ChatSupportingChunk = {
  id: string;
  file_path: string;
  language: string;
  start_line: number;
  end_line: number;
  snippet: string;
  score: number;
};

type ChatApiResponse = {
  answer: string;
  related_files: string[];
  supporting_chunks: ChatSupportingChunk[];
  mode: string;
  source: string;
  observability_status: string;
};

type ChatTurn = {
  id: string;
  question: string;
  response: ChatApiResponse;
};

type ObservabilityDetail = {
  enabled: boolean;
  status: string;
  trace_id?: string | null;
  app_name: string;
  operations: string[];
  steps: Record<string, unknown>[];
  dashboard_url?: string | null;
  error?: string | null;
};

type TreeNode = {
  name: string;
  path: string;
  type: 'folder' | 'file';
  children: TreeNode[];
  file?: CodeFile;
};

const modes: { value: AnalysisMode; label: string; help: string }[] = [
  { value: 'quick', label: 'Quick Scan', help: 'Fast stack, architecture and issue signals.' },
  { value: 'deep', label: 'Deep Scan', help: 'Uses the backend\'s broader static scanner limits.' },
  { value: 'issue_triage_only', label: 'Issue Triage Only', help: 'Focuses on actionable tickets and risk.' },
];

const demoAnalysis: AnalysisDetail = {
  id: 'local_demo_react_fastapi_saas',
  repository_url: 'https://github.com/demo/react-fastapi-saas',
  repository_name: 'react-fastapi-saas',
  branch: 'main',
  source_type: 'demo',
  status: 'completed',
  analysis_mode: 'quick',
  detected_stack: ['React', 'TypeScript', 'Vite', 'FastAPI', 'SQLModel', 'PostgreSQL', 'Docker'],
  languages: { TypeScript: 48, Python: 32, Markdown: 12, YAML: 8 },
  files_analyzed: 42,
  total_files_seen: 68,
  risk_score: 'medium',
  summary: 'Demo SaaS repository with a React/Vite frontend, FastAPI backend, SQLModel persistence and deployment scaffolding. The codebase is small enough for quick onboarding and highlights the main production-readiness gaps teams usually triage first.',
  architecture_summary: 'The app follows a split frontend/backend architecture. apps/web owns the client experience and API calls, apps/api exposes health and analysis endpoints, packages/shared carries contracts, and docs plus examples support deployment and deterministic demos.',
  duration_ms: 1800,
  observability_trace_id: 'trace_demo_local_001',
  observability_status: 'disabled',
  observability_operations: ['analyze_repository', 'load_demo_repo', 'detect_stack', 'generate_architecture_summary', 'generate_issue_triage', 'persist_analysis'],
  observability_steps: [
    { step_type: 'tool_call', name: 'load_demo_repo', output: 'react-fastapi-saas' },
    { step_type: 'tool_call', name: 'detect_stack', output: ['React', 'FastAPI', 'PostgreSQL'] },
    { step_type: 'llm_call', name: 'generate_issue_triage', output: 'Generated demo issues with deterministic heuristics' },
  ],
  observability_error: null,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  files: [
    { id: 'f1', path: 'apps/web/src/App.tsx', language: 'TypeScript', size_bytes: 14500, is_entry_point: true, is_important: true, summary: 'Primary React route shell and product UI.' },
    { id: 'f2', path: 'apps/web/src/styles.css', language: 'CSS', size_bytes: 12000, is_entry_point: false, is_important: true, summary: 'CSS-only SaaS dashboard styling.' },
    { id: 'f3', path: 'apps/api/main.py', language: 'Python', size_bytes: 5200, is_entry_point: true, is_important: true, summary: 'FastAPI routes for health, config, analyses, issues and exports.' },
    { id: 'f4', path: 'apps/api/services/repository_analysis.py', language: 'Python', size_bytes: 16000, is_entry_point: false, is_important: true, summary: 'Static GitHub repository scanner and analysis pipeline.' },
    { id: 'f5', path: 'apps/api/services/issue_generation.py', language: 'Python', size_bytes: 8800, is_entry_point: false, is_important: true, summary: 'Heuristic and optional AI issue generation.' },
    { id: 'f6', path: 'packages/shared/src/index.ts', language: 'TypeScript', size_bytes: 2200, is_entry_point: false, is_important: false, summary: 'Shared TypeScript contracts.' },
    { id: 'f7', path: 'docs/observability-integration.md', language: 'Markdown', size_bytes: 4100, is_entry_point: false, is_important: false, summary: 'Portfolio story and trace integration documentation.' },
  ],
  chunks: [
    { id: 'c1', file_id: 'f3', file_path: 'apps/api/main.py', language: 'Python', redacted_content: 'FastAPI app exposes /health, /api/config, demo analysis, public GitHub analysis, analysis detail, issue and export endpoints.', start_line: 37, end_line: 139 },
    { id: 'c2', file_id: 'f4', file_path: 'apps/api/services/repository_analysis.py', language: 'Python', redacted_content: 'Downloads public GitHub ZIP archives, applies static safety filters, redacts secret-like content and persists files/chunks.', start_line: 1, end_line: 180 },
  ],
  issues: [
    {
      id: 'i1',
      title: 'Add end-to-end coverage for repository intake flow',
      category: 'testing',
      severity: 'medium',
      priority: 'p2',
      confidence: 0.87,
      effort: 'medium',
      description: 'The analysis workflow depends on frontend/API coordination, but the demo has no browser-level coverage for success and fallback paths.',
      evidence: 'No Playwright or Cypress config detected in the scanned files.',
      related_files: ['apps/web/src/App.tsx', 'apps/api/main.py'],
      suggested_fix: 'Add a smoke test that starts the app, runs demo analysis and verifies overview, file tree and issues table render.',
      github_issue_markdown: '## Problem\nThe repository intake flow lacks end-to-end coverage.\n\n## Evidence\nNo browser test config was detected.\n\n## Suggested fix\nAdd a smoke test for demo analysis and issue triage views.',
    },
    {
      id: 'i2',
      title: 'Document production database requirements in deploy checklist',
      category: 'docs',
      severity: 'low',
      priority: 'p3',
      confidence: 0.78,
      effort: 'small',
      description: 'SQLite is fine locally, but hosted deployments should make the Postgres requirement unmissable.',
      evidence: 'README mentions SQLite fallback and Postgres for production.',
      related_files: ['README.md', 'docs/deployment.md'],
      suggested_fix: 'Add a short deployment checklist item requiring DATABASE_URL from Neon, Supabase or another Postgres-compatible provider.',
      github_issue_markdown: '## Problem\nProduction database setup can be missed during deploy.\n\n## Suggested fix\nAdd a checklist for DATABASE_URL and CORS before publishing the backend.',
    },
  ],
};

function storeLocalAnalysis(analysis: AnalysisDetail) {
  sessionStorage.setItem(`analysis:${analysis.id}`, JSON.stringify(analysis));
}

function getStoredAnalysis(id: string) {
  const raw = sessionStorage.getItem(`analysis:${id}`);
  return raw ? (JSON.parse(raw) as AnalysisDetail) : null;
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  if (!apiUrl) {
    throw new Error('Hosted backend API is not configured. Set VITE_API_URL to your Render/Koyeb backend URL and redeploy GitHub Pages.');
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), apiTimeoutMs);

  let response: Response;
  try {
    response = await fetch(`${apiUrl}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error(`The backend did not respond within ${Math.round(apiTimeoutMs / 1000)} seconds. Check VITE_API_URL, backend health, or use demo fallback.`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function useApiConfig() {
  const [config, setConfig] = useState<PublicConfig | null>(null);
  useEffect(() => {
    apiRequest<PublicConfig>('/api/config').then(setConfig).catch(() => setConfig({ demo_mode: frontendDemoMode, observability_enabled: false }));
  }, []);
  return config;
}

function modeLabel(analysis?: AnalysisDetail | null, config?: PublicConfig | null) {
  if (!analysis) return frontendDemoMode ? 'Demo mode ready' : 'API mode';
  if (analysis.source_type === 'demo' || analysis.id.startsWith('local_demo')) return 'Demo / deterministic mode';
  if (config?.demo_mode === false) return 'AI-assisted mode available';
  return 'Static scanner mode';
}

function statusClass(value: string) {
  return `badge ${value.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`;
}

function formatDuration(ms?: number | null) {
  if (!ms) return '—';
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

function buildTree(files: CodeFile[]) {
  const root: TreeNode = { name: 'repository', path: '', type: 'folder', children: [] };
  files.forEach((file) => {
    const parts = file.path.split('/');
    let node = root;
    parts.forEach((part, index) => {
      const childPath = parts.slice(0, index + 1).join('/');
      let child = node.children.find((item) => item.name === part);
      if (!child) {
        child = { name: part, path: childPath, type: index === parts.length - 1 ? 'file' : 'folder', children: [] };
        node.children.push(child);
      }
      if (index === parts.length - 1) child.file = file;
      node = child;
    });
  });
  const sort = (node: TreeNode) => {
    node.children.sort((a, b) => (a.type === b.type ? a.name.localeCompare(b.name) : a.type === 'folder' ? -1 : 1));
    node.children.forEach(sort);
  };
  sort(root);
  return root;
}

function inferPurpose(path: string, type: 'file' | 'folder') {
  const lower = path.toLowerCase();
  if (type === 'folder') {
    if (lower.includes('api')) return 'Backend/API surface or server-side services.';
    if (lower.includes('web') || lower.includes('src')) return 'Frontend application code and UI behavior.';
    if (lower.includes('docs')) return 'Documentation and portfolio/deployment narrative.';
    if (lower.includes('services')) return 'Business logic and integration boundary.';
    return 'Project area grouping related files.';
  }
  if (lower.endsWith('main.py') || lower.endsWith('app.py')) return 'Backend application entry point.';
  if (lower.endsWith('app.tsx') || lower.endsWith('main.tsx')) return 'Frontend application entry point or route shell.';
  if (lower.includes('issue')) return 'Issue triage or finding generation logic.';
  if (lower.includes('observability')) return 'Trace/instrumentation integration.';
  if (lower.endsWith('.md')) return 'Human-readable product or engineering documentation.';
  return 'Analyzed source file used to understand stack and architecture.';
}

function importantFolders(analysis: AnalysisDetail) {
  const folders = new Map<string, number>();
  analysis.files.forEach((file) => {
    const [first, second] = file.path.split('/');
    const key = second ? `${first}/${second}` : first;
    folders.set(key, (folders.get(key) ?? 0) + 1);
  });
  return [...folders.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
}

function Shell({ children }: { children: React.ReactNode }) {
  const config = useApiConfig();
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">
          <span className="brand-mark">AI</span>
          <span>Codebase Explainer</span>
        </Link>
        <nav>
          <NavLink to="/analyze">Analyze</NavLink>
          <a href={dashboardUrl}>Observability Dashboard</a>
          <a href={repoUrl}>GitHub</a>
        </nav>
        <span className="mode-pill">{config?.demo_mode ?? frontendDemoMode ? 'Demo mode enabled' : 'Live API mode'}</span>
      </header>
      {children}
    </div>
  );
}

function Landing() {
  const proofPoints = [
    ['42', 'demo files analyzed'],
    ['5', 'product surfaces'],
    ['0', 'frontend secrets'],
  ];

  return (
    <main className="hero-grid">
      <section className="hero-card glow-card">
        <span className="eyebrow">Portfolio-ready AI engineering product</span>
        <h1>AI Codebase Explainer & Issue Triage</h1>
        <p className="lead">Turn a public GitHub repository into an architecture brief, stack map, risk review and copy-ready engineering backlog in minutes.</p>
        <div className="actions">
          <Link className="button primary" to="/analyze">Analyze Repository</Link>
          <Link className="button" to="/analyze?demo=true">Try Demo Repository</Link>
          <a className="button ghost" href={repoUrl}>View GitHub</a>
        </div>
        <div className="proof-grid">
          {proofPoints.map(([value, label]) => <article key={label}><strong>{value}</strong><span>{label}</span></article>)}
        </div>
        <div className="badges">
          <span>Static scanner fallback</span>
          <span>No frontend secrets</span>
          <span>GitHub Pages ready</span>
        </div>
      </section>

      <section className="panel product-card product-preview">
        <span className="eyebrow">Live product shape</span>
        <h2>From repo URL to engineering decision pack</h2>
        <div className="preview-window">
          <div className="window-bar"><i /><i /><i /></div>
          <div className="preview-metrics">
            <article><span>Risk</span><strong>medium</strong></article>
            <article><span>Issues</span><strong>8 drafts</strong></article>
            <article><span>Trace</span><strong>sent</strong></article>
          </div>
          <div className="preview-list">
            <p><b>Architecture:</b> React/Vite frontend, FastAPI backend, SQLModel persistence.</p>
            <p><b>Top issue:</b> Add intake flow smoke tests before scaling analysis modes.</p>
            <p><b>Ask:</b> “Which files should I read first?” returns file-backed context.</p>
          </div>
        </div>
      </section>

      <section className="panel wide quick-story">
        <div>
          <span className="eyebrow">What it proves</span>
          <h2>A practical AI tool, not a toy chat demo</h2>
          <p>It demonstrates product thinking, static-analysis safety, deterministic fallbacks, backend-owned secrets, exportable artifacts and observability-first AI engineering.</p>
        </div>
        <div className="feature-list">
          {[
            ['Architecture summary', 'High-level explanation of structure, entry points and important modules.'],
            ['Stack detection', 'Language and framework signals extracted from repository files.'],
            ['AI issue triage', 'Prioritized tickets with evidence, confidence, effort and markdown export.'],
            ['Ask your codebase', 'Contextual Q&A over persisted analysis chunks with related files.'],
            ['Observability integrated', 'Trace status surfaced in the UI for the portfolio story.'],
          ].map(([feature, text]) => (
            <article key={feature}>
              <strong>{feature}</strong>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel wide workflow-strip">
        {['Submit public repo or demo', 'Scan safely without execution', 'Map stack and architecture', 'Generate issue drafts', 'Inspect trace story'].map((step, index) => (
          <article key={step}><span>{index + 1}</span><strong>{step}</strong></article>
        ))}
      </section>

      <section className="panel wide observability-story">
        <div>
          <span className="eyebrow">Portfolio integration</span>
          <h2>Built after, and instrumented by, AI Agent Observability Dashboard</h2>
          <p>
            First came the observability platform for AI agents. This project is the next layer: a repository-analysis product that can emit non-blocking traces for scans, retrieval, LLM calls, issue triage, latency and errors into that dashboard.
          </p>
        </div>
        <a className="button" href={dashboardUrl}>Open dashboard</a>
      </section>
    </main>
  );
}

function Analyze() {
  const location = useLocation();
  const navigate = useNavigate();
  const config = useApiConfig();
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [branch, setBranch] = useState('');
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('quick');
  const [demoRepo, setDemoRepo] = useState('react-fastapi-saas');
  const [useDemo, setUseDemo] = useState(new URLSearchParams(location.search).get('demo') === 'true');
  const [sendObservability, setSendObservability] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!useDemo && !/^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(repositoryUrl.trim())) {
      setError('Enter a public GitHub repository URL like https://github.com/octocat/Hello-World, or choose the demo repository.');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = useDemo
        ? await apiRequest<{ analysis_id: string; analysis: AnalysisDetail }>('/api/demo/analyze', {
            method: 'POST',
            body: JSON.stringify({ demo_repo: demoRepo, analysis_mode: analysisMode, send_observability: sendObservability }),
          })
        : await apiRequest<{ analysis_id: string; analysis: AnalysisDetail }>('/api/repositories/analyze', {
            method: 'POST',
            body: JSON.stringify({ repository_url: repositoryUrl.trim(), branch: branch.trim() || undefined, analysis_mode: analysisMode, send_observability: sendObservability }),
          });
      sessionStorage.setItem(`analysis:${response.analysis_id}`, JSON.stringify(response.analysis));
      navigate(`/analysis/${response.analysis_id}`);
    } catch (err) {
      if (useDemo && (config?.demo_mode ?? frontendDemoMode)) {
        const local = { ...demoAnalysis, id: `local_demo_${Date.now()}`, analysis_mode: analysisMode, observability_status: sendObservability ? 'failed' : 'disabled' };
        storeLocalAnalysis(local);
        navigate(`/analysis/${local.id}`);
      } else {
        setError(err instanceof Error ? err.message : 'Analysis request failed. Try the demo repository fallback.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="page-grid intake-page">
      <section className="page-card">
        <span className="eyebrow">Repository intake</span>
        <h1>Analyze a repository</h1>
        <p className="muted">Run a public GitHub repository through the static scanner or use the deterministic demo path for presentations.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label className={useDemo ? 'disabled' : ''}>
            GitHub Repository URL
            <input disabled={useDemo} value={repositoryUrl} onChange={(event) => setRepositoryUrl(event.target.value)} placeholder="https://github.com/octocat/Hello-World" />
          </label>
          <label className={useDemo ? 'disabled' : ''}>
            Branch <small>optional</small>
            <input disabled={useDemo} value={branch} onChange={(event) => setBranch(event.target.value)} placeholder="main" />
          </label>
          <label>
            Analysis mode
            <select value={analysisMode} onChange={(event) => setAnalysisMode(event.target.value as AnalysisMode)}>
              {modes.map((mode) => <option key={mode.value} value={mode.value}>{mode.label}</option>)}
            </select>
            <small>{modes.find((mode) => mode.value === analysisMode)?.help}</small>
          </label>
          <label>
            Demo Repository
            <select value={demoRepo} onChange={(event) => setDemoRepo(event.target.value)}>
              <option value="react-fastapi-saas">react-fastapi-saas</option>
            </select>
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={useDemo} onChange={(event) => setUseDemo(event.target.checked)} /> Use demo repository
          </label>
          <label className="checkbox">
            <input type="checkbox" checked={sendObservability} onChange={(event) => setSendObservability(event.target.checked)} /> Send telemetry to observability dashboard
          </label>
          {error && <p className="error-box">{error}</p>}
          <button className="button primary" disabled={isSubmitting} type="submit">{isSubmitting ? 'Analyzing…' : 'Start Analysis'}</button>
        </form>
      </section>

      <aside className="panel sticky-panel">
        <span className="eyebrow">Safety model</span>
        <h2>Public, static analysis only</h2>
        <p className="security-note">No GitHub tokens are requested in the frontend. Do not submit private repositories or secrets. The backend downloads public repositories, filters heavy/generated paths, redacts secret-like values and never executes repository code.</p>
        <div className="callout"><strong>Fallback:</strong> If the API is unavailable, demo mode can still open a deterministic local analysis so the frontend flow remains presentable.</div>
      </aside>
    </main>
  );
}

function useAnalysis() {
  const { id } = useParams();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    const stored = getStoredAnalysis(id);
    if (stored) {
      setAnalysis(stored);
      setLoading(false);
    }
    apiRequest<AnalysisDetail>(`/api/analyses/${id}`)
      .then((remote) => {
        setAnalysis(remote);
        storeLocalAnalysis(remote);
        setError(null);
      })
      .catch((err) => {
        if (!stored) setError(err instanceof Error ? err.message : 'Unable to load analysis.');
      })
      .finally(() => setLoading(false));
  }, [id]);

  return { analysis, loading, error };
}

function AnalysisLayout({ children, analysis }: { children: React.ReactNode; analysis: AnalysisDetail }) {
  return (
    <main className="analysis-layout">
      <aside className="analysis-sidebar">
        <Link className="back-link" to="/analyze">← New analysis</Link>
        <h2>{analysis.repository_name}</h2>
        <p>{analysis.repository_url ?? 'Demo repository'}</p>
        <span className={statusClass(analysis.status)}>{analysis.status}</span>
        <nav className="side-nav">
          <NavLink end to={`/analysis/${analysis.id}`}>Overview</NavLink>
          <NavLink to={`/analysis/${analysis.id}/architecture`}>Architecture</NavLink>
          <NavLink to={`/analysis/${analysis.id}/issues`}>Issues</NavLink>
          <NavLink to={`/analysis/${analysis.id}/chat`}>Ask your codebase</NavLink>
          <NavLink to={`/analysis/${analysis.id}/observability`}>Observability</NavLink>
        </nav>
      </aside>
      <section className="analysis-content">{children}</section>
    </main>
  );
}

function AnalysisGate({ render }: { render: (analysis: AnalysisDetail) => React.ReactNode }) {
  const { analysis, loading, error } = useAnalysis();
  if (loading && !analysis) return <main className="page-card"><h1>Loading analysis…</h1></main>;
  if (error && !analysis) return <main className="page-card"><h1>Analysis unavailable</h1><p className="error-box">{error}</p><Link className="button" to="/analyze?demo=true">Try demo fallback</Link></main>;
  if (!analysis) return null;
  return <AnalysisLayout analysis={analysis}>{render(analysis)}</AnalysisLayout>;
}

function Overview() {
  const config = useApiConfig();
  return <AnalysisGate render={(analysis) => {
    const folders = importantFolders(analysis);
    const entryPoints = analysis.files.filter((file) => file.is_entry_point || file.is_important).slice(0, 6);
    return (
      <div className="stacked">
        <div className="section-heading">
          <div>
            <span className="eyebrow">Analysis overview</span>
            <h1>{analysis.repository_name}</h1>
          </div>
          <span className="mode-pill strong">{modeLabel(analysis, config)}</span>
        </div>

        <div className="metric-grid">
          <Metric label="Repository" value={analysis.repository_name} />
          <Metric label="Branch" value={analysis.branch ?? 'main'} />
          <Metric label="Status" value={analysis.status} badge />
          <Metric label="Files analyzed" value={`${analysis.files_analyzed}/${analysis.total_files_seen}`} />
          <Metric label="Languages" value={Object.keys(analysis.languages).join(', ') || '—'} />
          <Metric label="Stack" value={analysis.detected_stack.slice(0, 3).join(', ') || '—'} />
          <Metric label="Risk" value={analysis.risk_score} badge />
          <Metric label="Suggested issues" value={String(analysis.issues.length)} />
          <Metric label="Duration" value={formatDuration(analysis.duration_ms)} />
          <Metric label="Trace status" value={analysis.observability_status} badge />
        </div>

        <section className="panel"><h2>Executive Summary</h2><p>{analysis.summary ?? 'No summary was returned for this analysis.'}</p></section>
        <section className="panel"><h2>Architecture Summary</h2><p>{analysis.architecture_summary ?? 'No architecture summary was returned for this analysis.'}</p></section>

        <div className="two-col">
          <section className="panel">
            <h2>Detected Stack</h2>
            <div className="chip-row">{analysis.detected_stack.map((item) => <span className="chip" key={item}>{item}</span>)}</div>
            <h3>Language mix</h3>
            {Object.entries(analysis.languages).map(([language, percent]) => <div className="bar" key={language}><span>{language}</span><div><i style={{ width: `${Math.min(percent, 100)}%` }} /></div><b>{percent}%</b></div>)}
          </section>
          <section className="panel">
            <h2>Important Folders</h2>
            <ul className="clean-list">{folders.map(([folder, count]) => <li key={folder}><strong>{folder}</strong><span>{count} analyzed files</span></li>)}</ul>
          </section>
        </div>

        <section className="panel">
          <h2>Main Entry Points</h2>
          <div className="file-card-grid">{entryPoints.map((file) => <FileCard file={file} key={file.id} />)}</div>
        </section>

        <section className="panel">
          <div className="split-heading"><h2>Suggested Issues</h2><Link to={`/analysis/${analysis.id}/issues`}>Open triage table →</Link></div>
          <div className="issue-preview">{analysis.issues.slice(0, 3).map((issue) => <IssueRow issue={issue} key={issue.id} compact />)}</div>
        </section>

        <section className="panel observability-story">
          <div><h2>Observability Trace</h2><p>Trace status is <strong>{analysis.observability_status}</strong>{analysis.observability_trace_id ? ` with ID ${analysis.observability_trace_id}` : '. No trace ID was returned.'}</p></div>
          <Link className="button" to={`/analysis/${analysis.id}/observability`}>View trace story</Link>
        </section>
      </div>
    );
  }} />;
}

function Metric({ label, value, badge }: { label: string; value: string; badge?: boolean }) {
  return <article className="metric"><span>{label}</span>{badge ? <b className={statusClass(value)}>{value}</b> : <strong>{value}</strong>}</article>;
}

function FileCard({ file }: { file: CodeFile }) {
  return <article className="file-card"><strong>{file.path}</strong><p>{file.summary ?? inferPurpose(file.path, 'file')}</p><div><span>{file.language}</span>{file.is_entry_point && <span>entry point</span>}{file.is_important && <span>important</span>}</div></article>;
}

function Architecture() {
  return <AnalysisGate render={(analysis) => <ArchitectureContent analysis={analysis} />} />;
}

function ArchitectureContent({ analysis }: { analysis: AnalysisDetail }) {
  const tree = useMemo(() => buildTree(analysis.files), [analysis.files]);
  const [selected, setSelected] = useState<TreeNode>(() => tree.children[0] ?? tree);
  const relatedChunk = analysis.chunks.find((chunk) => chunk.file_path === selected.path);
  return (
    <div className="stacked">
      <div className="section-heading"><div><span className="eyebrow">Architecture explorer</span><h1>File tree & module map</h1></div><span className="mode-pill">{analysis.files.length} files</span></div>
      <div className="explorer">
        <section className="tree-panel panel"><TreeView node={tree} selectedPath={selected.path} onSelect={setSelected} /></section>
        <section className="panel detail-panel">
          <span className="eyebrow">Selected {selected.type}</span>
          <h2>{selected.path || 'repository'}</h2>
          <p>{selected.file?.summary ?? inferPurpose(selected.path, selected.type)}</p>
          <div className="detail-grid">
            <Metric label="Type" value={selected.type} />
            <Metric label="Language" value={selected.file?.language ?? 'mixed'} />
            <Metric label="Importance" value={selected.file?.is_important || selected.file?.is_entry_point ? 'high' : 'normal'} badge />
            <Metric label="Size" value={selected.file ? `${Math.round(selected.file.size_bytes / 1024)} KB` : `${selected.children.length} children`} />
          </div>
          <h3>Why it matters</h3>
          <p>{selected.file?.is_entry_point ? 'Entry points are often the safest starting place for onboarding and risk review.' : 'This node contributes to stack detection, architecture mapping and issue evidence.'}</p>
          <h3>Recommendations</h3>
          <ul>
            <li>Keep ownership and purpose documented for this area.</li>
            <li>Prioritize tests around entry points and important service boundaries.</li>
            <li>Review related issues before modifying this module.</li>
          </ul>
          {relatedChunk && <pre className="code-snippet">{relatedChunk.redacted_content}</pre>}
        </section>
      </div>
    </div>
  );
}

function TreeView({ node, selectedPath, onSelect }: { node: TreeNode; selectedPath: string; onSelect: (node: TreeNode) => void }) {
  return <ul className="tree-list"><li><button className={selectedPath === node.path ? 'selected' : ''} onClick={() => onSelect(node)}>{node.type === 'folder' ? '▸' : '•'} {node.name}</button>{node.children.length > 0 && <ul>{node.children.map((child) => <TreeView key={child.path} node={child} selectedPath={selectedPath} onSelect={onSelect} />)}</ul>}</li></ul>;
}

function Issues() {
  return <AnalysisGate render={(analysis) => <IssuesContent analysis={analysis} />} />;
}

function IssuesContent({ analysis }: { analysis: AnalysisDetail }) {
  const [selected, setSelected] = useState<SuggestedIssue | null>(analysis.issues[0] ?? null);
  const [copied, setCopied] = useState(false);
  async function copyIssue() {
    if (!selected) return;
    await navigator.clipboard.writeText(selected.github_issue_markdown);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }
  return (
    <div className="stacked">
      <div className="section-heading"><div><span className="eyebrow">Issue triage</span><h1>Suggested engineering issues</h1></div><span className="mode-pill">Copy-ready Markdown only</span></div>
      <div className="issues-layout">
        <section className="panel table-panel">
          <table>
            <thead><tr><th>Priority</th><th>Severity</th><th>Category</th><th>Title</th><th>Confidence</th><th>Effort</th><th>Related files</th><th>Status</th></tr></thead>
            <tbody>{analysis.issues.map((issue) => <IssueRow issue={issue} key={issue.id} onSelect={() => setSelected(issue)} selected={selected?.id === issue.id} />)}</tbody>
          </table>
        </section>
        <aside className="panel issue-detail">
          {selected ? <>
            <span className={statusClass(selected.severity)}>{selected.severity}</span>
            <h2>{selected.title}</h2>
            <p>{selected.description}</p>
            <h3>Evidence</h3><p>{selected.evidence}</p>
            <h3>Suggested fix</h3><p>{selected.suggested_fix}</p>
            <h3>Related files</h3><div className="chip-row">{selected.related_files.map((file) => <span className="chip" key={file}>{file}</span>)}</div>
            <div className="split-heading"><h3>GitHub Issue Markdown</h3><button className="button" onClick={copyIssue}>{copied ? 'Copied!' : 'Copy Markdown'}</button></div>
            <pre className="markdown-box">{selected.github_issue_markdown}</pre>
          </> : <p>No issues were generated for this analysis.</p>}
        </aside>
      </div>
    </div>
  );
}

function IssueRow({ issue, onSelect, selected, compact }: { issue: SuggestedIssue; onSelect?: () => void; selected?: boolean; compact?: boolean }) {
  if (compact) return <article className="mini-issue"><span className={statusClass(issue.priority)}>{issue.priority}</span><strong>{issue.title}</strong><span>{issue.category}</span></article>;
  return <tr className={selected ? 'selected-row' : ''} onClick={onSelect}><td><span className={statusClass(issue.priority)}>{issue.priority}</span></td><td><span className={statusClass(issue.severity)}>{issue.severity}</span></td><td>{issue.category}</td><td><button className="link-button">{issue.title}</button></td><td>{Math.round(issue.confidence * 100)}%</td><td>{issue.effort}</td><td>{issue.related_files.slice(0, 2).join(', ') || '—'}</td><td><span className="badge draft">draft</span></td></tr>;
}

function ChatShell() {
  return <AnalysisGate render={(analysis) => <ChatContent analysis={analysis} />} />;
}

function ChatContent({ analysis }: { analysis: AnalysisDetail }) {
  const [question, setQuestion] = useState('Where are the most important files?');
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const important = analysis.files.filter((file) => file.is_important || file.is_entry_point).slice(0, 5);

  function localChatFallback(prompt: string, reason = 'frontend_fallback'): ChatApiResponse {
    const lower = prompt.toLowerCase();
    const related = important.map((file) => file.path);
    const filesText = related.length ? related.map((file) => `\`${file}\``).join(', ') : 'the entry points listed in the overview';
    let answer = `I could not reach the backend chat endpoint, so this is a presentation-safe local fallback. Start with ${filesText}. The analysis risk score is ${analysis.risk_score} and there are ${analysis.issues.length} suggested issues.`;
    if (lower.includes('risk') || lower.includes('issue')) {
      const topIssues = analysis.issues.slice(0, 3).map((issue) => `${issue.severity} ${issue.category}: ${issue.title}`).join('; ');
      answer = `The main risks are ${topIssues || 'represented by the current risk score and issue table'}. Related files: ${filesText}.`;
    } else if (lower.includes('test')) {
      answer = `Add tests around ${filesText} first. Prioritize API contract smoke tests, UI intake flow coverage and service-level tests for the highest-risk issue categories.`;
    } else if (lower.includes('backend') || lower.includes('architecture')) {
      answer = `${analysis.architecture_summary ?? analysis.summary ?? 'The analysis summary is unavailable.'} Related files: ${filesText}.`;
    }
    return {
      answer,
      related_files: related,
      supporting_chunks: important.map((file) => ({ id: file.id, file_path: file.path, language: file.language, start_line: 1, end_line: 1, snippet: file.summary ?? inferPurpose(file.path, 'file'), score: 1 })),
      mode: reason,
      source: 'local_demo',
      observability_status: 'disabled',
    };
  }

  async function askChat(prompt = question) {
    const trimmed = prompt.trim();
    if (!trimmed || isAsking) return;
    setQuestion(trimmed);
    setIsAsking(true);
    setError(null);
    try {
      const response = await apiRequest<ChatApiResponse>(`/api/analyses/${analysis.id}/chat`, {
        method: 'POST',
        body: JSON.stringify({ message: trimmed }),
      });
      setTurns((current) => [{ id: `${Date.now()}`, question: trimmed, response }, ...current].slice(0, 6));
    } catch (err) {
      const fallback = localChatFallback(trimmed, 'api_unavailable_fallback');
      setTurns((current) => [{ id: `${Date.now()}`, question: trimmed, response: fallback }, ...current].slice(0, 6));
      setError(err instanceof Error ? 'Backend chat unavailable; showing local fallback.' : 'Backend chat unavailable; showing local fallback.');
    } finally {
      setIsAsking(false);
    }
  }

  const latest = turns[0]?.response ?? localChatFallback(question, analysis.source_type === 'demo' ? 'demo_preview' : 'static_preview');
  return (
    <div className="stacked">
      <div className="section-heading"><div><span className="eyebrow">Ask your codebase</span><h1>Contextual Q&A</h1></div><span className="mode-pill">{latest.mode} · {latest.source}</span></div>
      <section className="panel chat-panel">
        <form className="chat-message user" onSubmit={(event) => { event.preventDefault(); void askChat(); }}>
          <strong>You</strong>
          <div className="chat-input-row"><input value={question} onChange={(event) => setQuestion(event.target.value)} /><button className="button primary" disabled={isAsking} type="submit">{isAsking ? 'Asking…' : 'Ask'}</button></div>
        </form>
        {error && <p className="callout">{error}</p>}
        <div className="chat-message assistant"><strong>Assistant</strong><p>{latest.answer}</p><div className="chip-row">{latest.related_files.map((file) => <span className="chip" key={file}>{file}</span>)}</div><small>Mode: {latest.mode} · Observability: {latest.observability_status}</small></div>
        {latest.supporting_chunks.length > 0 && <div className="supporting-snippets">{latest.supporting_chunks.slice(0, 3).map((chunk) => <article key={chunk.id}><strong>{chunk.file_path}:{chunk.start_line}-{chunk.end_line}</strong><pre>{chunk.snippet}</pre></article>)}</div>}
      </section>
      <section className="panel"><h2>Suggested prompts</h2><div className="prompt-grid">{['Where is authentication handled?', 'What files would I modify to add payments?', 'What are the main risks in this repo?', 'Explain the backend architecture.', 'Which tests should be added first?'].map((prompt) => <button key={prompt} onClick={() => void askChat(prompt)}>{prompt}</button>)}</div></section>
      {turns.length > 1 && <section className="panel"><h2>Recent questions</h2><div className="chat-history">{turns.slice(1).map((turn) => <article key={turn.id}><strong>{turn.question}</strong><p>{turn.response.answer}</p></article>)}</div></section>}
    </div>
  );
}

function ObservabilityView() {
  return <AnalysisGate render={(analysis) => <ObservabilityContent analysis={analysis} />} />;
}

function ObservabilityContent({ analysis }: { analysis: AnalysisDetail }) {
  const config = useApiConfig();
  const [detail, setDetail] = useState<ObservabilityDetail>(() => ({
    enabled: config?.observability_enabled ?? false,
    status: analysis.observability_status,
    trace_id: analysis.observability_trace_id,
    app_name: 'ai-codebase-explainer',
    operations: analysis.observability_operations ?? [],
    steps: analysis.observability_steps ?? [],
    dashboard_url: dashboardUrl,
    error: analysis.observability_error,
  }));

  useEffect(() => {
    apiRequest<ObservabilityDetail>(`/api/analyses/${analysis.id}/observability`)
      .then((remote) => setDetail({ ...remote, dashboard_url: remote.dashboard_url || dashboardUrl }))
      .catch(() => setDetail((current) => ({ ...current, dashboard_url: dashboardUrl })));
  }, [analysis.id]);

  const operations = detail.operations.length ? detail.operations : ['analyze_repository', 'detect_stack', 'generate_architecture_summary', 'generate_issue_triage', 'ask_codebase'];
  const steps = detail.steps.length ? detail.steps : [
    { step_type: 'tool_call', name: 'scan_repository', output: `${analysis.files_analyzed}/${analysis.total_files_seen} files analyzed` },
    { step_type: 'tool_call', name: 'detect_stack', output: analysis.detected_stack },
    { step_type: 'llm_call', name: 'generate_issue_triage', output: `${analysis.issues.length} issues available` },
  ];
  const enabledText = detail.enabled ? 'Enabled on backend' : 'Disabled or not configured';
  const traceHint = detail.status === 'sent' ? 'Trace delivery succeeded.' : detail.status === 'failed' ? 'Trace delivery failed, but the product flow continued.' : 'Telemetry was not sent because the backend integration is disabled or no trace was requested.';
  return (
    <div className="stacked">
      <div className="section-heading"><div><span className="eyebrow">Observability integration</span><h1>Trace status & portfolio story</h1></div><span className={statusClass(detail.status)}>{detail.status}</span></div>
      <section className="panel observability-dashboard">
        <div className="trace-card"><span>Enabled</span><strong>{enabledText}</strong></div>
        <div className="trace-card"><span>Trace ID</span><strong>{detail.trace_id ?? 'Not generated'}</strong></div>
        <div className="trace-card"><span>Status</span><strong>{detail.status}</strong></div>
        <div className="trace-card"><span>App</span><strong>{detail.app_name}</strong></div>
        <div className="trace-card"><span>Dashboard</span><a href={dashboardUrl}>Open dashboard</a></div>
      </section>
      <section className="panel">
        <h2>Send status</h2>
        <p>{traceHint}</p>
        {detail.error && <p className="error-box">Last send error: {detail.error}</p>}
      </section>
      <section className="panel">
        <h2>Operations represented</h2>
        <div className="chip-row">{operations.map((operation) => <span className="chip" key={operation}>{operation}</span>)}</div>
      </section>
      <section className="panel">
        <h2>Step summary sent to the dashboard</h2>
        <div className="timeline">{steps.map((step, index) => {
          const name = String(step.name ?? 'unnamed_step');
          const type = String(step.step_type ?? 'step');
          const output = typeof step.output === 'string' ? step.output : JSON.stringify(step.output ?? step.metadata ?? {});
          return <article key={`${name}-${index}`}><span>{index + 1}</span><div><strong>{name}</strong><p>{type} · {output || 'No output summary recorded.'}</p></div></article>;
        })}</div>
      </section>
      <section className="panel"><h2>How this connects to the prior dashboard</h2><p>When backend observability variables are configured, repository analysis and chat emit non-blocking traces to the AI Agent Observability Dashboard with tool calls, retrieval, LLM calls, final responses and errors. The ingest key stays backend-only; GitHub Pages only receives safe status metadata.</p></section>
    </div>
  );
}

function Health() {
  const config = useApiConfig();
  return <main className="page-card"><span className="eyebrow">Backend connection</span><h1>API health</h1><p>API URL: <code>{apiUrl}</code></p><p>Public config: <code>{JSON.stringify(config ?? { loading: true })}</code></p></main>;
}

export function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/analysis/:id" element={<Overview />} />
        <Route path="/analysis/:id/architecture" element={<Architecture />} />
        <Route path="/analysis/:id/issues" element={<Issues />} />
        <Route path="/analysis/:id/chat" element={<ChatShell />} />
        <Route path="/analysis/:id/observability" element={<ObservabilityView />} />
        <Route path="/health" element={<Health />} />
      </Routes>
    </Shell>
  );
}
