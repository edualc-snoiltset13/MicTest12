import { useMemo, useState } from 'react';
import Card from '../components/Card';
import { users } from '../data/mockData';
import type { User } from '../data/mockData';

type RoleFilter = 'all' | User['role'];
type StatusFilter = 'all' | User['status'];

export default function Users() {
  const [query, setQuery] = useState('');
  const [role, setRole] = useState<RoleFilter>('all');
  const [status, setStatus] = useState<StatusFilter>('all');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return users.filter((u) => {
      if (role !== 'all' && u.role !== role) return false;
      if (status !== 'all' && u.status !== status) return false;
      if (q && !`${u.name} ${u.email}`.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [query, role, status]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Users</h1>
          <p className="page-subtitle">{users.length} team members and collaborators.</p>
        </div>
        <div className="page-header-actions">
          <button className="btn btn-primary">+ Invite user</button>
        </div>
      </div>

      <Card>
        <div className="toolbar">
          <input
            className="input"
            type="search"
            placeholder="Search by name or email…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <select className="select" value={role} onChange={(e) => setRole(e.target.value as RoleFilter)}>
            <option value="all">All roles</option>
            <option value="Admin">Admin</option>
            <option value="Editor">Editor</option>
            <option value="Viewer">Viewer</option>
          </select>
          <select className="select" value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)}>
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="invited">Invited</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>

        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Last seen</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td>
                  <div className="user-row">
                    <div className="avatar">{initials(u.name)}</div>
                    <span>{u.name}</span>
                  </div>
                </td>
                <td className="muted">{u.email}</td>
                <td>{u.role}</td>
                <td>
                  <span className={`badge badge-${u.status}`}>{u.status}</span>
                </td>
                <td className="muted">{u.lastSeen}</td>
                <td className="row-actions">
                  <button className="btn-icon" aria-label="More">⋯</button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="empty">No users match those filters.</td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function initials(name: string) {
  return name
    .split(' ')
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase();
}
