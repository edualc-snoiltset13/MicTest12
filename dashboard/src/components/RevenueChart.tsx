import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { revenueSeries } from '../data/mockData';

export default function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={revenueSeries} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.45} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="expFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent-2)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--accent-2)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" stroke="var(--muted)" tickLine={false} axisLine={false} />
        <YAxis
          stroke="var(--muted)"
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            color: 'var(--text)',
          }}
          formatter={(v: number) => `$${v.toLocaleString()}`}
        />
        <Legend wrapperStyle={{ paddingTop: 8 }} />
        <Area
          type="monotone"
          dataKey="revenue"
          stroke="var(--accent)"
          strokeWidth={2}
          fill="url(#revFill)"
          name="Revenue"
        />
        <Area
          type="monotone"
          dataKey="expenses"
          stroke="var(--accent-2)"
          strokeWidth={2}
          fill="url(#expFill)"
          name="Expenses"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
