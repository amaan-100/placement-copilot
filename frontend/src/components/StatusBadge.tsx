import { statusLabel } from '../utils';

export function StatusBadge({ status }: { status: string }) {
  const tone = status === 'APPROVED' ? 'success' : status === 'PENDING_APPROVAL' ? 'warning' : 'neutral';
  return <span className={`badge badge-${tone}`}>{statusLabel(status)}</span>;
}
