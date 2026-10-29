import { Icon } from './Icon';

type HeaderProps = {
  apiOnline: boolean | null;
  waking: boolean;
};

export function Header({ apiOnline, waking }: HeaderProps) {
  const statusLabel = waking
    ? 'Waking server'
    : apiOnline === null
      ? 'Connecting'
      : apiOnline
        ? 'API connected'
        : 'API offline';
  const statusClass = waking
    ? 'standby'
    : apiOnline === null
      ? ''
      : apiOnline
        ? 'online'
        : 'offline';

  return (
    <header className="topbar">
      <div className="topbar-title">
        <span>Workspace</span>
        <Icon name="chevron" size={13} />
        <strong>Placement desk</strong>
      </div>
      <div className="topbar-actions">
        <span className="status-pill" aria-live="polite">
          <span className={`status-dot ${statusClass}`} aria-hidden="true" />
          {statusLabel}
        </span>
        <span className="status-pill quiet">
          <Icon name="lock" size={14} />
          Session private
        </span>
      </div>
    </header>
  );
}
