import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { weeklyActivity } from '../data/mockData';

export default function ActivityChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={weeklyActivity} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="day" stroke="var(--muted)" tickLine={false} axisLine={false} />
        <YAxis stroke="var(--muted)" tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            color: 'var(--text)',
          }}
        />
        <Legend wrapperStyle={{ paddingTop: 8 }} />
        <Bar dataKey="sessions" fill="var(--accent)" radius={[6, 6, 0, 0]} name="Sessions" />
        <Bar dataKey="signups" fill="var(--accent-2)" radius={[6, 6, 0, 0]} name="Signups" />
      </BarChart>
    </ResponsiveContainer>
  );
}
