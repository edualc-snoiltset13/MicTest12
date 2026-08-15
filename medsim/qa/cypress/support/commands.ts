/// <reference types="cypress" />

/**
 * Custom commands.
 *
 * The two that carry the suite are `assertNoHorizontalOverflow` and
 * `assertNoClippedText`. Both encode a rule that is trivially stated and
 * tedious to check by hand, and both catch the class of bug that localization
 * actually produces: text that fits in English and does not fit in German.
 */

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      visitLocale(path: string, locale: string): Chainable<void>;
      setLocale(locale: string): Chainable<void>;
      assertNoHorizontalOverflow(): Chainable<void>;
      assertNoClippedText(selector: string): Chainable<void>;
      assertMinimumTouchTarget(selector: string, minPx?: number): Chainable<void>;
      assertContrastPair(selector: string, minRatio: number): Chainable<void>;
      interceptCases(alias?: string): Chainable<void>;
      chaos(headers: Record<string, string>): Chainable<void>;
      openFirstCase(): Chainable<void>;
    }
  }
}

/** Visits a path with an explicit language, bypassing browser detection. */
Cypress.Commands.add('visitLocale', (path: string, locale: string) => {
  const separator = path.includes('?') ? '&' : '?';
  cy.visit(`${path}${separator}lang=${locale}`);
  cy.get('html').should('have.attr', 'lang', locale);
});

Cypress.Commands.add('setLocale', (locale: string) => {
  cy.get('[data-testid="locale-switcher"]').select(locale);
  cy.get('html').should('have.attr', 'lang', locale);
});

/**
 * The page body must never scroll horizontally.
 *
 * Wide content - tables, charts, code - is allowed to scroll inside its own
 * container; that is the design rule. This asserts the *document* does not,
 * which is the symptom a user actually feels.
 *
 * A 1px tolerance absorbs sub-pixel rounding at fractional device scales.
 */
Cypress.Commands.add('assertNoHorizontalOverflow', () => {
  cy.document().then((doc) => {
    const element = doc.documentElement;
    const overflow = element.scrollWidth - element.clientWidth;

    if (overflow > 1) {
      // Name the culprit rather than just failing. A bare "expected 172 to be
      // at most 1" sends the reader hunting; naming the element does not.
      const offenders: string[] = [];
      const clipped = (node: Element): boolean => {
        for (let n: Element | null = node; n && n !== element; n = n.parentElement) {
          const style = doc.defaultView!.getComputedStyle(n);
          if (['hidden', 'auto', 'scroll', 'clip'].includes(style.overflowX)) return true;
        }
        return false;
      };
      for (const node of Array.from(doc.querySelectorAll('*'))) {
        const rect = node.getBoundingClientRect();
        if (rect.width > 0 && rect.right > element.clientWidth + 1 && !clipped(node)) {
          offenders.push(
            `<${node.tagName.toLowerCase()} class="${String(node.className).slice(0, 60)}"> right=${Math.round(rect.right)}`,
          );
        }
        if (offenders.length >= 5) break;
      }
      throw new Error(
        `Document scrolls horizontally by ${overflow}px at ${element.clientWidth}px wide.\n` +
          `Unclipped elements past the viewport edge:\n  ${offenders.join('\n  ') || '(none identified - check a positioned descendant)'}`,
      );
    }
  });
});

/**
 * Asserts that text is not truncated by its own box.
 *
 * `scrollWidth > clientWidth` on a text-bearing element means the glyphs do not
 * fit. This is the failure mode that separates German and Russian from English
 * in a fixed-width control: the label renders, but the last word is gone.
 *
 * Elements that deliberately truncate (`line-clamp`, `text-ellipsis`) are
 * excluded, because for those truncation is the design.
 */
Cypress.Commands.add('assertNoClippedText', (selector: string) => {
  cy.get(selector).each(($element) => {
    const element = $element[0];
    const style = window.getComputedStyle(element);

    const intentional =
      style.textOverflow === 'ellipsis' ||
      style.webkitLineClamp !== 'none' ||
      element.classList.contains('line-clamp-3') ||
      element.classList.contains('truncate');
    if (intentional) return;

    // Only inspect elements whose own text is the content.
    const text = (element.textContent ?? '').trim();
    if (!text) return;

    const horizontal = element.scrollWidth - element.clientWidth;
    expect(
      horizontal,
      `text clipped horizontally in <${element.tagName.toLowerCase()}>: "${text.slice(0, 60)}"`,
    ).to.be.lessThan(2);
  });
});

/**
 * Minimum touch-target size.
 *
 * 44px is the WCAG 2.2 AA target-size floor and the number the Samsung device
 * testing in qa/adb uses. Controls smaller than this are reliably mis-tapped
 * with a thumb, which on a clinical tool means the wrong filter or the wrong
 * case.
 */
Cypress.Commands.add('assertMinimumTouchTarget', (selector: string, minPx = 44) => {
  cy.get(selector).each(($element) => {
    const rect = $element[0].getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return; // not rendered
    expect(
      Math.min(rect.width, rect.height),
      `touch target too small for <${$element[0].tagName.toLowerCase()}> "${$element.text().trim().slice(0, 30)}"`,
    ).to.be.at.least(minPx - 1);
  });
});

/** Relative luminance contrast between an element's colour and background. */
Cypress.Commands.add('assertContrastPair', (selector: string, minRatio: number) => {
  cy.get(selector)
    .first()
    .then(($element) => {
      const element = $element[0];
      const style = window.getComputedStyle(element);

      const parse = (value: string): [number, number, number] => {
        const match = value.match(/rgba?\(([^)]+)\)/);
        if (!match) return [0, 0, 0];
        const [r, g, b] = match[1]!.split(',').map((part) => parseFloat(part.trim()));
        return [r ?? 0, g ?? 0, b ?? 0];
      };

      // Walk up for the first non-transparent background.
      let backgroundElement: Element | null = element;
      let background: [number, number, number] = [255, 255, 255];
      while (backgroundElement) {
        const value = window.getComputedStyle(backgroundElement).backgroundColor;
        if (value && !value.includes('rgba(0, 0, 0, 0)') && value !== 'transparent') {
          background = parse(value);
          break;
        }
        backgroundElement = backgroundElement.parentElement;
      }

      const luminance = ([r, g, b]: [number, number, number]): number => {
        const channel = (value: number): number => {
          const scaled = value / 255;
          return scaled <= 0.03928 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4;
        };
        return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
      };

      const foreground = parse(style.color);
      const l1 = luminance(foreground);
      const l2 = luminance(background);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

      expect(ratio, `contrast for "${$element.text().trim().slice(0, 40)}"`).to.be.at.least(minRatio);
    });
});

Cypress.Commands.add('interceptCases', (alias = 'cases') => {
  cy.intercept('GET', '**/api/v1/cases*').as(alias);
});

/**
 * Applies chaos headers to every subsequent API request.
 *
 * This is the in-process equivalent of a Charles or Proxyman rewrite rule, and
 * it is what lets the network specs run deterministically in CI. The
 * equivalent real-proxy configurations live in qa/proxy for manual testing
 * against a device.
 */
Cypress.Commands.add('chaos', (headers: Record<string, string>) => {
  cy.intercept('**/api/v1/**', (request) => {
    Object.entries(headers).forEach(([name, value]) => {
      request.headers[name] = value;
    });
  });
});

Cypress.Commands.add('openFirstCase', () => {
  cy.get('[data-testid="case-card"]').first().find('[data-testid="case-link"]').click();
  cy.get('[data-testid="case-detail"]').should('exist');
});

export {};
