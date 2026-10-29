import type { Job } from '../api/types';
import { sourceLabel } from '../utils';
import { Icon } from './Icon';
import { Panel } from './Panel';

type JobsPanelProps = {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: () => void;
  searching: boolean;
  jobs: Job[];
  source: string;
  cached: boolean;
  draftingJobId: number | null;
  onDraft: (job: Job) => void;
  hasResume: boolean;
};

const SUGGESTIONS = [
  'Cybersecurity internship',
  'Python developer',
  'Data analyst',
  'Product intern',
];

function scoreClass(score: number): string {
  if (score >= 70) {
    return 'score high';
  }
  if (score >= 40) {
    return 'score';
  }
  return 'score low';
}

export function JobsPanel({
  query,
  onQueryChange,
  onSearch,
  searching,
  jobs,
  source,
  cached,
  draftingJobId,
  onDraft,
  hasResume,
}: JobsPanelProps) {
  return (
    <Panel
      id="roles"
      step="02"
      title="Matched roles"
      description="Ranked openings from the live jobs feed, with mock roles as a guaranteed fallback."
      action={jobs.length ? <span className="panel-count">{jobs.length} matched</span> : undefined}
    >
      <form
        className="search-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch();
        }}
      >
        <div className="search-field">
          <Icon name="search" size={16} />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="e.g. cybersecurity internship"
            aria-label="Job search query"
          />
        </div>
        <button type="submit" disabled={searching || !hasResume}>
          {searching ? 'Searching…' : 'Find openings'}
        </button>
      </form>

      <div className="quick-searches" aria-label="Suggested searches">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="quick-chip"
            onClick={() => onQueryChange(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>

      {!hasResume ? (
        <p className="inline-hint">Upload a resume first so the Job Agent can rank openings.</p>
      ) : null}

      {source ? (
        <p className="source-line">
          Source: <strong>{sourceLabel(source)}</strong>
          {cached ? ' · cached result' : ''}
        </p>
      ) : null}

      {searching ? (
        <div className="job-list" aria-busy="true" aria-label="Loading jobs">
          <div className="skeleton-row" />
          <div className="skeleton-row" />
          <div className="skeleton-row" />
        </div>
      ) : jobs.length ? (
        <div className="job-list">
          {jobs.map((job) => (
            <article className="job-card" key={job.id}>
              <div className="job-main">
                <h3 className="job-title">{job.title}</h3>
                <p className="job-company">{job.company}</p>
                <p className="job-sub">{job.location}</p>
                <div className="job-skills">
                  {job.skills.slice(0, 6).map((skill) => (
                    <span className="chip" key={`${job.id}-${skill}`}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div className="job-side">
                <div className="job-match">
                  <span className={scoreClass(job.match_score)}>
                    <strong>{job.match_score}</strong>
                    <small>%</small>
                  </span>
                  <span className="job-match-label">match</span>
                </div>
                <button
                  type="button"
                  className="button-secondary button-small"
                  onClick={() => onDraft(job)}
                  disabled={draftingJobId !== null}
                >
                  <Icon name="spark" size={14} />
                  {draftingJobId === job.id ? 'Drafting…' : 'Draft application'}
                </button>
                {job.url ? (
                  <a
                    className="job-link"
                    href={job.url}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    View role
                    <Icon name="arrow" size={12} />
                  </a>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty">
          <strong>{hasResume ? 'No roles yet' : 'Resume needed'}</strong>
          {hasResume
            ? 'Search for a target role to see ranked openings and draft an application.'
            : 'Add your resume above, then search for the kind of role you want.'}
        </div>
      )}
    </Panel>
  );
}
