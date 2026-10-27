import type { Trace } from '../api/types';
import { formatDuration, summarizeOutput } from '../utils';
import { Panel } from './Panel';

type TracePanelProps = {
  traces: Trace[];
  loading: boolean;
};

export function TracePanel({ traces, loading }: TracePanelProps) {
  return (
    <Panel
      title="Agent trace"
      description="A live record of every agent run, so judges and users can see what happened."
    >
      {loading && traces.length === 0 ? (
        <div className="trace-loading" aria-busy="true">
          <div className="skeleton-line" />
          <div className="skeleton-line short" />
          <div className="skeleton-line" />
        </div>
      ) : traces.length ? (
        <div className="trace-list">
          {traces.map((trace) => {
            const llm = trace.output.llm as
              | { used?: boolean; model?: string; provider?: string }
              | undefined;
            return (
              <div className="trace-item" key={trace.id}>
                <div className="trace-top">
                  <span className="trace-agent">{trace.agent}</span>
                  <span className="trace-time">{formatDuration(trace.latency_ms)}</span>
                </div>
                <p className="trace-detail">
                  {trace.action} · {summarizeOutput(trace.output)}
                </p>
                {llm ? (
                  <span className={`trace-llm ${llm.used ? 'used' : ''}`}>
                    {llm.used
                      ? `${llm.provider}/${llm.model}`
                      : 'deterministic fallback'}
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty">
          <strong>No agent runs yet</strong>
          Upload a resume to start the trace.
        </div>
      )}
    </Panel>
  );
}
