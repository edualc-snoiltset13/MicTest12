/**
 * Tailwind configuration for the MedSimQA dashboard.
 *
 * Design decisions encoded here:
 *
 * 1. Colours are declared as CSS custom properties in `src/index.css` and
 *    referenced here through `rgb(var(--token) / <alpha-value>)`. That is what
 *    lets a single `data-theme` attribute swap the whole palette without
 *    Tailwind emitting a duplicate `dark:` variant for every utility, and it
 *    keeps one source of truth shared with the hand-rolled SVG charts, which
 *    cannot use Tailwind classes for stroke/fill geometry.
 *
 * 2. `darkMode: ['class', '[data-theme="dark"]']` means the viewer's explicit
 *    choice wins over the OS setting in both directions. The media-query
 *    fallback lives in index.css for the "system" case.
 *
 * 3. The type scale is deliberately short. A clinical dashboard needs about six
 *    sizes; more invites inconsistency between screens.
 *
 * 4. Every colour pair in the `semantic` group was checked against the surface
 *    it renders on. Body text is >= 7:1 (AAA), secondary text and large text are
 *    >= 4.5:1 (AA), and non-text UI boundaries are >= 3:1.
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        // --- surfaces ----------------------------------------------------
        canvas: 'rgb(var(--c-canvas) / <alpha-value>)',
        surface: 'rgb(var(--c-surface) / <alpha-value>)',
        'surface-raised': 'rgb(var(--c-surface-raised) / <alpha-value>)',
        'surface-sunken': 'rgb(var(--c-surface-sunken) / <alpha-value>)',

        // --- ink ---------------------------------------------------------
        ink: 'rgb(var(--c-ink) / <alpha-value>)',
        'ink-secondary': 'rgb(var(--c-ink-secondary) / <alpha-value>)',
        'ink-muted': 'rgb(var(--c-ink-muted) / <alpha-value>)',
        'ink-inverse': 'rgb(var(--c-ink-inverse) / <alpha-value>)',

        // --- lines -------------------------------------------------------
        hairline: 'rgb(var(--c-hairline) / <alpha-value>)',
        border: 'rgb(var(--c-border) / <alpha-value>)',
        grid: 'rgb(var(--c-grid) / <alpha-value>)',

        // --- brand / interactive ------------------------------------------
        accent: 'rgb(var(--c-accent) / <alpha-value>)',
        'accent-hover': 'rgb(var(--c-accent-hover) / <alpha-value>)',
        'accent-wash': 'rgb(var(--c-accent-wash) / <alpha-value>)',
        focus: 'rgb(var(--c-focus) / <alpha-value>)',

        // --- clinical status ------------------------------------------------
        // Reserved. These are never reused as chart series colours, and they
        // always ship with an icon or a text label so that colour alone never
        // carries the meaning of a result flag.
        good: 'rgb(var(--c-good) / <alpha-value>)',
        'good-wash': 'rgb(var(--c-good-wash) / <alpha-value>)',
        warning: 'rgb(var(--c-warning) / <alpha-value>)',
        'warning-wash': 'rgb(var(--c-warning-wash) / <alpha-value>)',
        serious: 'rgb(var(--c-serious) / <alpha-value>)',
        'serious-wash': 'rgb(var(--c-serious-wash) / <alpha-value>)',
        critical: 'rgb(var(--c-critical) / <alpha-value>)',
        'critical-wash': 'rgb(var(--c-critical-wash) / <alpha-value>)',

        // --- chart series (validated categorical order) ---------------------
        // Slots 1-3 only. The validator confirms these three clear the
        // all-pairs CVD and normal-vision floors in both modes; a fourth slot
        // would not, so the compare view caps at three series and folds the
        // rest into small multiples.
        'series-1': 'rgb(var(--c-series-1) / <alpha-value>)',
        'series-2': 'rgb(var(--c-series-2) / <alpha-value>)',
        'series-3': 'rgb(var(--c-series-3) / <alpha-value>)',
      },

      fontFamily: {
        sans: [
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Noto Sans',
          // Cyrillic coverage for the Russian locale on systems whose default
          // UI font lacks it.
          'Noto Sans Cyrillic',
          'Arial',
          'sans-serif',
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'Liberation Mono', 'monospace'],
      },

      fontSize: {
        // A short, deliberate scale. label -> hero, nothing in between.
        label: ['0.6875rem', { lineHeight: '1rem', letterSpacing: '0.06em' }],
        sm: ['0.8125rem', { lineHeight: '1.25rem' }],
        base: ['0.9375rem', { lineHeight: '1.5rem' }],
        lg: ['1.0625rem', { lineHeight: '1.625rem' }],
        xl: ['1.375rem', { lineHeight: '1.875rem', letterSpacing: '-0.011em' }],
        '2xl': ['1.75rem', { lineHeight: '2.25rem', letterSpacing: '-0.019em' }],
        hero: ['2.5rem', { lineHeight: '2.75rem', letterSpacing: '-0.024em' }],
      },

      spacing: {
        // 4px base grid; these are the two off-grid values the layout needs.
        4.5: '1.125rem',
        18: '4.5rem',
      },

      borderRadius: {
        card: '0.75rem',
        control: '0.5rem',
        pill: '9999px',
      },

      boxShadow: {
        // Shadows are hairline-plus-diffuse rather than heavy drops; on a dark
        // surface the ring does the work because the shadow is invisible.
        card: '0 1px 2px rgb(var(--c-shadow) / 0.06), 0 4px 12px rgb(var(--c-shadow) / 0.04)',
        raised: '0 2px 4px rgb(var(--c-shadow) / 0.08), 0 12px 28px rgb(var(--c-shadow) / 0.08)',
        focus: '0 0 0 3px rgb(var(--c-focus) / 0.45)',
      },

      maxWidth: {
        // ~72 characters at the base size: the readable measure for the long
        // clinical narratives (smear reports, histories).
        prose: '68ch',
        shell: '96rem',
      },

      transitionDuration: {
        // Everything is fast. A dashboard that animates slowly feels broken.
        DEFAULT: '150ms',
      },

      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'none' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'draw-line': {
          from: { strokeDashoffset: '1' },
          to: { strokeDashoffset: '0' },
        },
      },

      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        shimmer: 'shimmer 1.6s infinite',
        'draw-line': 'draw-line 600ms ease-out forwards',
      },

      gridTemplateColumns: {
        // The dashboard shell: fixed filter rail, fluid content.
        dashboard: 'minmax(15rem, 17rem) minmax(0, 1fr)',
      },
    },
  },
  plugins: [],
};
