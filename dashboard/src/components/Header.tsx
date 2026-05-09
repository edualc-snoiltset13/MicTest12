import { useTheme } from '../context/ThemeContext';

type Props = { onToggleSidebar: () => void };

export default function Header({ onToggleSidebar }: Props) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="app-header">
      <button className="icon-button" onClick={onToggleSidebar} aria-label="Toggle sidebar">
        ☰
      </button>
      <div className="search">
        <input type="search" placeholder="Search dashboard…" aria-label="Search" />
      </div>
      <div className="header-actions">
        <button
          className="icon-button"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? '☾' : '☀'}
        </button>
        <button className="icon-button" aria-label="Notifications">
          ◔
        </button>
        <div className="header-avatar" title="Eva Adams">
          EA
        </div>
      </div>
    </header>
  );
}
