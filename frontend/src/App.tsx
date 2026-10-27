import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from './api/client';
import type {
  Application,
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
import { InterviewPanel } from './components/InterviewPanel';
import { JobsPanel } from './components/JobsPanel';
import { Panel } from './components/Panel';
import { ResumePanel } from './components/ResumePanel';
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
};

const INITIAL_LOADING: LoadingState = {
  upload: false,
  deleteResume: false,
  search: false,
  interviewStart: false,
  interviewEvaluate: false,
  approve: false,
};

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Try again.';
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

  const handleApprove = async () => {
    if (!approvalTarget) {
      return;
    }
    setLoading((current) => ({ ...current, approve: true }));
    try {
      const result = await api.approveApplication(approvalTarget.id);
      notify('success', result.message);
      setApprovalTarget(null);
      await Promise.all([refreshApplications(), refreshDashboard(), refreshTraces()]);
    } catch (error) {
      handleLoadError(error);
      notify('error', errorText(error));
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

  return (
    <div className="app">
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <Header apiOnline={apiOnline} />

      <main id="main-content">
        <section className="hero">
          <div>
            <h1>Your placement co-pilot.</h1>
            <p>
              Finds roles, drafts applications, and coaches interviews. You approve every
              submission.
            </p>
          </div>
          <div className="hero-note">
            <span className="status-dot online" aria-hidden="true" />
            Approval gate active
          </div>
        </section>

        <section className="stats" aria-label="Placement summary">
          <StatCard label="Applications" value={dashboard.applications} />
          <StatCard
            label="Pending approval"
            value={dashboard.pending_approvals}
            tone="warning"
          />
          <StatCard label="Approved" value={dashboard.approved} tone="success" />
          <StatCard label="Interviews" value={dashboard.interviews} />
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
              onAnswerChange={setAnswer}
              onStart={handleStartInterview}
              onEvaluate={handleEvaluate}
            />
          </div>

          <aside className="workspace-side">
            <TracePanel traces={traces} loading={tracesLoading} />
            <Panel
              title="Local AI"
              description="Ollama runs on this machine, with deterministic fallback."
            >
              <div className="llm-status">
                <span
                  className={`status-dot ${llmStatus?.model_available ? 'online' : 'offline'}`}
                  aria-hidden="true"
                />
                <div>
                  <strong>
                    {llmStatus === null
                      ? 'Checking Ollama…'
                      : llmStatus.model_available
                        ? llmStatus.model
                        : 'Fallback mode'}
                  </strong>
                  <span>
                    {llmStatus && !llmStatus.enabled
                      ? 'Local generation is disabled in backend settings.'
                      : llmStatus?.model_available
                        ? 'Local generation is enabled for drafts and interviews.'
                        : llmStatus?.reachable
                          ? `Ollama is running; pull ${llmStatus.model} to enable local generation.`
                          : 'Ollama is offline; deterministic agents stay available.'}
                  </span>
                </div>
              </div>
            </Panel>
            <Panel title="Safety" description="Applications stay in your control.">
              <ul className="safety-list">
                <li>Drafts use facts already present in your resume.</li>
                <li>Nothing is submitted without your explicit approval.</li>
                <li>Every agent action is recorded in the trace.</li>
                <li>Your workspace is anonymous and isolated by session.</li>
              </ul>
            </Panel>
          </aside>
        </div>
      </main>

      <ApprovalModal
        application={approvalTarget}
        approving={loading.approve}
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
