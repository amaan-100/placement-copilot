type StatCardProps = {
  label: string;
  value: number;
  tone?: 'warning' | 'success';
};

export function StatCard({ label, value, tone }: StatCardProps) {
  return (
    <div className={['stat', tone].filter(Boolean).join(' ')}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
