import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { trafficByChannel } from '../data/mockData';

const COLORS = ['#5b8def', '#27c39f', '#f4a13c', '#d36ad3', '#ef6b6b'];

export default function ChannelChart() {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Tooltip
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            color: 'var(--text)',
          }}
        />
        <Legend />
        <Pie
          data={trafficByChannel}
          dataKey="value"
          nameKey="name"
          innerRadius={56}
          outerRadius={90}
          paddingAngle={2}
        >
          {trafficByChannel.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="var(--surface)" />
          ))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}
