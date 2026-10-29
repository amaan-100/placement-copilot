import { useEffect, useRef, useState } from 'react';
import type { MouseEvent } from 'react';
import type { Application } from '../api/types';
import { Icon } from './Icon';
import { StatusBadge } from './StatusBadge';

const RESUME_LIMIT = 20_000;
const COVER_LIMIT = 8_000;

type DraftValues = {
  resume_draft: string;
  cover_note: string;
};

type ApprovalModalProps = {
  application: Application | null;
  saving: boolean;
  approving: boolean;
  onSave: (draft: DraftValues) => Promise<Application | null>;
  onConfirm: (draft: DraftValues) => Promise<boolean>;
  onClose: () => void;
};

export function ApprovalModal({
  application,
  saving,
  approving,
  onSave,
  onConfirm,
  onClose,
}: ApprovalModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [coverNote, setCoverNote] = useState('');
  const [resumeDraft, setResumeDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) {
      dialog.showModal();
    }
  }, [application?.id]);

  useEffect(() => {
    if (!application) {
      return;
    }
    setCoverNote(application.cover_note);
    setResumeDraft(application.resume_draft);
    setError(null);
  }, [application?.id]);

  if (!application) {
    return null;
  }

  const isApproved = application.status === 'APPROVED';
  const isBusy = saving || approving;
  const dirty =
    coverNote !== application.cover_note || resumeDraft !== application.resume_draft;

  const draftValues = (): DraftValues | null => {
    const cleanCover = coverNote.trim();
    const cleanResume = resumeDraft.trim();
    if (!cleanCover || !cleanResume) {
      setError('Both the cover note and resume draft need text before saving.');
      return null;
    }
    return { cover_note: cleanCover, resume_draft: cleanResume };
  };

  const handleBackdropClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === dialogRef.current) {
      onClose();
    }
  };

  const handleSave = async () => {
    const values = draftValues();
    if (!values) {
      return;
    }
    setError(null);
    const updated = await onSave(values);
    if (!updated) {
      setError('The draft could not be saved. Check the connection and try again.');
      return;
    }
    setCoverNote(updated.cover_note);
    setResumeDraft(updated.resume_draft);
  };

  const handleConfirm = async () => {
    const values = draftValues();
    if (!values) {
      return;
    }
    setError(null);
    const confirmed = await onConfirm(values);
    if (!confirmed) {
      setError('The draft could not be approved. Check the connection and try again.');
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="approval-dialog"
      aria-labelledby="approval-title"
      aria-describedby="approval-description"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={handleBackdropClick}
    >
      <div className="approval-shell">
        <div className="approval-head">
          <span className="approval-mark" aria-hidden="true">
            <Icon name="shield" size={20} />
          </span>
          <div>
            <h2 id="approval-title">Review and edit draft</h2>
            <p id="approval-description">
              Edit anything that needs your voice. Approving records your decision, but does
              not submit anything to the employer.
            </p>
          </div>
        </div>

        <div className="approval-body">
          <div className="approval-grid">
            <div className="meta-block">
              <span>Role</span>
              <strong>{application.title}</strong>
            </div>
            <div className="meta-block">
              <span>Company</span>
              <strong>{application.company}</strong>
            </div>
            <div className="meta-block">
              <span>Status</span>
              <StatusBadge status={application.status} />
            </div>
          </div>

          {isApproved ? (
            <p className="approval-warning">
              This draft is approved. Saving changes will reset it to pending approval, and
              you will need to approve the edited text again.
            </p>
          ) : null}

          <div className="draft-block">
            <label className="draft-label" htmlFor="approval-cover-note">
              Cover note
            </label>
            <textarea
              id="approval-cover-note"
              className="draft-editor"
              value={coverNote}
              maxLength={COVER_LIMIT}
              rows={7}
              spellCheck
              onChange={(event) => setCoverNote(event.target.value)}
              disabled={isBusy}
            />
            <span className="draft-count">
              {coverNote.length.toLocaleString()} / {COVER_LIMIT.toLocaleString()}
            </span>
          </div>

          <div className="draft-block">
            <label className="draft-label" htmlFor="approval-resume-draft">
              Resume draft
            </label>
            <textarea
              id="approval-resume-draft"
              className="draft-editor"
              value={resumeDraft}
              maxLength={RESUME_LIMIT}
              rows={10}
              spellCheck
              onChange={(event) => setResumeDraft(event.target.value)}
              disabled={isBusy}
            />
            <span className="draft-count">
              {resumeDraft.length.toLocaleString()} / {RESUME_LIMIT.toLocaleString()}
            </span>
          </div>

          {error ? (
            <p className="form-error" role="alert">
              {error}
            </p>
          ) : null}
        </div>

        <div className="approval-foot">
          <p className="approval-note">
            {isApproved
              ? 'Editing approved text reopens it for approval. No automatic submission.'
              : 'No automatic submission. You stay in control.'}
          </p>
          <div className="approval-actions">
            <button
              type="button"
              className="button-secondary"
              onClick={onClose}
              disabled={isBusy}
            >
              Cancel
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={handleSave}
              disabled={isBusy || !dirty}
            >
              {saving ? 'Saving…' : 'Save changes'}
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              disabled={isBusy || (isApproved && !dirty)}
            >
              {approving
                ? 'Approving…'
                : isApproved && !dirty
                  ? 'Approved'
                  : isApproved
                    ? 'Save & re-approve'
                    : dirty
                      ? 'Save & approve'
                      : 'Approve draft'}
            </button>
          </div>
        </div>
      </div>
    </dialog>
  );
}
