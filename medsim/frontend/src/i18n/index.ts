/**
 * Localization module.
 *
 * Hand-rolled rather than pulled from i18next, for three reasons specific to
 * this application:
 *
 *  1. **Type safety.** The message catalogue is a TypeScript object, so
 *     `t('case.difficulty')` is checked at compile time and a missing key in
 *     any of the five locales is a build error, not a runtime `[missing]`.
 *  2. **Auditability.** A clinical tool's translations are reviewed by
 *     clinicians, not engineers. A flat `.ts` file of literal strings is
 *     reviewable; a runtime plugin chain is not.
 *  3. **Bundle size.** The whole module is under 200 lines and adds no
 *     dependency, while locale catalogues are code-split so a reader only
 *     downloads the language they use.
 *
 * What it does provide, because a real clinical UI needs it:
 *   - interpolation with `{placeholder}` syntax
 *   - CLDR plural categories via `Intl.PluralRules` (Russian needs
 *     one/few/many, which a naive `count === 1` check gets wrong)
 *   - locale-correct number, date and unit formatting via `Intl`
 *   - decimal-separator awareness (German and Russian use a comma, which is
 *     the single most common source of lab-value misreading)
 *   - persistence, `<html lang>` maintenance, and OS-language detection
 */

import type { Locale, MessageKey, Messages } from './types';
import { en } from './locales/en';

export const SUPPORTED_LOCALES: readonly Locale[] = ['en', 'de', 'es', 'nl', 'ru'] as const;

export const DEFAULT_LOCALE: Locale = 'en';

const STORAGE_KEY = 'medsim.locale';

/**
 * Locale metadata. `nativeName` is what the switcher shows - a reader looking
 * for their own language scans for "Deutsch", not "German".
 *
 * `dir` is present and honoured throughout the layout even though all five
 * shipped locales are LTR: adding Arabic or Hebrew later must be a catalogue
 * change, not a layout rewrite.
 */
export interface LocaleMeta {
  code: Locale;
  nativeName: string;
  englishName: string;
  dir: 'ltr' | 'rtl';
  /** BCP-47 tag used for Intl formatting; may be more specific than `code`. */
  intlTag: string;
  /** Decimal separator, surfaced in the UI so users can sanity-check values. */
  decimalSeparator: string;
  /** Typical expansion versus English, used by the layout stress tests. */
  expansionFactor: number;
}

export const LOCALE_META: Record<Locale, LocaleMeta> = {
  en: {
    code: 'en',
    nativeName: 'English',
    englishName: 'English',
    dir: 'ltr',
    intlTag: 'en-GB',
    decimalSeparator: '.',
    expansionFactor: 1.0,
  },
  de: {
    code: 'de',
    nativeName: 'Deutsch',
    englishName: 'German',
    dir: 'ltr',
    intlTag: 'de-DE',
    decimalSeparator: ',',
    // German runs 25-35% longer than English and produces very long compounds.
    // It is the layout-stress locale for the Cypress suite.
    expansionFactor: 1.35,
  },
  es: {
    code: 'es',
    nativeName: 'Español',
    englishName: 'Spanish',
    dir: 'ltr',
    intlTag: 'es-ES',
    decimalSeparator: ',',
    expansionFactor: 1.25,
  },
  nl: {
    code: 'nl',
    nativeName: 'Nederlands',
    englishName: 'Dutch',
    dir: 'ltr',
    intlTag: 'nl-NL',
    decimalSeparator: ',',
    expansionFactor: 1.28,
  },
  ru: {
    code: 'ru',
    nativeName: 'Русский',
    englishName: 'Russian',
    dir: 'ltr',
    intlTag: 'ru-RU',
    decimalSeparator: ',',
    // Cyrillic plus grammatical case makes Russian both long and structurally
    // different: it is the locale that exposes hardcoded plural logic.
    expansionFactor: 1.3,
  },
};

// ---------------------------------------------------------------------------
// Catalogue loading
// ---------------------------------------------------------------------------

/**
 * English is bundled eagerly as the fallback; the rest are dynamic imports so
 * Vite emits one chunk per locale.
 */
const loaders: Record<Locale, () => Promise<Messages>> = {
  en: async () => en,
  de: async () => (await import('./locales/de')).de,
  es: async () => (await import('./locales/es')).es,
  nl: async () => (await import('./locales/nl')).nl,
  ru: async () => (await import('./locales/ru')).ru,
};

const cache = new Map<Locale, Messages>([['en', en]]);

export async function loadMessages(locale: Locale): Promise<Messages> {
  const cached = cache.get(locale);
  if (cached) return cached;
  try {
    const messages = await loaders[locale]();
    cache.set(locale, messages);
    return messages;
  } catch {
    // A failed locale chunk must not blank the dashboard. Fall back to English
    // and let the UI carry on; the QA suite asserts this path explicitly.
    return en;
  }
}

// ---------------------------------------------------------------------------
// Detection & persistence
// ---------------------------------------------------------------------------

export function isSupported(value: string | null | undefined): value is Locale {
  return !!value && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

/** Reads `?lang=`, then storage, then the browser's languages, then English. */
export function detectLocale(): Locale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE;

  const fromQuery = new URLSearchParams(window.location.search).get('lang');
  if (isSupported(fromQuery)) return fromQuery;

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (isSupported(stored)) return stored;
  } catch {
    /* storage disabled (private mode / locked-down WebView) */
  }

  for (const tag of navigator.languages ?? [navigator.language]) {
    const base = tag.split('-')[0]?.toLowerCase();
    if (isSupported(base)) return base;
  }

  return DEFAULT_LOCALE;
}

export function persistLocale(locale: Locale): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* non-fatal */
  }
  // Keeps CSS hyphenation, spell-check and screen-reader pronunciation correct.
  document.documentElement.setAttribute('lang', locale);
  document.documentElement.setAttribute('dir', LOCALE_META[locale].dir);
}

// ---------------------------------------------------------------------------
// Translation
// ---------------------------------------------------------------------------

export type TranslateValues = Record<string, string | number>;

function resolve(messages: Messages, key: string): string | undefined {
  // Keys are dotted paths ("case.labs.title"). Walking the object beats a flat
  // map because it keeps the catalogue readable in nested groups.
  const value = key
    .split('.')
    .reduce<unknown>((acc, part) => (acc && typeof acc === 'object' ? (acc as Record<string, unknown>)[part] : undefined), messages);
  return typeof value === 'string' ? value : undefined;
}

function interpolate(template: string, values?: TranslateValues): string {
  if (!values) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = values[name];
    return value === undefined ? match : String(value);
  });
}

export function createTranslator(locale: Locale, messages: Messages) {
  const pluralRules = new Intl.PluralRules(LOCALE_META[locale].intlTag);

  /**
   * `t('case.count', { count: 3 })` resolves `case.count` and, if the catalogue
   * entry is an object of plural categories, selects with `Intl.PluralRules`.
   * Russian selects one/few/many/other; English selects one/other. Hardcoding
   * `count === 1 ? singular : plural` is wrong in three of our five locales.
   */
  function t(key: MessageKey, values?: TranslateValues): string {
    let template: string | undefined;

    // Which number drives plural selection is not always `count`. In the
    // "N of M cases" construction, Russian agreement follows the TOTAL, not
    // the count: "1 из 25 случаев", never "1 из 25 случая". Callers pass
    // `pluralCount` to say which number the noun agrees with.
    const selector =
      values && typeof values.pluralCount === 'number'
        ? values.pluralCount
        : values && typeof values.count === 'number'
          ? values.count
          : undefined;

    if (selector !== undefined) {
      const category = pluralRules.select(selector);
      template = resolve(messages, `${key}.${category}`) ?? resolve(messages, `${key}.other`);
    }

    template ??= resolve(messages, key);

    if (template === undefined) {
      // Fall back to English, then to the key itself. Never render blank.
      template = resolve(en, key) ?? key;
      if (import.meta.env.DEV) {
        console.warn(`[i18n] missing key "${key}" for locale "${locale}"`);
      }
    }

    return interpolate(template, values);
  }

  return t;
}

export type Translator = ReturnType<typeof createTranslator>;

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

/**
 * Locale-aware formatters.
 *
 * The decimal separator matters clinically. A TSH of 0.005 mIU/L renders as
 * "0,005" in German, Spanish, Dutch and Russian. Hand-formatting with
 * `toFixed()` and shipping "0.005" to a German clinician is a real misreading
 * risk, and it is exactly the class of bug the regional-formatting tests in
 * Phase 3 exist to catch.
 */
export function createFormatters(locale: Locale) {
  const tag = LOCALE_META[locale].intlTag;

  const numberCache = new Map<number, Intl.NumberFormat>();

  function number(value: number, decimals = 2): string {
    let formatter = numberCache.get(decimals);
    if (!formatter) {
      formatter = new Intl.NumberFormat(tag, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      });
      numberCache.set(decimals, formatter);
    }
    return formatter.format(value);
  }

  /**
   * Lab values keep the number of decimal places the analyte is conventionally
   * reported to (TSH two, haemoglobin zero, bacterial index one) rather than a
   * fixed global precision. That precision comes from the API's reference
   * interval metadata, so a lab can change it without a frontend release.
   */
  function labValue(value: number, decimals: number): string {
    return number(value, decimals);
  }

  const dateFormatter = new Intl.DateTimeFormat(tag, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  const dateTimeFormatter = new Intl.DateTimeFormat(tag, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    // Explicit: en-GB is 24-hour, en-US is 12-hour, and a lab timestamp read as
    // 08:00 when it was 20:00 is a clinical error.
    hour12: false,
  });

  function date(value: string | Date): string {
    return dateFormatter.format(typeof value === 'string' ? new Date(value) : value);
  }

  function dateTime(value: string | Date): string {
    return dateTimeFormatter.format(typeof value === 'string' ? new Date(value) : value);
  }

  const relativeFormatter = new Intl.RelativeTimeFormat(tag, { numeric: 'auto' });

  /** Day offsets on the case timeline: "day 0", "+28 days", "3 months ago". */
  function relativeDays(days: number): string {
    if (Math.abs(days) < 31) return relativeFormatter.format(days, 'day');
    if (Math.abs(days) < 365) return relativeFormatter.format(Math.round(days / 30), 'month');
    return relativeFormatter.format(Math.round(days / 365), 'year');
  }

  const listFormatter = new Intl.ListFormat(tag, { style: 'long', type: 'conjunction' });

  function list(items: string[]): string {
    return listFormatter.format(items);
  }

  function percent(value: number, decimals = 0): string {
    return new Intl.NumberFormat(tag, {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  }

  return { number, labValue, date, dateTime, relativeDays, list, percent };
}

export type Formatters = ReturnType<typeof createFormatters>;

/**
 * Picks the best available translation from an API-supplied locale map,
 * falling back through English to the untranslated field. Clinical content is
 * translated per case and may be incomplete for a newly authored case; the UI
 * must degrade to showing *something* rather than an empty heading.
 */
export function pickLocalized(
  map: Record<string, string> | undefined,
  locale: Locale,
  fallback: string,
): string {
  if (!map) return fallback;
  return map[locale] ?? map.en ?? fallback;
}
