import type { ChangeEvent } from 'react';
import type { ResumeInfo } from '../api/types';
import { formatDate } from '../utils';
import { Icon } from './Icon';
import { Panel } from './Panel';

type ResumePanelProps = {
  resume: ResumeInfo | null;
  uploading: boolean;
  deleting: boolean;
  onUpload: (file: File) => void;
  onDelete: () => void;
};

export function ResumePanel({
  resume,
  uploading,
  deleting,
  onUpload,
  onDelete,
}: ResumePanelProps) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
    }
    event.target.value = '';
  };

  return (
    <Panel
      id="profile"
      step="01"
      title="Resume profile"
      description="This is the source of truth. Upload a text-based PDF and the Resume Agent extracts a grounded profile for every later step."
      action={
        resume ? (
          <button type="button" className="button-danger" onClick={onDelete} disabled={deleting}>
            {deleting ? 'Removing…' : 'Remove'}
          </button>
        ) : undefined
      }
    >
      <label className={`file-drop ${resume ? 'has-file' : ''}`}>
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          disabled={uploading}
        />
        <span className="drop-icon" aria-hidden="true">
          <Icon name={resume ? 'file' : 'route'} size={22} />
        </span>
        <span className="drop-copy">
          <strong>
            {uploading
              ? 'Reading your resume…'
              : resume
                ? 'Replace resume PDF'
                : 'Choose a resume PDF'}
          </strong>
          <span>PDF up to 8 MB. Parsed locally and scoped to this session.</span>
        </span>
        <span className="drop-action">{uploading ? 'Analyzing' : 'Browse'}</span>
      </label>

      {resume ? (
        <div className="resume-summary">
          <div className="resume-meta">
            <div className="resume-file">
              <span className="file-badge" aria-hidden="true">
                PDF
              </span>
              <div>
                <strong>{resume.filename}</strong>
                <span className="status-line">Uploaded {formatDate(resume.created_at)}</span>
              </div>
            </div>
            <span className="grounded-tag">
              <Icon name="shield" size={13} />
              Grounded
            </span>
          </div>
          {resume.facts.summary ? (
            <p className="resume-summary-text">{resume.facts.summary}</p>
          ) : null}
          <div className="resume-skill-head">
            <strong>Detected skills</strong>
            <span>{resume.facts.skills.length} signals</span>
          </div>
          <div className="chips" aria-label="Detected skills">
            {resume.facts.skills.length ? (
              resume.facts.skills.map((skill) => (
                <span className="chip" key={skill}>
                  {skill}
                </span>
              ))
            ) : (
              <span className="chip">No known skills detected</span>
            )}
          </div>
        </div>
      ) : (
        <div className="empty">
          <strong>What happens next</strong>
          The PDF is parsed locally, known skills are grounded against the text, and job search
          unlocks. No resume text leaves this machine.
        </div>
      )}
    </Panel>
  );
}
