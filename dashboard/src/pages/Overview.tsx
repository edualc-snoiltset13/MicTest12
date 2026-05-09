import StatCard from '../components/StatCard';
import RevenueChart from '../components/RevenueChart';
import ActivityChart from '../components/ActivityChart';
import Card from '../components/Card';
import { activityFeed, orders, stats } from '../data/mockData';

export default function Overview() {
  const recentOrders = orders.slice(0, 5);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Overview</h1>
          <p className="page-subtitle">Welcome back, Eva. Here's what's happening today.</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost">Export</button>
          <button className="btn btn-primary">+ New report</button>
        </div>
      </div>

      <div className="stat-grid">
        {stats.map((s) => (
          <StatCard key={s.id} stat={s} />
        ))}
      </div>

      <div className="grid grid-2">
        <Card
          title="Revenue & expenses"
          subtitle="Monthly trend, this year"
          actions={<button className="btn btn-ghost">View report</button>}
        >
          <RevenueChart />
        </Card>
        <Card title="Weekly activity" subtitle="Sessions and signups">
          <ActivityChart />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="Recent orders" actions={<a className="link" href="/orders">All orders →</a>}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Customer</th>
                <th>Status</th>
                <th className="num">Amount</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((o) => (
                <tr key={o.id}>
                  <td className="mono">{o.id}</td>
                  <td>{o.customer}</td>
                  <td>
                    <span className={`badge badge-${o.status}`}>{o.status}</span>
                  </td>
                  <td className="num">${o.amount.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Activity">
          <ul className="activity-feed">
            {activityFeed.map((a) => (
              <li key={a.id} className="activity-item">
                <div className="activity-dot" aria-hidden />
                <div className="activity-text">
                  <strong>{a.who}</strong> {a.action} <em>{a.target}</em>
                  <div className="activity-when">{a.when}</div>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
