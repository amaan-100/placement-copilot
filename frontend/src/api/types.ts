export type SkillFacts = {
  skills: string[];
  summary?: string;
};

export type ResumeUpload = {
  resume_id: number;
  filename: string;
  facts: SkillFacts;
  created_at: string;
};

export type ResumeInfo = {
  id: number;
  filename: string;
  facts: SkillFacts;
  created_at: string;
};

export type Job = {
  id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  skills: string[];
  deadline: string | null;
  match_score: number;
  source: string;
};

export type JobSearchResponse = {
  source: string;
  cached: boolean;
  jobs: Job[];
};

export type ApplicationStatus = 'PENDING_APPROVAL' | 'APPROVED' | string;

export type Application = {
  id: number;
  job_id: number | null;
  company: string;
  title: string;
  url: string;
  deadline: string | null;
  status: ApplicationStatus;
  resume_draft: string;
  cover_note: string;
  created_at: string;
  updated_at: string;
};

export type ApplicationList = {
  applications: Application[];
};

export type DraftResponse = {
  application_id: number;
  status: ApplicationStatus;
  resume_draft: string;
  cover_note: string;
};

export type ApproveResponse = {
  application_id: number;
  status: ApplicationStatus;
  message: string;
};

export type InterviewStart = {
  interview_id: number;
  question: string;
  status: string;
};

export type InterviewEvaluation = {
  interview_id: number;
  score: number;
  feedback: string;
  status: string;
};

export type Dashboard = {
  applications: number;
  pending_approvals: number;
  approved: number;
  interviews: number;
};

export type Trace = {
  id: number;
  agent: string;
  action: string;
  status: string;
  latency_ms: number;
  output: Record<string, unknown>;
  created_at: string;
};

export type SessionInfo = {
  session_id: string;
  created_at: string;
};

export type Health = {
  status: string;
  agent: string;
  approval_gate: boolean;
};

export type LlmStatus = {
  enabled: boolean;
  provider: string;
  model: string;
  base_url: string;
  reachable: boolean;
  model_available: boolean;
  models: string[];
};

export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  request_id?: string;
  detail?: string;
};
