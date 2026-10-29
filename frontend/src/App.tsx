import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from './api/client';
import type {
  Application,
  ApplicationUpdate,
  Dashboard,
  InterviewEvaluation,
  InterviewStart,
  Job,
  LlmStatus,
  ResumeInfo,
  Trace,
} from './api/types';
import { ApplicationsPanel } from './components/ApplicationsPanel';
import { ApprovalModal } from './components/ApprovalModal';
import { Header } from './components/Header';
import { Icon } from './components/Icon';
import { InterviewPanel } from './components/InterviewPanel';
import { JobsPanel } from './components/JobsPanel';
import { Panel } from './components/Panel';
import { ResumePanel } from './components/ResumePanel';
import { Sidebar } from './components/Sidebar';
import { StatCard } from './components/StatCard';
import { Toast } from './components/Toast';
import type { ToastKind, ToastMessage } from './components/Toast';
import { TracePanel } from './components/TracePanel';

const EMPTY_DASHBOARD: Dashboard = {
  applications: 0,
  pending_approvals: 0,
  approved: 0,
  interviews: 0,
};

type LoadingState = {
  upload: boolean;
  deleteResume: boolean;
  search: boolean;
  interviewStart: boolean;
  interviewEvaluate: boolean;
  approve: boolean;
  saveDraft: boolean;
};

type NextMove = {
  title: string;
  body: string;
  cta: string;
  href: string;
};

const INITIAL_LOADING: LoadingState = {
  upload: false,
  deleteResume: false,
  search: false,
  interviewStart: false,
  interviewEvaluate: false,
  approve: false,
  saveDraft: false,
};

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Try again.';
}

function llmTone(status: LlmStatus | null): string {
  if (status === null) {
    return '';
  }
  if (status.available) {
    return 'online';
  }
  return status.enabled ? 'offline' : 'standby';
}

function llmTitle(status: LlmStatus | null): string {
  if (status === null) {
    return 'Checking AI…';
  }
  if (status.available) {
    return 'AI drafting ready';
  }
  if (!status.enabled) {
    return 'Fallback drafting';
  }
  return 'AI drafting unavailable';
}

function llmDescription(status: LlmStatus | null): string {
  if (status === null) {
    return 'Checking whether AI-assisted drafting is available.';
  }
  if (status.available) {
    return 'AI-assisted drafts are available. Every draft still needs your review.';
  }
  if (!status.enabled) {
    return 'AI generation is off; deterministic drafts keep the workflow moving.';
  }
  return 'AI generation is temporarily unavailable; deterministic drafts stay available.';
}

export default function App() {
  const [dashboard, setDashboard] = useState<Dashboard>(EMPTY_DASHBOARD);
  const [resume, setResume] = useState<ResumeInfo | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobSource, setJobSource] = useState('');
  const [jobsCached, setJobsCached] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [traces, setTraces] = useState<Trace[]>([]);
  const [query, setQuery] = useState('cybersecurity internship');
  const [interview, setInterview] = useState<InterviewStart | null>(null);
  const [answer, setAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<InterviewEvaluation | null>(null);
  const [approvalTarget, setApprovalTarget] = useState<Application | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);
  const [loading, setLoading] = useState<LoadingState>(INITIAL_LOADING);
  const [draftingJobId, setDraftingJobId] = useState<number | null>(null);
  const [tracesLoading, setTracesLoading] = useState(true);
  const [showWakeNotice, setShowWakeNotice] = useState(false);

  const apiBusy =
    Object.values(loading).some(Boolean) ||
    draftingJobId !== null ||
    tracesLoading ||
    apiOnline === null;

  useEffect(() => {
    if (!apiBusy && apiOnline !== null) {
      setShowWakeNotice(false);
      return undefined;
    }
    const timer = window.setTimeout(() => setShowWakeNotice(true), 3_000);
    return () => window.clearTimeout(timer);
  }, [apiBusy, apiOnline]);

  const notify = useCallback((kind: ToastKind, text: string) => {
    setToast({ kind, text });
  }, []);

  useEffect(() => {
    if (!toast) {
      return undefined;
    }
    const timer = window.setTimeout(() => setToast(null), 6000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const handleLoadError = useCallback((error: unknown) => {
    if (error instanceof ApiError && error.status === 0) {
      setApiOnline(false);
    }
  }, []);

  const refreshDashboard = useCallback(async () => {
    try {
      setDashboard(await api.getDashboard());
      setApiOnline(true);
    } catch (error) {
      handleLoadError(error);
    }
  }, [handleLoadError]);

  const refreshApplications = useCallback(async () => {
    try {
      const result = await api.getApplications();
      setApplications(result.applications);
    } catch (error) {
      handleLoadError(error);
    }
  }, [handleLoadError]);

  const refreshTraces = useCallback(async () => {
    setTracesLoading(true);
    try {
      setTraces(await api.getTraces());
    } catch (error) {
      handleLoadError(error);
    } finally {
      setTracesLoading(false);
    }
  }, [handleLoadError]);

  const refreshLatestResume = useCallback(async () => {
    try {
      setResume(await api.getLatestResume());
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setResume(null);
        return;
      }
      handleLoadError(error);
    }
  }, [handleLoadError]);

  useEffect(() => {
    let active = true;
    api
      .getHealth()
      .then(() => {
        if (active) {
          setApiOnline(true);
        }
      })
      .catch(() => {
        if (active) {
          setApiOnline(false);
        }
      });

    void refreshDashboard();
    void refreshApplications();
    void refreshTraces();
    void refreshLatestResume();
    api
      .getLlmStatus()
      .then(setLlmStatus)
      .catch(() => setLlmStatus(null));

    return () => {
      active = false;
    };
  }, [refreshApplications, refreshDashboard, refreshLatestResume, refreshTraces]);

  const handleUpload = async (file: File) => {
    setLoading((current) => ({ ...current, upload: true }));
    try {
      const uploaded = await api.uploadResume(file);
      setResume({
        id: uploaded.resume_id,
        filename: uploaded.filename,
        facts: uploaded.facts,
        created_at: uploaded.created_at,
      });
      setApiOnline(true);
      notify(
        'success',
        `Resume analyzed. ${uploaded.facts.skills.length} skills detected.`,
      );
      await Promise.all([refreshDashboard(), refreshTraces()]);
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setLoading((current) => ({ ...current, upload: false }));
    }
  };

  const handleDeleteResume = async () => {
    setLoading((current) => ({ ...current, deleteResume: true }));
    try {
      const result = await api.deleteResume();
      setResume(null);
      setJobs([]);
      setJobSource('');
      setJobsCached(false);
      notify(
        'success',
        result.deleted ? 'Resume removed from this session.' : 'No resume was stored.',
      );
      await Promise.all([refreshDashboard(), refreshTraces()]);
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setLoading((current) => ({ ...current, deleteResume: false }));
    }
  };

  const handleSearch = async () => {
    if (!resume) {
      notify('error', 'Upload a resume before searching jobs.');
      return;
    }
    setLoading((current) => ({ ...current, search: true }));
    try {
      const result = await api.searchJobs(query.trim());
      setJobs(result.jobs);
      setJobSource(result.source);
      setJobsCached(result.cached);
      setApiOnline(true);
      if (result.jobs.length === 0) {
        notify('info', 'No roles matched that search. Try a broader query.');
      }
      await refreshTraces();
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setLoading((current) => ({ ...current, search: false }));
    }
  };

  const handleDraft = async (job: Job) => {
    setDraftingJobId(job.id);
    try {
      await api.draftApplication(job.id);
      notify('success', `Draft created for ${job.title}. Review it in the approval queue.`);
      await Promise.all([refreshApplications(), refreshDashboard(), refreshTraces()]);
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setDraftingJobId(null);
    }
  };

  const handleSaveDraft = async (
    draft: ApplicationUpdate,
  ): Promise<Application | null> => {
    if (!approvalTarget) {
      return null;
    }
    const wasApproved = approvalTarget.status === 'APPROVED';
    setLoading((current) => ({ ...current, saveDraft: true }));
    try {
      const updated = await api.updateApplication(approvalTarget.id, draft);
      const approvalReset = wasApproved && updated.status === 'PENDING_APPROVAL';
      setApprovalTarget(updated);
      notify(
        'success',
        approvalReset
          ? 'Draft updated. Approval reset; review and approve again.'
          : 'Draft changes saved.',
      );
      await Promise.all([refreshApplications(), refreshDashboard()]);
      return updated;
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
      return null;
    } finally {
      setLoading((current) => ({ ...current, saveDraft: false }));
    }
  };

  const handleApprove = async (draft: ApplicationUpdate): Promise<boolean> => {
    if (!approvalTarget) {
      return false;
    }
    setLoading((current) => ({ ...current, approve: true }));
    try {
      const edited =
        draft.cover_note !== approvalTarget.cover_note ||
        draft.resume_draft !== approvalTarget.resume_draft;
      let current = approvalTarget;
      if (edited) {
        current = await api.updateApplication(approvalTarget.id, draft);
        setApprovalTarget(current);
      }
      const result = await api.approveApplication(current.id);
      notify('success', result.message);
      setApprovalTarget(null);
      await Promise.all([refreshApplications(), refreshDashboard(), refreshTraces()]);
      return true;
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
      return false;
    } finally {
      setLoading((current) => ({ ...current, approve: false }));
    }
  };

  const handleStartInterview = async () => {
    if (!query.trim()) {
      notify('error', 'Enter a role or goal before starting the interview.');
      return;
    }
    setLoading((current) => ({ ...current, interviewStart: true }));
    try {
      const started = await api.startInterview(query.trim());
      setInterview(started);
      setAnswer('');
      setEvaluation(null);
      notify('info', 'Interview question ready.');
      await Promise.all([refreshDashboard(), refreshTraces()]);
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setLoading((current) => ({ ...current, interviewStart: false }));
    }
  };

  const handleEvaluate = async () => {
    if (!interview) {
      return;
    }
    setLoading((current) => ({ ...current, interviewEvaluate: true }));
    try {
      const result = await api.evaluateInterview(interview.interview_id, answer.trim());
      setEvaluation(result);
      notify('success', `Answer scored ${result.score}/100.`);
      await refreshTraces();
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
    } finally {
      setLoading((current) => ({ ...current, interviewEvaluate: false }));
    }
  };

  const pendingApprovals = applications.filter(
    (application) => application.status === 'PENDING_APPROVAL',
  ).length;

  let nextMove: NextMove;
  if (!resume) {
    nextMove = {
      title: 'Add your resume first.',
      body: 'The agents need one source of truth before they can match roles or draft a grounded application.',
      cta: 'Add your resume',
      href: '#profile',
    };
  } else if (!jobs.length && !applications.length) {
    nextMove = {
      title: 'Find your first match.',
      body: 'Your profile is ready. Search a target role and the Job Agent will rank live openings against it.',
      cta: 'Search roles',
      href: '#roles',
    };
  } else if (pendingApprovals) {
    nextMove = {
      title: 'Review your next draft.',
      body: `${pendingApprovals} application${pendingApprovals === 1 ? '' : 's'} waiting for your approval. Check the cover note before it moves forward.`,
      cta: 'Open approval queue',
      href: '#approvals',
    };
  } else if (!applications.length) {
    nextMove = {
      title: 'Draft a tailored application.',
      body: 'Pick a role worth pursuing. The Document Agent will draft a grounded cover note for you to review.',
      cta: 'Browse matches',
      href: '#roles',
    };
  } else if (dashboard.interviews === 0) {
    nextMove = {
      title: 'Practice the interview answer.',
      body: 'You cleared the approval gate. Rehearse one role-specific question and get a rubric score.',
      cta: 'Start practice',
      href: '#practice',
    };
  } else {
    nextMove = {
      title: 'Keep the run moving.',
      body: 'Review recent agent activity or look for another role. Nothing sends without your approval.',
      cta: 'Review activity',
      href: '#activity',
    };
  }

  return (
    <div className="app-shell" id="top">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <Sidebar
        resume={resume}
        jobs={jobs}
        applications={applications}
        interviews={dashboard.interviews}
        apiOnline={apiOnline}
        llmStatus={llmStatus}
      />

      <div className="page">
        <Header apiOnline={apiOnline} waking={showWakeNotice} />

        {showWakeNotice ? (
          <div className="server-wake" role="status" aria-live="polite">
            <span className="wake-spinner" aria-hidden="true" />
            <div>
              <strong>Waking the workspace</strong>
              <span>
                The first request after idle can take up to a minute. Your action is still
                loading.
              </span>
            </div>
          </div>
        ) : null}

        <main id="main-content">
          <section className="hero" aria-labelledby="hero-title">
            <div className="hero-copy">
              <h1 id="hero-title">
                One resume.
                <span>Every next move.</span>
              </h1>
              <p>
                Match roles, tailor applications, and practice interviews with agents that
                show their work — and a gate that keeps you in control.
              </p>
              <div className="hero-actions">
                <a className="button button-primary" href={nextMove.href}>
                  {nextMove.cta}
                  <Icon name="arrow" size={15} />
                </a>
                <a className="button button-ghost" href="#activity">
                  <Icon name="activity" size={15} />
                  Agent activity
                </a>
              </div>
            </div>

            <aside className="next-card" aria-label="Next best move">
              <Icon className="next-watermark" name="arrow" size={156} strokeWidth={0.8} />
              <div>
                <p className="next-title">{nextMove.title}</p>
                <p className="next-body">{nextMove.body}</p>
              </div>
              <a className="next-link" href={nextMove.href}>
                {nextMove.cta}
                <Icon name="arrow" size={14} />
              </a>
            </aside>
          </section>

          <section className="pipeline" aria-label="Session pipeline">
            <div className="pipeline-label">
              <span>Live pipeline</span>
              <strong>This session</strong>
            </div>
            <div className="stats">
              <StatCard label="Applications" value={dashboard.applications} />
              <StatCard
                label="Pending approval"
                value={dashboard.pending_approvals}
                tone="warning"
              />
              <StatCard label="Approved" value={dashboard.approved} tone="success" />
              <StatCard label="Interviews" value={dashboard.interviews} tone="accent" />
            </div>
          </section>

          <div className="workspace">
            <div className="workspace-main">
              <ResumePanel
                resume={resume}
                uploading={loading.upload}
                deleting={loading.deleteResume}
                onUpload={handleUpload}
                onDelete={handleDeleteResume}
              />
              <JobsPanel
                query={query}
                onQueryChange={setQuery}
                onSearch={handleSearch}
                searching={loading.search}
                jobs={jobs}
                source={jobSource}
                cached={jobsCached}
                draftingJobId={draftingJobId}
                onDraft={handleDraft}
                hasResume={Boolean(resume)}
              />
              <ApplicationsPanel
                applications={applications}
                onReview={setApprovalTarget}
              />
              <InterviewPanel
                goal={query}
                interview={interview}
                answer={answer}
                starting={loading.interviewStart}
                evaluating={loading.interviewEvaluate}
                evaluation={evaluation}
                pastInterviews={dashboard.interviews}
                onAnswerChange={setAnswer}
                onStart={handleStartInterview}
                onEvaluate={handleEvaluate}
              />
            </div>

            <aside className="workspace-side" aria-label="Workspace signals">
              <TracePanel traces={traces} loading={tracesLoading} />

              <Panel
                title="AI assistance"
                description="AI can speed up drafting, with a deterministic path when it is unavailable."
              >
                <div className="llm-status">
                  <span className="ai-icon" aria-hidden="true">
                    <Icon name="spark" size={18} />
                  </span>
                  <div>
                    <strong>
                      <span className={`status-dot ${llmTone(llmStatus)}`} aria-hidden="true" />
                      {llmTitle(llmStatus)}
                    </strong>
                    <span>{llmDescription(llmStatus)}</span>
                  </div>
                </div>
                <div className="ai-meta">
                  <div>
                    <span>Drafting</span>
                    <strong>{llmStatus?.available ? 'AI-assisted' : 'Template fallback'}</strong>
                  </div>
                  <div>
                    <span>Review</span>
                    <strong>Always required</strong>
                  </div>
                </div>
              </Panel>

              <Panel title="Guardrails" description="The parts that stay in your hands.">
                <ul className="safety-list">
                  <li>Unsupported claims are rejected before a draft reaches you.</li>
                  <li>Nothing is submitted without your explicit approval.</li>
                  <li>Every agent action is recorded in the trace.</li>
                  <li>AI features are optional and never bypass your approval gate.</li>
                  <li>Your workspace is anonymous and isolated by session.</li>
                </ul>
              </Panel>
            </aside>
          </div>

          <footer className="footer">
            <span>Placement Co-pilot</span>
            <span>AI-assisted · Session-scoped · Human-approved</span>
          </footer>
        </main>
      </div>

      <ApprovalModal
        application={approvalTarget}
        saving={loading.saveDraft}
        approving={loading.approve}
        onSave={handleSaveDraft}
        onConfirm={handleApprove}
        onClose={() => setApprovalTarget(null)}
      />

      {toast ? (
        <Toast
          message={toast}
          onDismiss={() => {
            setToast(null);
          }}
        />
      ) : null}
    </div>
  );
}
