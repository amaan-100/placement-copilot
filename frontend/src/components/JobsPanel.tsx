import type { Job } from '../api/types';
import { sourceLabel } from '../utils';
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
      title="Jobs"
      description="Ranked openings from the live jobs API, with mock listings as a guaranteed fallback."
    >
      <form
        className="search-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch();
        }}
      >
        <input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="e.g. cybersecurity internship"
          aria-label="Job search query"
        />
        <button type="submit" disabled={searching || !hasResume}>
          {searching ? 'Searching…' : 'Find openings'}
        </button>
      </form>

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
              <div>
                <h3 className="job-title">{job.title}</h3>
                <p className="job-sub">
                  {job.company} · {job.location}
                </p>
                <div className="job-skills">
                  {job.skills.slice(0, 6).map((skill) => (
                    <span className="chip" key={`${job.id}-${skill}`}>
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              <div className="job-side">
                <span className={scoreClass(job.match_score)}>{job.match_score}% match</span>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => onDraft(job)}
                  disabled={draftingJobId !== null}
                >
                  {draftingJobId === job.id ? 'Drafting…' : 'Draft application'}
                </button>
                {job.url ? (
                  <a
                    className="job-link"
                    href={job.url}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    Open listing
                  </a>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty">
          <strong>No roles yet</strong>
          Search for a role to see ranked openings and draft an application.
        </div>
      )}
    </Panel>
  );
}
