import { NavLink } from 'react-router-dom';

type NavItem = { to: string; label: string; icon: string };

const NAV: NavItem[] = [
  { to: '/overview', label: 'Overview', icon: '◈' },
  { to: '/analytics', label: 'Analytics', icon: '◭' },
  { to: '/users', label: 'Users', icon: '◉' },
  { to: '/orders', label: 'Orders', icon: '◊' },
  { to: '/settings', label: 'Settings', icon: '⚙' },
];

type Props = { open: boolean; onClose: () => void };

export default function Sidebar({ open, onClose }: Props) {
  return (
    <>
      {open && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`sidebar ${open ? 'open' : 'closed'}`}>
        <div className="sidebar-brand">
          <span className="brand-mark">M12</span>
          <span className="brand-name">MicTest12</span>
        </div>
        <nav className="sidebar-nav">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-icon" aria-hidden>
                {item.icon}
              </span>
              <span className="sidebar-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-card">
            <div className="user-avatar">EA</div>
            <div className="user-meta">
              <div className="user-name">Eva Adams</div>
              <div className="user-role">Administrator</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
