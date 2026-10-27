import type { Application } from '../api/types';
import { formatDate } from '../utils';
import { Panel } from './Panel';
import { StatusBadge } from './StatusBadge';

type ApplicationsPanelProps = {
  applications: Application[];
  onReview: (application: Application) => void;
};

export function ApplicationsPanel({ applications, onReview }: ApplicationsPanelProps) {
  return (
    <Panel
      title="Approval queue"
      description="Every draft waits here. Nothing is submitted until you explicitly approve it."
    >
      {applications.length ? (
        <div className="application-list">
          {applications.map((application) => (
            <article className="application-card" key={application.id}>
              <div className="application-main">
                <h3>{application.title}</h3>
                <p>
                  {application.company} · Drafted {formatDate(application.created_at)}
                </p>
                <p className="status-line">
                  {application.deadline
                    ? `Deadline ${application.deadline}`
                    : 'Deadline not supplied'}
                </p>
              </div>
              <div className="application-actions">
                <StatusBadge status={application.status} />
                {application.status === 'PENDING_APPROVAL' ? (
                  <button type="button" onClick={() => onReview(application)}>
                    Review and approve
                  </button>
                ) : application.status === 'APPROVED' ? (
                  <span className="status-line">Submission stays manual.</span>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty">
          <strong>No drafts yet</strong>
          Search for a job and draft an application. It will land here for approval.
        </div>
      )}
    </Panel>
  );
}
