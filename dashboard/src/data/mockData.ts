export type Stat = {
  id: string;
  label: string;
  value: string;
  delta: number;
  hint: string;
};

export const stats: Stat[] = [
  { id: 'revenue', label: 'Revenue', value: '$84,210', delta: 12.4, hint: 'vs last month' },
  { id: 'users', label: 'Active Users', value: '12,938', delta: 4.1, hint: 'rolling 30d' },
  { id: 'orders', label: 'Orders', value: '2,431', delta: -2.3, hint: 'vs last month' },
  { id: 'conv', label: 'Conversion', value: '3.84%', delta: 0.6, hint: 'vs last week' },
];

export type RevenuePoint = { month: string; revenue: number; expenses: number };

export const revenueSeries: RevenuePoint[] = [
  { month: 'Jan', revenue: 42000, expenses: 31000 },
  { month: 'Feb', revenue: 47500, expenses: 32400 },
  { month: 'Mar', revenue: 51000, expenses: 35100 },
  { month: 'Apr', revenue: 49500, expenses: 34000 },
  { month: 'May', revenue: 58200, expenses: 37500 },
  { month: 'Jun', revenue: 61300, expenses: 39200 },
  { month: 'Jul', revenue: 67800, expenses: 41100 },
  { month: 'Aug', revenue: 71250, expenses: 43200 },
  { month: 'Sep', revenue: 73900, expenses: 45100 },
  { month: 'Oct', revenue: 79400, expenses: 46800 },
  { month: 'Nov', revenue: 82150, expenses: 48400 },
  { month: 'Dec', revenue: 84210, expenses: 49100 },
];

export type ChannelPoint = { name: string; value: number };

export const trafficByChannel: ChannelPoint[] = [
  { name: 'Organic', value: 4820 },
  { name: 'Direct', value: 3140 },
  { name: 'Referral', value: 2210 },
  { name: 'Social', value: 1730 },
  { name: 'Email', value: 980 },
];

export type ActivityPoint = { day: string; sessions: number; signups: number };

export const weeklyActivity: ActivityPoint[] = [
  { day: 'Mon', sessions: 1840, signups: 64 },
  { day: 'Tue', sessions: 2100, signups: 81 },
  { day: 'Wed', sessions: 1990, signups: 72 },
  { day: 'Thu', sessions: 2340, signups: 95 },
  { day: 'Fri', sessions: 2680, signups: 110 },
  { day: 'Sat', sessions: 1520, signups: 48 },
  { day: 'Sun', sessions: 1280, signups: 36 },
];

export type User = {
  id: string;
  name: string;
  email: string;
  role: 'Admin' | 'Editor' | 'Viewer';
  status: 'active' | 'invited' | 'suspended';
  lastSeen: string;
};

export const users: User[] = [
  { id: 'u_001', name: 'Eva Adams', email: 'eva@mictest12.io', role: 'Admin', status: 'active', lastSeen: '2026-05-09 09:14' },
  { id: 'u_002', name: 'Marcus Liu', email: 'marcus@mictest12.io', role: 'Editor', status: 'active', lastSeen: '2026-05-09 08:42' },
  { id: 'u_003', name: 'Priya Shah', email: 'priya@mictest12.io', role: 'Editor', status: 'active', lastSeen: '2026-05-08 22:11' },
  { id: 'u_004', name: 'Diego Rivera', email: 'diego@mictest12.io', role: 'Viewer', status: 'invited', lastSeen: '—' },
  { id: 'u_005', name: 'Sana Khan', email: 'sana@mictest12.io', role: 'Viewer', status: 'active', lastSeen: '2026-05-09 07:05' },
  { id: 'u_006', name: 'Henrik Olsen', email: 'henrik@mictest12.io', role: 'Editor', status: 'suspended', lastSeen: '2026-04-21 14:33' },
  { id: 'u_007', name: 'Aisha Bello', email: 'aisha@mictest12.io', role: 'Admin', status: 'active', lastSeen: '2026-05-09 10:02' },
  { id: 'u_008', name: 'Tom Becker', email: 'tom@mictest12.io', role: 'Viewer', status: 'active', lastSeen: '2026-05-08 18:50' },
];

export type Order = {
  id: string;
  customer: string;
  amount: number;
  status: 'paid' | 'pending' | 'refunded' | 'failed';
  channel: 'web' | 'mobile' | 'partner';
  createdAt: string;
};

export const orders: Order[] = [
  { id: 'INV-10421', customer: 'Acme Corp', amount: 1240.0, status: 'paid', channel: 'web', createdAt: '2026-05-09 09:42' },
  { id: 'INV-10420', customer: 'Globex',     amount: 480.5,  status: 'pending', channel: 'partner', createdAt: '2026-05-09 09:30' },
  { id: 'INV-10419', customer: 'Initech',    amount: 2180.0, status: 'paid', channel: 'web', createdAt: '2026-05-09 08:58' },
  { id: 'INV-10418', customer: 'Umbrella',   amount: 99.0,   status: 'refunded', channel: 'mobile', createdAt: '2026-05-09 08:11' },
  { id: 'INV-10417', customer: 'Stark Ind.', amount: 5920.0, status: 'paid', channel: 'web', createdAt: '2026-05-09 07:45' },
  { id: 'INV-10416', customer: 'Wayne Ent.', amount: 312.75, status: 'failed', channel: 'mobile', createdAt: '2026-05-09 07:21' },
  { id: 'INV-10415', customer: 'Hooli',      amount: 870.0,  status: 'paid', channel: 'web', createdAt: '2026-05-09 06:58' },
  { id: 'INV-10414', customer: 'Pied Piper', amount: 145.99, status: 'pending', channel: 'partner', createdAt: '2026-05-09 06:30' },
];

export type ActivityFeedItem = {
  id: string;
  who: string;
  action: string;
  target: string;
  when: string;
};

export const activityFeed: ActivityFeedItem[] = [
  { id: 'a1', who: 'Aisha Bello',  action: 'invited',   target: 'tom@mictest12.io',     when: '2m ago' },
  { id: 'a2', who: 'Marcus Liu',   action: 'refunded',  target: 'INV-10418',            when: '14m ago' },
  { id: 'a3', who: 'Eva Adams',    action: 'updated',   target: 'Billing settings',     when: '1h ago' },
  { id: 'a4', who: 'Priya Shah',   action: 'published', target: 'Onboarding v3',        when: '3h ago' },
  { id: 'a5', who: 'Sana Khan',    action: 'commented', target: 'Q2 roadmap',           when: '5h ago' },
  { id: 'a6', who: 'Diego Rivera', action: 'joined',    target: 'the team',             when: 'yesterday' },
];
