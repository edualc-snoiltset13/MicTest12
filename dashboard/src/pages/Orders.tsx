import { useMemo, useState } from 'react';
import Card from '../components/Card';
import { orders } from '../data/mockData';
import type { Order } from '../data/mockData';

type StatusFilter = 'all' | Order['status'];
type SortKey = 'createdAt' | 'amount' | 'customer';

export default function Orders() {
  const [status, setStatus] = useState<StatusFilter>('all');
  const [sort, setSort] = useState<SortKey>('createdAt');
  const [dir, setDir] = useState<'asc' | 'desc'>('desc');

  const visible = useMemo(() => {
    const list = orders.filter((o) => status === 'all' || o.status === status);
    list.sort((a, b) => {
      const av = a[sort];
      const bv = b[sort];
      if (av < bv) return dir === 'asc' ? -1 : 1;
      if (av > bv) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }, [status, sort, dir]);

  const total = visible.reduce((sum, o) => sum + o.amount, 0);
  const paidTotal = visible
    .filter((o) => o.status === 'paid')
    .reduce((sum, o) => sum + o.amount, 0);

  function toggleSort(key: SortKey) {
    if (sort === key) setDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else {
      setSort(key);
      setDir('desc');
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Orders</h1>
          <p className="page-subtitle">
            {visible.length} orders · ${paidTotal.toLocaleString()} paid · ${total.toLocaleString()} total
          </p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-ghost">Export CSV</button>
          <button className="btn btn-primary">+ New order</button>
        </div>
      </div>

      <Card>
        <div className="toolbar">
          <select className="select" value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
            <option value="all">All statuses</option>
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="refunded">Refunded</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>
                <button className="th-sort" onClick={() => toggleSort('customer')}>
                  Customer {sort === 'customer' && (dir === 'asc' ? '↑' : '↓')}
                </button>
              </th>
              <th>Channel</th>
              <th>Status</th>
              <th>
                <button className="th-sort" onClick={() => toggleSort('createdAt')}>
                  Created {sort === 'createdAt' && (dir === 'asc' ? '↑' : '↓')}
                </button>
              </th>
              <th className="num">
                <button className="th-sort" onClick={() => toggleSort('amount')}>
                  Amount {sort === 'amount' && (dir === 'asc' ? '↑' : '↓')}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {visible.map((o) => (
              <tr key={o.id}>
                <td className="mono">{o.id}</td>
                <td>{o.customer}</td>
                <td className="muted">{o.channel}</td>
                <td>
                  <span className={`badge badge-${o.status}`}>{o.status}</span>
                </td>
                <td className="muted">{o.createdAt}</td>
                <td className="num">${o.amount.toLocaleString()}</td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">No orders match.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
