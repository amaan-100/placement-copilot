type HeaderProps = {
  apiOnline: boolean | null;
};

export function Header({ apiOnline }: HeaderProps) {
  const statusLabel =
    apiOnline === null ? 'Connecting to API' : apiOnline ? 'API connected' : 'API offline';
  const statusClass = apiOnline === null ? '' : apiOnline ? 'online' : 'offline';

  return (
    <header className="header">
      <div className="header-inner">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            PC
          </span>
          <div>
            <span className="brand-name">Placement Co-pilot</span>
            <span className="brand-tag">Multi-agent placement assistant</span>
          </div>
        </div>
        <div className="header-meta" aria-live="polite">
          <span className={`status-dot ${statusClass}`} aria-hidden="true" />
          {statusLabel}
        </div>
      </div>
    </header>
  );
}
