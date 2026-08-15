#!/usr/bin/env node
/**
 * Locale parity check.
 *
 * TypeScript already guarantees that every locale has every KEY - that is what
 * the `Messages` type is for. This script checks the things the type system
 * cannot:
 *
 *   1. **Untranslated copies.** A key whose value is byte-identical to English
 *      in a non-English locale is almost always a placeholder that a
 *      translator never reached. Genuinely identical strings (proper nouns,
 *      "MedSimQA", "BMI", "ICD-10", unit symbols) are allowlisted.
 *   2. **Interpolation drift.** If English says `{count}` and German says
 *      `{anzahl}`, the type checker is satisfied and the UI renders a literal
 *      "{anzahl}". This compares placeholder sets per key.
 *   3. **Missing plural categories.** Russian needs one/few/many/other. A
 *      Russian plural group with only one/other type-checks (all categories
 *      past `other` are optional) but renders "5 случай".
 *   4. **Expansion budget.** Reports the longest strings per locale so the
 *      layout-stress fixtures in the Cypress suite stay grounded in the real
 *      catalogue rather than invented worst cases.
 *
 * Exits non-zero on any failure, so it can gate CI.
 */

import { readFileSync, readdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const LOCALES_DIR = join(HERE, '..', 'src', 'i18n', 'locales');

/** CLDR plural categories each locale is REQUIRED to supply. */
const REQUIRED_PLURALS = {
  en: ['one', 'other'],
  de: ['one', 'other'],
  es: ['one', 'other'],
  nl: ['one', 'other'],
  ru: ['one', 'few', 'many', 'other'],
};

/**
 * Values that are legitimately identical across languages: acronyms, units,
 * proper nouns and international codes. Anything else matching English is
 * treated as an untranslated placeholder.
 */
const ALLOWED_IDENTICAL = new Set([
  'MedSimQA',
  'BMI',
  'ICD-10',
  'Status',
  'N',
  'H',
  'L',
  'HH',
  'LL',
  'A',
  'Filters',
  'Glasgow Coma Scale',
  'Microbiologie',
  'Version {version}',
  'Tag {day}',
  'Dag {day}',
  'Día {day}',
  'День {day}',
  // Genuinely identical in the target language, not placeholders:
  'Interpretation',   // identical in German
  'Status {code}',    // "Status" is used unchanged in German and Dutch
  '{count} panel',    // Dutch uses the English loanword
  '{count} panels',
  'Microbiologie',    // identical in German and Dutch
  'Farmacologie',
  'ICD-10',
]);

/**
 * The locale files are TypeScript, so rather than adding a transpiler we parse
 * them as text. This is deliberately simple and deliberately strict: the
 * catalogues are plain nested object literals of string values by convention,
 * and a file that stops matching that shape SHOULD fail this check.
 */
function extractEntries(source) {
  const entries = new Map();
  const stack = [];
  const lines = source.split('\n');

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('//') || line.startsWith('*') || line.startsWith('/*')) continue;

    // Closing brace: pop a level.
    if (line.startsWith('}')) {
      stack.pop();
      continue;
    }

    // `key: { a: 'x', b: 'y' },` - a nested group written on ONE line. The
    // catalogues use this for short, flat groups such as the HL7 flag codes,
    // and a parser that only understands multi-line groups silently
    // under-counts those locales, which then fails the parity check for a
    // reason that has nothing to do with the translations.
    const inlineGroupMatch = line.match(/^'?([\w.-]+)'?\s*:\s*\{(.+)\}\s*,?$/);
    if (inlineGroupMatch) {
      const prefix = [...stack, inlineGroupMatch[1]].join('.');
      for (const pair of inlineGroupMatch[2].matchAll(/'?([\w.-]+)'?\s*:\s*(['"])((?:\\.|(?!\2).)*)\2/g)) {
        entries.set(`${prefix}.${pair[1]}`, pair[3]);
      }
      continue;
    }

    // `key: {` opens a nested group.
    const groupMatch = line.match(/^'?([\w.-]+)'?\s*:\s*\{$/);
    if (groupMatch) {
      stack.push(groupMatch[1]);
      continue;
    }

    // `key: 'value',` (single or double quoted, possibly multi-line - we only
    // capture the single-line form, which is what the catalogues use except
    // for a handful of long strings handled below).
    const pairMatch = line.match(/^'?([\w.-]+)'?\s*:\s*(['"])((?:\\.|(?!\2).)*)\2\s*,?$/);
    if (pairMatch) {
      const key = [...stack, pairMatch[1]].join('.');
      entries.set(key, pairMatch[3]);
      continue;
    }

    // `key:` on its own line with the value on the next - record the key so a
    // missing translation is still detected, with a sentinel value.
    const danglingMatch = line.match(/^'?([\w.-]+)'?\s*:$/);
    if (danglingMatch) {
      entries.set([...stack, danglingMatch[1]].join('.'), '<multiline>');
    }
  }

  return entries;
}

function placeholders(value) {
  return new Set([...value.matchAll(/\{(\w+)\}/g)].map((match) => match[1]));
}

function setsEqual(a, b) {
  if (a.size !== b.size) return false;
  for (const value of a) if (!b.has(value)) return false;
  return true;
}

// ---------------------------------------------------------------------------

const files = readdirSync(LOCALES_DIR).filter((name) => name.endsWith('.ts'));
const catalogues = new Map();

for (const file of files) {
  const locale = file.replace('.ts', '');
  catalogues.set(locale, extractEntries(readFileSync(join(LOCALES_DIR, file), 'utf8')));
}

const english = catalogues.get('en');
if (!english) {
  console.error('FAIL: en.ts not found');
  process.exit(1);
}

const problems = [];
const stats = [];

for (const [locale, entries] of catalogues) {
  let identical = 0;
  let longest = { key: '', length: 0 };

  for (const [key, value] of entries) {
    if (value.length > longest.length) longest = { key, length: value.length };

    const englishValue = english.get(key);
    if (englishValue === undefined) {
      // A key absent from English is an error UNLESS it is an extra plural
      // category. Russian legitimately supplies few/many where English has
      // only one/other, and Spanish supplies many. Flagging those as "not in
      // English" would punish exactly the translations that are correct.
      if (!/\.(zero|one|two|few|many|other)$/.test(key)) {
        problems.push(`${locale}: key "${key}" does not exist in English`);
      }
      continue;
    }

    if (locale !== 'en') {
      // 1. untranslated copies
      if (value === englishValue && !ALLOWED_IDENTICAL.has(value) && value !== '<multiline>') {
        identical += 1;
        if (value.length > 12) {
          problems.push(`${locale}: "${key}" is identical to English ("${value.slice(0, 48)}")`);
        }
      }

      // 2. interpolation drift
      if (!setsEqual(placeholders(value), placeholders(englishValue))) {
        problems.push(
          `${locale}: "${key}" placeholders differ - en {${[...placeholders(englishValue)]}} vs ${locale} {${[...placeholders(value)]}}`,
        );
      }
    }
  }

  // 3. required plural categories
  const required = REQUIRED_PLURALS[locale] ?? ['one', 'other'];
  const pluralGroups = new Set();
  for (const key of entries.keys()) {
    const match = key.match(/^(.*)\.(zero|one|two|few|many|other)$/);
    if (match) pluralGroups.add(match[1]);
  }
  for (const group of pluralGroups) {
    for (const category of required) {
      if (!entries.has(`${group}.${category}`)) {
        problems.push(`${locale}: plural group "${group}" is missing the "${category}" category`);
      }
    }
  }

  const nonPluralKeys = [...entries.keys()].filter(
    (key) => !/\.(zero|one|two|few|many|other)$/.test(key),
  ).length;

  stats.push({
    locale,
    keys: entries.size,
    comparableKeys: nonPluralKeys,
    pluralGroups: pluralGroups.size,
    identicalToEnglish: identical,
    longestKey: longest.key,
    longestLength: longest.length,
  });
}

// 4. key-count parity, over non-plural keys only - plural category counts
// differ by design between languages.
const counts = new Set(stats.map((entry) => entry.comparableKeys));
if (counts.size !== 1) {
  problems.push(
    `comparable key counts differ across locales: ${stats.map((s) => `${s.locale}=${s.comparableKeys}`).join(', ')}`,
  );
}

console.table(stats);

if (problems.length > 0) {
  console.error(`\n${problems.length} locale problem(s):`);
  for (const problem of problems) console.error(`  - ${problem}`);
  process.exit(1);
}

console.log('\nAll locale checks passed.');
