import { useState } from 'react';
import type { FormEvent } from 'react';
import Card from '../components/Card';
import { useTheme } from '../context/ThemeContext';

export default function Settings() {
  const { theme, setTheme } = useTheme();
  const [profile, setProfile] = useState({
    name: 'Eva Adams',
    email: 'eva@mictest12.io',
    role: 'Administrator',
  });
  const [notifs, setNotifs] = useState({
    email: true,
    desktop: true,
    weekly: false,
  });
  const [saved, setSaved] = useState(false);

  function update<K extends keyof typeof profile>(key: K, v: string) {
    setProfile((p) => ({ ...p, [key]: v }));
    setSaved(false);
  }

  function save(e: FormEvent) {
    e.preventDefault();
    setSaved(true);
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p className="page-subtitle">Manage your profile, appearance, and notifications.</p>
        </div>
      </div>

      <div className="grid grid-2">
        <Card title="Profile" subtitle="How others see you on the team">
          <form className="form" onSubmit={save}>
            <label className="field">
              <span>Full name</span>
              <input
                className="input"
                value={profile.name}
                onChange={(e) => update('name', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Email</span>
              <input
                className="input"
                type="email"
                value={profile.email}
                onChange={(e) => update('email', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Role</span>
              <input className="input" value={profile.role} readOnly />
            </label>
            <div className="form-actions">
              <button className="btn btn-primary" type="submit">Save changes</button>
              {saved && <span className="saved-toast">✓ Saved</span>}
            </div>
          </form>
        </Card>

        <Card title="Appearance" subtitle="Choose your theme">
          <div className="theme-options">
            <button
              type="button"
              className={`theme-option ${theme === 'light' ? 'active' : ''}`}
              onClick={() => setTheme('light')}
            >
              <div className="theme-preview light-preview" />
              <span>Light</span>
            </button>
            <button
              type="button"
              className={`theme-option ${theme === 'dark' ? 'active' : ''}`}
              onClick={() => setTheme('dark')}
            >
              <div className="theme-preview dark-preview" />
              <span>Dark</span>
            </button>
          </div>
        </Card>
      </div>

      <Card title="Notifications" subtitle="Decide how you want to be notified">
        <ul className="toggle-list">
          <li>
            <div>
              <strong>Email alerts</strong>
              <p className="muted">Receive emails for important updates</p>
            </div>
            <Toggle
              checked={notifs.email}
              onChange={(v) => setNotifs({ ...notifs, email: v })}
            />
          </li>
          <li>
            <div>
              <strong>Desktop notifications</strong>
              <p className="muted">Show a system notification in the browser</p>
            </div>
            <Toggle
              checked={notifs.desktop}
              onChange={(v) => setNotifs({ ...notifs, desktop: v })}
            />
          </li>
          <li>
            <div>
              <strong>Weekly digest</strong>
              <p className="muted">Summary of activity sent every Monday</p>
            </div>
            <Toggle
              checked={notifs.weekly}
              onChange={(v) => setNotifs({ ...notifs, weekly: v })}
            />
          </li>
        </ul>
      </Card>

      <Card title="Danger zone" className="danger-zone">
        <div className="danger-row">
          <div>
            <strong>Delete account</strong>
            <p className="muted">Permanently remove your account and all associated data.</p>
          </div>
          <button className="btn btn-danger">Delete account</button>
        </div>
      </Card>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      className={`toggle ${checked ? 'on' : ''}`}
      onClick={() => onChange(!checked)}
    >
      <span className="toggle-knob" />
    </button>
  );
}
