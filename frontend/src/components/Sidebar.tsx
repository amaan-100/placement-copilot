import type { Application, Job, LlmStatus, ResumeInfo } from '../api/types';
import { Icon } from './Icon';

type SidebarProps = {
  resume: ResumeInfo | null;
  jobs: Job[];
  applications: Application[];
  interviews: number;
  apiOnline: boolean | null;
  llmStatus: LlmStatus | null;
};

type StepState = 'done' | 'current' | 'upcoming';

type RouteStep = {
  id: string;
  label: string;
  detail: string;
  state: StepState;
  count?: number;
};

function llmLabel(llmStatus: LlmStatus | null): string {
  if (llmStatus === null) {
    return 'Checking AI';
  }
  if (llmStatus.available) {
    return 'AI drafting ready';
  }
  if (!llmStatus.enabled) {
    return 'Fallback drafting';
  }
  return 'AI drafting unavailable';
}

function llmDot(llmStatus: LlmStatus | null): string {
  if (llmStatus === null) {
    return '';
  }
  if (llmStatus.available) {
    return 'online';
  }
  return llmStatus.enabled ? 'offline' : 'standby';
}

export function Sidebar({
  resume,
  jobs,
  applications,
  interviews,
  apiOnline,
  llmStatus,
}: SidebarProps) {
  const hasResume = Boolean(resume);
  const hasMatches = jobs.length > 0 || applications.length > 0;
  const hasApproved = applications.some((application) => application.status === 'APPROVED');
  const hasInterview = interviews > 0;
  const pending = applications.filter(
    (application) => application.status === 'PENDING_APPROVAL',
  ).length;

  const activeIndex = !hasResume ? 0 : !hasMatches ? 1 : pending > 0 || !hasApproved ? 2 : 3;

  const steps: RouteStep[] = [
    {
      id: 'profile',
      label: 'Profile',
      detail: hasResume ? 'Resume grounded' : 'Add your resume',
      state: hasResume ? 'done' : activeIndex === 0 ? 'current' : 'upcoming',
    },
    {
      id: 'roles',
      label: 'Matches',
      detail: hasMatches ? 'Roles ranked' : 'Rank live roles',
      state: hasMatches ? 'done' : activeIndex === 1 ? 'current' : 'upcoming',
      count: jobs.length || undefined,
    },
    {
      id: 'approvals',
      label: 'Approvals',
      detail: pending > 0 ? 'Drafts waiting' : hasApproved ? 'Decision logged' : 'Review every draft',
      state: pending > 0 ? 'current' : hasApproved ? 'done' : activeIndex === 2 ? 'current' : 'upcoming',
      count: pending || undefined,
    },
    {
      id: 'practice',
      label: 'Practice',
      detail: hasInterview ? 'Answer scored' : 'Rehearse the answer',
      state: hasInterview ? 'done' : activeIndex === 3 ? 'current' : 'upcoming',
    },
  ];

  const apiLabel =
    apiOnline === null ? 'Connecting' : apiOnline ? 'API connected' : 'API offline';
  const apiDot = apiOnline === null ? '' : apiOnline ? 'online' : 'offline';

  return (
    <aside className="sidebar">
      <a className="brand" href="#top" aria-label="Placement Co-pilot home">
        <span className="brand-mark" aria-hidden="true">
          <Icon name="route" size={22} />
        </span>
        <span>
          <span className="brand-name">Placement Co-pilot</span>
          <span className="brand-tag">Career operations</span>
        </span>
      </a>

      <nav className="route-nav" aria-label="Placement route">
        <div className="route-label">
          <span>Your route</span>
          <span>04 gates</span>
        </div>
        <ol className="route-list">
          {steps.map((step, index) => (
            <li key={step.id}>
              <a
                className={`route-step ${step.state}`}
                href={`#${step.id}`}
                aria-current={step.state === 'current' ? 'step' : undefined}
              >
                <span className="route-index" aria-hidden="true">
                  {step.state === 'done' ? (
                    <Icon name="check" size={13} strokeWidth={2.2} />
                  ) : (
                    String(index + 1).padStart(2, '0')
                  )}
                </span>
                <span className="route-copy">
                  <strong>{step.label}</strong>
                  <span>{step.detail}</span>
                </span>
                {step.count ? (
                  <span className="route-count" aria-label={`${step.count} items`}>
                    {step.count}
                  </span>
                ) : (
                  <Icon className="route-chevron" name="chevron" size={14} />
                )}
              </a>
            </li>
          ))}
        </ol>
      </nav>

      <div className="sidebar-foot">
        <div className="mini-status" aria-live="polite">
          <span className={`status-dot ${apiDot}`} aria-hidden="true" />
          {apiLabel}
        </div>
        <div className="mini-status">
          <span className={`status-dot ${llmDot(llmStatus)}`} aria-hidden="true" />
          <span className="mini-model">{llmLabel(llmStatus)}</span>
        </div>
        <div className="approval-lock">
          <Icon name="lock" size={18} />
          <div>
            <strong>Approval gate on</strong>
            <span>Nothing sends without you.</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
