import type { Stat } from '../data/mockData';

export default function StatCard({ stat }: { stat: Stat }) {
  const positive = stat.delta >= 0;
  return (
    <article className="stat-card">
      <div className="stat-label">{stat.label}</div>
      <div className="stat-value">{stat.value}</div>
      <div className={`stat-delta ${positive ? 'up' : 'down'}`}>
        <span className="stat-arrow" aria-hidden>
          {positive ? '▲' : '▼'}
        </span>
        <span>{Math.abs(stat.delta).toFixed(1)}%</span>
        <span className="stat-hint">{stat.hint}</span>
      </div>
    </article>
  );
}
