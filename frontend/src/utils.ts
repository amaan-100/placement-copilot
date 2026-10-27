export function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'recently';
  }
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(date);
}

export function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }
  return `${(ms / 1000).toFixed(1)} s`;
}

export function summarizeOutput(output: Record<string, unknown>): string {
  const entries = Object.entries(output)
    .filter(([, value]) => value !== null && typeof value !== 'object')
    .slice(0, 3);
  if (entries.length === 0) {
    return 'Run recorded';
  }
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join(' · ');
}

export function sourceLabel(source: string): string {
  if (source === 'live_api') {
    return 'Live jobs API';
  }
  if (source === 'mock_fallback') {
    return 'Mock fallback';
  }
  return source.replaceAll('_', ' ');
}

export function statusLabel(status: string): string {
  if (status === 'PENDING_APPROVAL') {
    return 'Pending approval';
  }
  if (status === 'APPROVED') {
    return 'Approved';
  }
  return status.toLowerCase().replaceAll('_', ' ');
}
