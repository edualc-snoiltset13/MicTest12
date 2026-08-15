/// <reference types="cypress" />

/**
 * Spec 02 - Clinical data rendering. Edge cases 14-25.
 *
 * These assert that the clinically load-bearing parts of a case render
 * correctly and, where a value is dangerous to misread, that redundant
 * non-colour channels are present.
 */

describe('02 - Clinical data rendering', () => {
  it('EC-14: a critical result is distinguished by more than colour', () => {
    // THY-002 has a TSH of 68.4 flagged critically high.
    cy.visitLocale('/cases/THY-002', 'en');
    cy.get('[data-testid="flag-HH"]').should('exist');

    cy.get('[data-testid="flag-HH"]')
      .first()
      .then(($badge) => {
        const text = $badge.text();
        // Three redundant channels: a directional glyph, the HL7 short code,
        // and a full translated name for assistive technology.
        expect(text, 'directional glyph present').to.match(/[▲▼]/);
        expect(text, 'HL7 short code present').to.contain('HH');
        expect(text, 'accessible full name present').to.contain('Critically high');
      });
  });

  it('EC-15: a critical row is visually marked in the results table', () => {
    cy.visitLocale('/cases/HEM-003', 'en');
    // HEM-003 has an LDH of 3840 and a haemoglobin of 54, both critical.
    cy.get('[data-testid="lab-result-row"][data-analyte="LDH"]')
      .should('have.class', 'bg-critical-wash');
  });

  it('EC-16: the lab timeline renders in chronological order', () => {
    cy.visitLocale('/cases/THY-003', 'en');
    const seen: number[] = [];
    cy.get('[data-testid="lab-panel"]')
      .each(($panel) => {
        const match = $panel.text().match(/(?:Day|Presentation)\s*(\d+)?/);
        if (match?.[1]) seen.push(Number(match[1]));
      })
      .then(() => {
        const sorted = [...seen].sort((a, b) => a - b);
        expect(seen, 'panels are in chronological order').to.deep.equal(sorted);
      });
  });

  it('EC-17: the trend chart plots every numeric point for an analyte', () => {
    // THY-003's TSH series is the longitudinal exercise: six measurements.
    cy.visitLocale('/cases/THY-003', 'en');
    cy.get('[data-testid="lab-trend-chart"][data-analyte="TSH"]')
      .find('circle')
      .should('have.length.at.least', 6);
  });

  it('EC-18: the chart shades the reference interval', () => {
    cy.visitLocale('/cases/THY-003', 'en');
    cy.get('[data-testid="lab-trend-chart"][data-analyte="TSH"]')
      .find('[data-testid="reference-band"]')
      .should('exist')
      .and(($band) => {
        // A band of zero height is a silent failure - the element exists but
        // conveys nothing.
        expect(Number($band.attr('height')), 'reference band has height').to.be.greaterThan(0);
      });
  });

  it('EC-19: qualitative results are excluded from the chart but present in the table', () => {
    // A direct antiglobulin test reported as "Positive 4+" has no place on a
    // numeric axis, but must not vanish from the record.
    cy.visitLocale('/cases/HEM-001', 'en');
    cy.get('[data-testid="lab-trend-chart"][data-analyte="DAT_POLY"]').should('not.exist');
    cy.get('[data-testid="lab-result-row"][data-analyte="DAT_POLY"]').should('contain', 'Positive');
  });

  it('EC-20: every chart ships an equivalent data table', () => {
    cy.visitLocale('/cases/THY-003', 'en');
    cy.get('[data-testid="lab-trend-chart"]')
      .first()
      .within(() => {
        cy.get('[data-testid="table-view-toggle"]').click();
        cy.get('table').should('be.visible');
        cy.get('[data-testid="chart-svg"]').should('not.exist');
        cy.get('[data-testid="chart-view-toggle"]').click();
        cy.get('[data-testid="chart-svg"]').should('be.visible');
      });
  });

  it('EC-21: the chart exposes an accessible text summary', () => {
    cy.visitLocale('/cases/THY-003', 'en');
    cy.get('[data-testid="lab-trend-chart"][data-analyte="TSH"]')
      .find('desc')
      .invoke('text')
      .should('match', /measured \d+ times/)
      .and('contain', 'Reference range');
  });

  it('EC-22: the peripheral smear report renders its morphology and narrative', () => {
    cy.visitLocale('/cases/HEM-003', 'en');
    cy.get('[data-testid="smear-report"]').should('exist');
    // The oxidative-injury findings are the diagnostic content of this case.
    cy.get('[data-testid="smear-report"]').should('contain', 'bite cells');
    cy.get('[data-testid="smear-report"]').should('contain', 'Heinz bodies');
  });

  it('EC-23: drug resistance is shown by symbol and text, not colour alone', () => {
    cy.visitLocale('/cases/LEP-002', 'en');
    cy.get('[data-testid="susceptibility-list"]').should('exist');
    cy.get('[data-resistant="true"]')
      .first()
      .should('contain', '✕')
      .and('contain', 'Resistant');
    cy.get('[data-resistant="false"]').first().should('contain', '✓');
  });

  it('EC-24: the diagnosis is hidden until deliberately revealed', () => {
    // This is a teaching corpus; the answer must not be absorbed while
    // scrolling past it.
    cy.visitLocale('/cases/HEM-005', 'en');
    cy.get('[data-testid="primary-diagnosis"]').should('not.exist');
    cy.get('[data-testid="reveal-diagnosis"]').click();
    cy.get('[data-testid="primary-diagnosis"]').should('be.visible');
    cy.get('[data-testid="differential-diagnosis"]').should('have.length.at.least', 2);
  });

  it('EC-25: a section that fails to render is isolated by its error boundary', () => {
    // Corrupt only the trends endpoint. The rest of the case must survive,
    // because partial information beats a blank page on a clinical screen.
    cy.intercept('GET', '**/api/v1/cases/*/trends*', {
      statusCode: 500,
      body: { title: 'Injected', status: 500, detail: 'boom', type: '', instance: null, errors: [], request_id: 'x' },
    }).as('brokenTrends');

    cy.visitLocale('/cases/THY-001', 'en');
    cy.wait('@brokenTrends');

    cy.get('[data-testid="error-state"]').should('exist');
    // Everything else still renders.
    cy.get('[data-testid="lab-panel"]').should('exist');
    cy.get('[data-testid="patient-panel"]').should('exist');
    cy.get('[data-testid="teaching-point"]').should('exist');
  });
});
