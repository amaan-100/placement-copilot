import type { ChangeEvent } from 'react';
import type { ResumeInfo } from '../api/types';
import { formatDate } from '../utils';
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
      title="Resume"
      description="Upload a PDF. The Resume Agent extracts skills and keeps the text scoped to your session."
      action={
        resume ? (
          <button type="button" className="button-danger" onClick={onDelete} disabled={deleting}>
            {deleting ? 'Removing…' : 'Remove'}
          </button>
        ) : undefined
      }
    >
      <label className="file-drop">
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          disabled={uploading}
        />
        <strong>
          {uploading
            ? 'Analyzing your resume…'
            : resume
              ? 'Replace resume PDF'
              : 'Choose a resume PDF'}
        </strong>
        <span>PDF up to 8 MB. Text is parsed locally and never sent to a third party.</span>
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
          </div>
          {resume.facts.summary ? (
            <p className="resume-summary-text">{resume.facts.summary}</p>
          ) : null}
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
          <strong>No resume yet</strong>
          Upload a PDF to unlock job search and application drafting.
        </div>
      )}
    </Panel>
  );
}
