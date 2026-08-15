/**
 * Types derived from the English catalogue.
 *
 * `Messages` is a *structural* mirror of `en` with every leaf widened from a
 * string literal to `string`. That is what makes de/es/nl/ru type-check against
 * English: they must have exactly the same keys, but may have any string value.
 *
 * `MessageKey` is the union of every dotted path in the catalogue, so
 * `t('case.sections.labs')` is checked at compile time and `t('case.sectons.labs')`
 * is a build error rather than a runtime fallback.
 */

import type { en } from './locales/en';

export type Locale = 'en' | 'de' | 'es' | 'nl' | 'ru';

/** The six CLDR plural categories. */
export type PluralCategory = 'zero' | 'one' | 'two' | 'few' | 'many' | 'other';

/**
 * A plural group. `other` is mandatory because it is the universal fallback;
 * every other category is optional because which ones a language uses is a
 * property of the language, not of the catalogue.
 *
 * This is why the widening below special-cases plural groups. English uses
 * one/other, but Russian needs one/few/many/other and Spanish adds many. If
 * the type were derived structurally from English, those extra categories
 * would be *errors* - which is exactly backwards, since supplying them is
 * what makes the translation correct.
 */
export type PluralGroup = { other: string } & Partial<Record<PluralCategory, string>>;

/**
 * Recursively widen string literals to `string`, preserving the key shape -
 * except for plural groups, which widen to the full CLDR-capable shape.
 */
type Widen<T> = T extends string
  ? string
  : T extends { one: string; other: string }
    ? PluralGroup
    : { [K in keyof T]: Widen<T[K]> };

export type Messages = Widen<typeof en>;

/**
 * Dotted-path union over the catalogue.
 *
 * The recursion is bounded by the catalogue's actual depth (four levels), which
 * keeps TypeScript from hitting its instantiation limit. Plural groups are
 * included as their parent key too, since `t('labs.panelCount', { count })`
 * addresses the group rather than a specific category.
 */
type Join<K, P> = K extends string | number
  ? P extends string | number
    ? `${K}${'' extends P ? '' : '.'}${P}`
    : never
  : never;

type Paths<T, Depth extends number = 4> = [Depth] extends [never]
  ? never
  : T extends string
    ? ''
    : {
        [K in keyof T]-?: K extends string | number
          ? `${K}` | Join<K, Paths<T[K], Prev[Depth]>>
          : never;
      }[keyof T];

type Prev = [never, 0, 1, 2, 3, 4, 5, 6];

export type MessageKey = Paths<typeof en>;

/** The metadata a locale must supply alongside its catalogue. */
export interface LocaleModule {
  locale: Locale;
  messages: Messages;
}
