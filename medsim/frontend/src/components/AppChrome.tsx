/**
 * Application chrome: header, locale switcher, theme toggle, synthetic-data
 * banner and the layout shell.
 *
 * The locale switcher is a native `<select>` rather than a custom dropdown.
 * That is a deliberate choice: it inherits the platform's keyboard model, its
 * touch behaviour on Android and iOS, and its screen-reader semantics for free,
 * and a language picker is the last place to spend accessibility budget on a
 * bespoke widget.
 */

import { Link, NavLink } from 'react-router-dom';

import { LOCALE_META, SUPPORTED_LOCALES } from '../i18n';
import type { Locale } from '../i18n/types';
import { useApp, useI18n } from '../hooks/useApp';
import { useOnline } from '../hooks/useAsync';

export function LocaleSwitcher() {
  const { locale, setLocale } = useApp();
  const { t } = useI18n();

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="locale-select" className="sr-only">
        {t('language.change')}
      </label>
      <select
        id="locale-select"
        className="input w-auto py-1.5 pr-8 text-sm"
        value={locale}
        onChange={(event) => setLocale(event.target.value as Locale)}
        data-testid="locale-switcher"
        aria-label={t('language.change')}
      >
        {SUPPORTED_LOCALES.map((code) => (
          <option key={code} value={code} lang={code}>
            {LOCALE_META[code].nativeName}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useApp();
  const { t } = useI18n();
  const next = resolvedTheme === 'dark' ? 'light' : 'dark';

  return (
    <div className="segmented" role="group" aria-label={t('theme.label')}>
      {(['light', 'dark', 'system'] as const).map((option) => (
        <button
          key={option}
          type="button"
          className="segmented-option"
          aria-pressed={theme === option}
          onClick={() => setTheme(option)}
          data-testid={`theme-${option}`}
          title={t('theme.toggle', { mode: t(`theme.${next}` as never) })}
        >
          {t(`theme.${option}` as never)}
        </button>
      ))}
    </div>
  );
}

export function Header() {
  const { t } = useI18n();

  return (
    <header className="sticky top-0 z-30 border-b border-hairline bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div className="mx-auto flex max-w-shell flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-baseline gap-2 no-underline" data-testid="app-home-link">
          <span className="text-lg font-semibold tracking-tight text-ink">{t('app.name')}</span>
          <span className="hidden text-sm text-ink-secondary sm:inline">{t('app.tagline')}</span>
        </Link>

        <nav aria-label={t('nav.dashboard')} className="flex items-center gap-1">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `btn-ghost ${isActive ? 'bg-surface-sunken text-ink' : ''}`
            }
            data-testid="nav-cases"
          >
            {t('nav.cases')}
          </NavLink>
        </nav>

        <div className="ms-auto flex flex-wrap items-center gap-3">
          <ThemeToggle />
          <LocaleSwitcher />
        </div>
      </div>
    </header>
  );
}

/**
 * A standing, non-dismissible banner. Synthetic clinical data that looks real
 * is a genuine hazard the moment a screenshot leaves the building, so the
 * disclaimer is part of the chrome rather than a one-time toast.
 */
export function SyntheticDataBanner() {
  const { t } = useI18n();
  return (
    <div className="border-b border-warning/30 bg-warning-wash" data-testid="synthetic-banner">
      <p className="mx-auto max-w-shell px-4 py-2 text-sm text-ink sm:px-6">
        <span aria-hidden="true" className="mr-1.5">
          ⚠
        </span>
        {t('app.syntheticBanner')}
      </p>
    </div>
  );
}

export function OfflineBanner() {
  const online = useOnline();
  const { t } = useI18n();
  if (online) return null;
  return (
    <div className="border-b border-serious/30 bg-serious-wash" role="status" data-testid="offline-banner">
      <p className="mx-auto max-w-shell px-4 py-2 text-sm text-ink sm:px-6">{t('errors.offline')}</p>
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-canvas">
      <a href="#main" className="skip-link">
        {t('app.skipToContent')}
      </a>
      <SyntheticDataBanner />
      <OfflineBanner />
      <Header />
      <main id="main" className="mx-auto max-w-shell px-4 py-6 sm:px-6" tabIndex={-1}>
        {children}
      </main>
      <footer className="mx-auto max-w-shell px-4 py-8 text-sm text-ink-muted sm:px-6">
        <p>{t('app.syntheticBanner')}</p>
      </footer>
    </div>
  );
}
