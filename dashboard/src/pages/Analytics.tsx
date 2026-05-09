import Card from '../components/Card';
import RevenueChart from '../components/RevenueChart';
import ActivityChart from '../components/ActivityChart';
import ChannelChart from '../components/ChannelChart';
import StatCard from '../components/StatCard';
import { stats, trafficByChannel } from '../data/mockData';

export default function Analytics() {
  const totalSessions = trafficByChannel.reduce((sum, c) => sum + c.value, 0);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p className="page-subtitle">Acquisition, engagement, and revenue trends.</p>
        </div>
        <div className="page-header-actions">
          <select className="select" defaultValue="30">
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      <div className="stat-grid">
        {stats.map((s) => (
          <StatCard key={s.id} stat={s} />
        ))}
      </div>

      <div className="grid grid-3-2">
        <Card title="Revenue & expenses" subtitle="Monthly trend">
          <RevenueChart />
        </Card>
        <Card title="Traffic by channel" subtitle={`${totalSessions.toLocaleString()} sessions`}>
          <ChannelChart />
        </Card>
      </div>

      <div className="grid grid-2">
        <Card title="Weekly activity">
          <ActivityChart />
        </Card>
        <Card title="Top countries">
          <ul className="ranked-list">
            <li>
              <span>United States</span>
              <span className="bar"><span style={{ width: '92%' }} /></span>
              <span className="num">38.4k</span>
            </li>
            <li>
              <span>Germany</span>
              <span className="bar"><span style={{ width: '64%' }} /></span>
              <span className="num">22.1k</span>
            </li>
            <li>
              <span>Japan</span>
              <span className="bar"><span style={{ width: '48%' }} /></span>
              <span className="num">14.6k</span>
            </li>
            <li>
              <span>Brazil</span>
              <span className="bar"><span style={{ width: '36%' }} /></span>
              <span className="num">9.8k</span>
            </li>
            <li>
              <span>India</span>
              <span className="bar"><span style={{ width: '28%' }} /></span>
              <span className="num">7.2k</span>
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
