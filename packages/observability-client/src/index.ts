export type TraceStep = {
  step_type?: 'user_message' | 'tool_call' | 'retrieval' | 'llm_call' | 'final_response' | 'error';
  name: string;
  input?: unknown;
  output?: unknown;
  metadata?: Record<string, unknown>;
};

export type TracePayload = {
  app_name?: string;
  session_id?: string;
  operation: 'analyze_repository' | 'detect_stack' | 'generate_architecture_summary' | 'generate_issue_triage' | 'ask_codebase' | string;
  model?: string;
  provider?: string;
  status: 'success' | 'error' | 'disabled';
  input_tokens?: number;
  output_tokens?: number;
  metadata?: Record<string, unknown>;
  steps: TraceStep[];
};

export type ObservabilityClientConfig = {
  enabled: boolean;
  apiUrl?: string;
  ingestApiKey?: string;
  appName: string;
};

export function createObservabilityClient(config: ObservabilityClientConfig) {
  const enabled = Boolean(config.enabled && config.apiUrl);

  return {
    isEnabled: enabled,
    async captureTrace(payload: TracePayload): Promise<{ status: 'disabled' | 'sent' | 'failed'; traceId?: string }> {
      if (!enabled) {
        return { status: 'disabled' };
      }

      try {
        const response = await fetch(`${config.apiUrl!.replace(/\/$/, '')}/api/traces`, {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            ...(config.ingestApiKey ? { authorization: `Bearer ${config.ingestApiKey}` } : {}),
          },
          body: JSON.stringify({ app_name: config.appName, ...payload }),
        });

        if (!response.ok) return { status: 'failed' };
        const data = (await response.json().catch(() => ({}))) as { trace_id?: string; id?: string };
        return { status: 'sent', traceId: data.trace_id ?? data.id };
      } catch (error) {
        console.warn('Observability trace failed; continuing without blocking.', error);
        return { status: 'failed' };
      }
    },
  };
}
