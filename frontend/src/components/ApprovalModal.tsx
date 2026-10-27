import { useEffect, useRef } from 'react';
import type { MouseEvent } from 'react';
import type { Application } from '../api/types';
import { StatusBadge } from './StatusBadge';

type ApprovalModalProps = {
  application: Application | null;
  approving: boolean;
  onConfirm: () => void;
  onClose: () => void;
};

export function ApprovalModal({
  application,
  approving,
  onConfirm,
  onClose,
}: ApprovalModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) {
      dialog.showModal();
    }
  }, [application?.id]);

  if (!application) {
    return null;
  }

  const handleBackdropClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === dialogRef.current) {
      onClose();
    }
  };

  return (
    <dialog
      ref={dialogRef}
      className="approval-dialog"
      aria-labelledby="approval-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={handleBackdropClick}
    >
      <div className="approval-shell">
        <div className="approval-head">
          <h2 id="approval-title">Approve application</h2>
          <p>Review the draft, then approve. Nothing is sent to the employer automatically.</p>
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

          <div className="draft-block">
            <h3>Cover note</h3>
            <pre>{application.cover_note}</pre>
          </div>
          <div className="draft-block">
            <h3>Resume draft</h3>
            <pre>{application.resume_draft}</pre>
          </div>
        </div>

        <div className="approval-foot">
          <button type="button" className="button-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="button" onClick={onConfirm} disabled={approving}>
            {approving ? 'Approving…' : 'Approve application'}
          </button>
        </div>
      </div>
    </dialog>
  );
}
