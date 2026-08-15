/**
 * Application context: locale, formatters and theme.
 *
 * One context rather than three, because every consumer that needs `t` also
 * needs `fmt` (a translated label beside a locale-formatted number), and
 * splitting them only adds provider nesting without reducing re-renders.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  createFormatters,
  createTranslator,
  detectLocale,
  loadMessages,
  LOCALE_META,
  persistLocale,
  SUPPORTED_LOCALES,
  type Formatters,
  type Translator,
} from '../i18n';
import { en } from '../i18n/locales/en';
import type { Locale, Messages } from '../i18n/types';

export type ThemeChoice = 'light' | 'dark' | 'system';

const THEME_KEY = 'medsim.theme';

interface AppContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  localeReady: boolean;
  t: Translator;
  fmt: Formatters;
  theme: ThemeChoice;
  setTheme: (theme: ThemeChoice) => void;
  /** The theme actually rendering, after resolving `system`. */
  resolvedTheme: 'light' | 'dark';
}

const AppContext = createContext<AppContextValue | null>(null);

function readStoredTheme(): ThemeChoice {
  try {
    const stored = window.localStorage.getItem(THEME_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    /* storage unavailable */
  }
  return 'system';
}

function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === 'system') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', choice);
  }
  try {
    if (choice === 'system') window.localStorage.removeItem(THEME_KEY);
    else window.localStorage.setItem(THEME_KEY, choice);
  } catch {
    /* non-fatal */
  }
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => detectLocale());
  const [messages, setMessages] = useState<Messages>(en);
  const [localeReady, setLocaleReady] = useState(false);
  const [theme, setThemeState] = useState<ThemeChoice>(readStoredTheme);
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false,
  );

  // --- locale ------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    setLocaleReady(false);
    loadMessages(locale).then((loaded) => {
      if (cancelled) return;
      setMessages(loaded);
      setLocaleReady(true);
    });
    persistLocale(locale);
    return () => {
      cancelled = true;
    };
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    if (!SUPPORTED_LOCALES.includes(next)) return;
    setLocaleState(next);
    // Keep the URL shareable: a colleague pasting the link gets the same
    // language, which matters when a reviewer reports a layout bug.
    const url = new URL(window.location.href);
    url.searchParams.set('lang', next);
    window.history.replaceState({}, '', url);
  }, []);

  // --- theme -------------------------------------------------------------
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia?.('(prefers-color-scheme: dark)');
    if (!media) return;
    const listener = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, []);

  const t = useMemo(() => createTranslator(locale, messages), [locale, messages]);
  const fmt = useMemo(() => createFormatters(locale), [locale]);
  const resolvedTheme: 'light' | 'dark' =
    theme === 'system' ? (systemDark ? 'dark' : 'light') : theme;

  const value = useMemo<AppContextValue>(
    () => ({
      locale,
      setLocale,
      localeReady,
      t,
      fmt,
      theme,
      setTheme: setThemeState,
      resolvedTheme,
    }),
    [locale, setLocale, localeReady, t, fmt, theme, resolvedTheme],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used inside an AppProvider');
  }
  return context;
}

/** Convenience accessor for the common `t` + `fmt` pair. */
export function useI18n() {
  const { t, fmt, locale } = useApp();
  return { t, fmt, locale, meta: LOCALE_META[locale] };
}
