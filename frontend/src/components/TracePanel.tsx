import type { Trace } from '../api/types';
import { formatDuration, summarizeOutput } from '../utils';
import { Icon } from './Icon';
import type { IconName } from './Icon';
import { Panel } from './Panel';

type TracePanelProps = {
  traces: Trace[];
  loading: boolean;
};

function agentIcon(agent: string): IconName {
  const name = agent.toLowerCase();
  if (name.includes('resume')) {
    return 'file';
  }
  if (name.includes('job')) {
    return 'briefcase';
  }
  if (name.includes('document')) {
    return 'spark';
  }
  if (name.includes('interview')) {
    return 'mic';
  }
  return 'activity';
}

export function TracePanel({ traces, loading }: TracePanelProps) {
  return (
    <Panel
      id="activity"
      title="Agent activity"
      description="Every run and fallback, newest first."
      action={
        <span className="live-tag">
          <span className="status-dot online" aria-hidden="true" />
          Live
        </span>
      }
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
            const llm = trace.output.llm as { used?: boolean } | undefined;
            return (
              <div className="trace-item" key={trace.id}>
                <span className="trace-icon" aria-hidden="true">
                  <Icon name={agentIcon(trace.agent)} size={14} />
                </span>
                <div className="trace-body">
                  <div className="trace-top">
                    <span className="trace-agent">{trace.agent}</span>
                    <span className="trace-time">{formatDuration(trace.latency_ms)}</span>
                  </div>
                  <p className="trace-detail">
                    {trace.action} · {summarizeOutput(trace.output)}
                  </p>
                  {llm ? (
                    <span className={`trace-llm ${llm.used ? 'used' : ''}`}>
                      {llm.used ? 'AI-assisted' : 'Template fallback'}
                    </span>
                  ) : null}
                </div>
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
