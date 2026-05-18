import { Link, Route, Routes } from 'react-router-dom';

import type { AnalysisMode } from '@ai-codebase-explainer/shared';
import { createObservabilityClient } from '@ai-codebase-explainer/observability-client';

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
const repoUrl = import.meta.env.VITE_REPO_URL ?? 'https://github.com/YOUR_USERNAME/ai-codebase-explainer';
const dashboardUrl = import.meta.env.VITE_OBSERVABILITY_DASHBOARD_URL ?? 'https://calebdani23.github.io/ai-agent-observability-dashboard/';
const demoMode = import.meta.env.VITE_DEMO_MODE !== 'false';

const observability = createObservabilityClient({
  enabled: false,
  appName: 'ai-codebase-explainer-web',
});

const modes: AnalysisMode[] = ['quick', 'deep', 'issue_triage_only'];

function Landing() {
  return (
    <main className="hero-grid">
      <section className="hero-card">
        <span className="eyebrow">AI engineering portfolio project</span>
        <h1>AI Codebase Explainer & Issue Triage</h1>
        <p className="lead">Understand repositories, map architecture and generate actionable engineering issues with AI.</p>
        <div className="actions">
          <Link className="button primary" to="/analyze">Analyze Repository</Link>
          <Link className="button" to="/analyze?demo=true">Try Demo Repository</Link>
          <a className="button ghost" href={repoUrl}>View GitHub</a>
        </div>
        <div className="badges">
          <span>{demoMode ? 'Demo mode ready' : 'AI mode ready'}</span>
          <span>GitHub Pages compatible</span>
          <span>FastAPI backend</span>
        </div>
      </section>
      <section className="panel">
        <h2>What it will analyze</h2>
        <div className="feature-list">
          {['Architecture summary', 'Stack detection', 'AI issue triage', 'Ask your codebase', 'Observability integrated'].map((feature) => (
            <article key={feature}>
              <strong>{feature}</strong>
              <p>Phase-ready foundation for repository analysis workflows.</p>
            </article>
          ))}
        </div>
      </section>
      <section className="panel wide">
        <h2>Instrumented with AI Agent Observability Dashboard</h2>
        <p>
          This project is designed to send optional traces for repository analysis runs, including tool usage,
          LLM calls, latency, cost estimates and errors. Telemetry is non-blocking and disabled unless backend
          observability variables are configured.
        </p>
        <a href={dashboardUrl}>Open observability dashboard</a>
      </section>
    </main>
  );
}

function Analyze() {
  void observability.captureTrace({ operation: 'view_analyze_page', status: 'disabled', steps: [] });
  return (
    <main className="page-card">
      <span className="eyebrow">Repository intake foundation</span>
      <h1>Analyze a repository</h1>
      <form className="form">
        <label>
          GitHub Repository URL
          <input placeholder="https://github.com/example/repo" />
        </label>
        <label>
          Branch <small>optional</small>
          <input placeholder="main" />
        </label>
        <label>
          Analysis mode
          <select defaultValue="quick">
            {modes.map((mode) => <option key={mode} value={mode}>{mode}</option>)}
          </select>
        </label>
        <label className="checkbox">
          <input type="checkbox" defaultChecked /> Use demo repository if no URL is provided
        </label>
        <label className="checkbox">
          <input type="checkbox" /> Send telemetry to observability dashboard
        </label>
        <button className="button primary" type="button">Start Analysis (Phase 2)</button>
      </form>
      <p className="security-note">Security note: MVP analysis is for public repositories only. Do not submit private repos or secrets.</p>
    </main>
  );
}

function Health() {
  return (
    <main className="page-card">
      <h1>Backend health</h1>
      <p>API URL: <code>{apiUrl}</code></p>
      <p>Check locally with <code>curl {apiUrl}/health</code>.</p>
    </main>
  );
}

export function App() {
  return (
    <div>
      <header className="topbar">
        <Link className="brand" to="/">AI Codebase Explainer</Link>
        <nav>
          <Link to="/analyze">Analyze</Link>
          <Link to="/health">Health</Link>
          <a href={dashboardUrl}>Observability</a>
        </nav>
      </header>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/health" element={<Health />} />
      </Routes>
    </div>
  );
}
