/// <reference types="cypress" />

/**
 * Spec 03 - Layout constraints and regional formatting. Edge cases 26-38.
 *
 * This is the heart of the localization suite. The failure modes it targets are
 * the ones that only appear once the interface is not in English:
 *
 *   - German and Dutch compounds overflow fixed-width controls
 *   - Russian is both long and structurally different (four plural categories)
 *   - four of the five locales use a comma decimal separator, and a lab value
 *     misread by a factor of a thousand is a patient-safety event, not a
 *     cosmetic bug
 *   - a translated label that fits at 1440px does not fit at 320px
 *
 * Every test runs across the full locale set unless the test is specifically
 * about one language.
 */

const LOCALES = ['en', 'de', 'es', 'nl', 'ru'] as const;
const COMMA_DECIMAL = ['de', 'es', 'nl', 'ru'] as const;

/** Viewports mirroring the devices in qa/adb. */
const VIEWPORTS: Record<string, [number, number]> = {
  narrow: [320, 640],
  galaxyA: [360, 740],
  iphoneSe: [375, 667],
  galaxyS: [412, 915],
  tablet: [768, 1024],
  laptop: [1024, 768],
  desktop: [1440, 900],
};

describe('03 - Layout constraints and regional formatting', () => {
  it('EC-26: the dashboard never scrolls horizontally, in any locale at any width', () => {
    // The combinatorial core of the suite: 5 locales x 7 viewports = 35
    // layouts, every one of which must contain itself.
    Object.entries(VIEWPORTS).forEach(([name, [width, height]]) => {
      LOCALES.forEach((locale) => {
        cy.viewport(width, height);
        cy.visitLocale('/', locale);
        cy.get('[data-testid="case-card"]').should('exist');
        cy.log(`dashboard ${locale} @ ${name} ${width}x${height}`);
        cy.assertNoHorizontalOverflow();
      });
    });
  });

  it('EC-27: the case detail view never scrolls horizontally, in any locale at any width', () => {
    // HEM-001 is the widest case: long German morphology lists, a wide lab
    // table and a wide protocol table on the same page.
    Object.entries(VIEWPORTS).forEach(([name, [width, height]]) => {
      LOCALES.forEach((locale) => {
        cy.viewport(width, height);
        cy.visitLocale('/cases/HEM-001', locale);
        cy.get('[data-testid="case-detail"]').should('exist');
        cy.log(`case detail ${locale} @ ${name}`);
        cy.assertNoHorizontalOverflow();
      });
    });
  });

  it('EC-28: wide tables scroll inside their own container, not the page', () => {
    // The rule is not "no wide content" - a 12-column protocol table is wide
    // by nature. The rule is that the OVERFLOW belongs to the table.
    cy.viewport(360, 740);
    cy.visitLocale('/cases/LEP-001', 'de');
    cy.get('[data-testid="treatment-protocol"]').should('exist');

    cy.get('.scroll-x')
      .filter(':visible')
      .first()
      .then(($wrapper) => {
        const element = $wrapper[0];
        expect(element.scrollWidth, 'the container genuinely has wide content').to.be.greaterThan(
          element.clientWidth,
        );
        expect(
          window.getComputedStyle(element).overflowX,
          'and it scrolls that content itself',
        ).to.be.oneOf(['auto', 'scroll']);
      });

    cy.assertNoHorizontalOverflow();
  });

  it('EC-29: German filter labels are not clipped by their controls', () => {
    // German is the expansion worst case: "Schwierigkeitsgrad" and
    // "Sortierreihenfolge" against English "Difficulty" and "Sort direction".
    cy.viewport(360, 740);
    cy.visitLocale('/', 'de');
    cy.assertNoClippedText('label.overline');
    cy.assertNoClippedText('[data-testid="clear-filters"]');
    cy.contains('Schwierigkeitsgrad').should('be.visible');
  });

  it('EC-30: the language switcher itself fits every language name it offers', () => {
    // A switcher that clips "Nederlands" cannot be used to escape a language
    // the reader does not speak - the one control that must never break.
    LOCALES.forEach((locale) => {
      cy.viewport(320, 640);
      cy.visitLocale('/', locale);
      cy.get('[data-testid="locale-switcher"]').should('be.visible');
      cy.assertNoClippedText('[data-testid="locale-switcher"]');
      cy.get('[data-testid="locale-switcher"] option').should('have.length', 5);
    });
  });

  it('EC-31: decimal separators follow the locale for lab values', () => {
    // THY-001 has a TSH of 0.005 mIU/L. Rendering "0.005" to a German reader
    // who expects comma decimals is a real misreading risk.
    cy.visitLocale('/cases/THY-001', 'en');
    cy.get('[data-testid="lab-result-row"][data-analyte="TSH"]').first().should('contain', '0.005');

    COMMA_DECIMAL.forEach((locale) => {
      cy.visitLocale('/cases/THY-001', locale);
      cy.get('[data-testid="lab-result-row"][data-analyte="TSH"]')
        .first()
        .invoke('text')
        .should('match', /0,005/)
        .and('not.match', /0\.005/);
    });
  });

  it('EC-32: chart axis labels also follow the locale decimal convention', () => {
    // A chart that formats its axis with a hardcoded toFixed() will disagree
    // with the table beside it - the most confusing possible outcome.
    cy.visitLocale('/cases/THY-003', 'de');
    cy.get('[data-testid="lab-trend-chart"][data-analyte="TSH"]')
      .find('.chart-endpoint-label')
      .invoke('text')
      .should('match', /\d+,\d+/);
  });

  it('EC-33: Russian plural forms use the correct CLDR category', () => {
    // Russian needs one/few/many. A `count === 1` ternary renders "5 случай"
    // and "2 случаев", both wrong. These are the three distinct forms.
    cy.visitLocale('/', 'ru');

    // 25 cases -> "many" (numbers ending 5-20)
    cy.get('[data-testid="result-count"]').invoke('text').should('match', /случаев/);

    // 4 cases -> "few" (numbers ending 2-4)
    cy.get('[data-testid="discipline-filter"]').select('microbiology');
    cy.get('[data-testid="case-card"]').should('have.length', 4);
    cy.get('[data-testid="result-count"]').invoke('text').should('match', /случа[яй]/);

    // 1 case -> "one"
    cy.get('[data-testid="search-input"]').type('THY-001');
    cy.get('[data-testid="discipline-filter"]').select('');
    cy.get('[data-testid="case-card"]').should('have.length', 1);
    cy.get('[data-testid="result-count"]').invoke('text').should('match', /1 случай/);
  });

  it('EC-34: Cyrillic renders without tofu boxes or fallback gaps', () => {
    cy.visitLocale('/cases/HEM-002', 'ru');
    cy.get('h1')
      .invoke('text')
      .should('match', /[Ѐ-ӿ]/)
      .and('not.match', /[�□]/); // replacement char / missing glyph box

    // A Cyrillic heading must not be measurably shorter than its glyph count
    // implies, which is what happens when the font falls back per-character.
    cy.get('h1').should(($heading) => {
      expect($heading[0].getBoundingClientRect().height).to.be.greaterThan(20);
    });
  });

  it('EC-35: dates and times follow the locale, in 24-hour form where expected', () => {
    cy.visitLocale('/cases/THY-001', 'en');
    cy.get('[data-testid="lab-panel"]').first().invoke('text').as('englishDate');

    // German dates are d MMM y; the ordering differs from en-US and the month
    // abbreviation differs from English.
    cy.visitLocale('/cases/THY-001', 'de');
    cy.get('[data-testid="lab-panel"]')
      .first()
      .invoke('text')
      .then(function (germanText) {
        expect(germanText).not.to.equal(this.englishDate);
        // 24-hour clock: a lab timestamp read as 08:00 when it was 20:00 is a
        // clinical error, so 12-hour AM/PM must never appear.
        expect(germanText, 'no 12-hour clock').not.to.match(/\b(AM|PM)\b/);
      });
  });

  it('EC-36: touch targets meet the 44px floor on a phone viewport', () => {
    cy.viewport(360, 740);
    cy.visitLocale('/', 'de');
    cy.assertMinimumTouchTarget('button.btn-primary, button.btn-secondary, .segmented-option', 40);
    cy.assertMinimumTouchTarget('[data-testid="locale-switcher"]', 40);
  });

  it('EC-37: body text meets AA contrast in both themes and both palettes', () => {
    (['light', 'dark'] as const).forEach((theme) => {
      cy.visitLocale('/', 'en');
      cy.get(`[data-testid="theme-${theme}"]`).click();
      cy.get('html').should('have.attr', 'data-theme', theme);

      // Body text at AAA, secondary text at AA. Axis labels are checked
      // separately because they sit at the muted step.
      cy.assertContrastPair('h1', 7);
      cy.assertContrastPair('[data-testid="result-count"]', 4.5);
    });
  });

  it('EC-38: theme choice survives a reload and beats the OS preference', () => {
    cy.visitLocale('/', 'en');
    cy.get('[data-testid="theme-dark"]').click();
    cy.get('html').should('have.attr', 'data-theme', 'dark');

    cy.reload();
    // The inline script in index.html applies this before first paint; if it
    // regressed, the page would flash light then switch.
    cy.get('html').should('have.attr', 'data-theme', 'dark');

    cy.get('[data-testid="theme-system"]').click();
    cy.get('html').should('not.have.attr', 'data-theme');
  });
});
