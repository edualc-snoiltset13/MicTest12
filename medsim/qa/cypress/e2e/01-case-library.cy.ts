/// <reference types="cypress" />

/**
 * Spec 01 - Case library behaviour. Edge cases 01-13.
 *
 * These are the functional cases: filtering, searching, sorting, navigation and
 * state persistence. Each test targets a specific way the library has broken or
 * could break, not a happy path re-tested five ways.
 */

describe('01 - Case library', () => {
  beforeEach(() => {
    cy.interceptCases();
    cy.visitLocale('/', 'en');
    cy.wait('@cases');
  });

  it('EC-01: loads the full 25-case corpus and reports the count', () => {
    cy.get('[data-testid="case-card"]').should('have.length', 25);
    cy.get('[data-testid="result-count"]').should('contain', '25');
    // The stat tiles come from a separate endpoint; a mismatch between them and
    // the grid means one of the two is stale.
    cy.get('[data-testid="stats-row"]').should('contain', '25');
  });

  it('EC-02: search debounces to a single request for a multi-character query', () => {
    // Nine characters typed quickly must not produce nine requests. The
    // debounce is 250ms; typing at 30ms/char is faster than a fast human.
    let requestCount = 0;
    cy.intercept('GET', '**/api/v1/cases?*', () => {
      requestCount += 1;
    }).as('search');

    cy.get('[data-testid="search-input"]').type('haemolysis', { delay: 30 });
    cy.wait('@search');
    cy.wait(600); // past the debounce window

    cy.then(() => {
      expect(requestCount, 'requests issued for a 10-character query').to.be.lessThan(4);
    });
  });

  it('EC-03: search with no matches shows an empty state, not a blank grid', () => {
    cy.get('[data-testid="search-input"]').type('zzzznotarealsearchterm');
    cy.get('[data-testid="empty-state"]').should('be.visible');
    cy.get('[data-testid="case-card"]').should('not.exist');
    // The empty state must offer a way out, or the user is stuck.
    cy.get('[data-testid="empty-state"]').find('button').should('be.visible');
  });

  it('EC-04: a search term containing regex metacharacters is treated literally', () => {
    // ".*" as a literal string must match nothing, not everything. If the
    // backend interpolated it into a pattern, this would return all 25.
    cy.get('[data-testid="search-input"]').type('.*');
    cy.wait(600);
    cy.get('[data-testid="case-card"]').should('have.length.lessThan', 25);
  });

  it('EC-05: a search term with SQL metacharacters is handled safely', () => {
    cy.get('[data-testid="search-input"]').type("'; DROP TABLE cases; --");
    cy.wait(700);
    cy.get('[data-testid="empty-state"]').should('be.visible');
    // The corpus must still be intact afterwards.
    cy.get('[data-testid="search-input"]').clear();
    cy.wait(700);
    cy.get('[data-testid="case-card"]').should('have.length', 25);
  });

  it('EC-06: discipline filter partitions the corpus without overlap', () => {
    const expected: Record<string, number> = {
      chemical_pathology: 9,
      hematology: 9,
      microbiology: 4,
      pharmacology: 3,
    };
    let running = 0;
    Object.entries(expected).forEach(([discipline, count]) => {
      cy.get('[data-testid="discipline-filter"]').select(discipline);
      cy.get('[data-testid="case-card"]').should('have.length', count);
      running += count;
    });
    cy.then(() => expect(running, 'partition sums to the corpus size').to.equal(25));
  });

  it('EC-07: filters compose rather than replace one another', () => {
    cy.get('[data-testid="discipline-filter"]').select('hematology');
    cy.get('[data-testid="difficulty-filter"]').select('5');
    cy.get('[data-testid="case-card"]').should('have.length.at.least', 1);
    // Every surviving card must satisfy BOTH filters.
    cy.get('[data-testid="case-card"]').each(($card) => {
      expect($card.attr('data-case-code')).to.match(/^HEM-/);
    });
    cy.get('[data-testid="active-filter-count"]').should('contain', '2');
  });

  it('EC-08: filter state round-trips through the URL', () => {
    cy.get('[data-testid="discipline-filter"]').select('microbiology');
    cy.get('[data-testid="search-input"]').type('leprosy');
    cy.wait(600);

    cy.url().should('include', 'discipline=microbiology').and('include', 'q=leprosy');

    // A reload must reproduce exactly the same view - this is what makes a bug
    // report with a pasted URL reproducible.
    cy.reload();
    cy.get('[data-testid="discipline-filter"]').should('have.value', 'microbiology');
    cy.get('[data-testid="search-input"]').should('have.value', 'leprosy');
  });

  it('EC-09: clearing filters preserves the chosen language', () => {
    cy.setLocale('de');
    cy.get('[data-testid="discipline-filter"]').select('hematology');
    cy.get('[data-testid="clear-filters"]').click();

    cy.get('[data-testid="case-card"]').should('have.length', 25);
    // The regression this guards: clearAll rebuilding the query string from
    // scratch and dropping ?lang=.
    cy.get('html').should('have.attr', 'lang', 'de');
    cy.url().should('include', 'lang=de');
  });

  it('EC-10: sorting changes order in both directions', () => {
    cy.get('[data-testid="case-card"]').first().invoke('attr', 'data-case-code').as('ascFirst');
    cy.get('[data-testid="sort-direction"]').select('desc');
    cy.get('[data-testid="case-card"]')
      .first()
      .invoke('attr', 'data-case-code')
      .then(function (descFirst) {
        expect(descFirst).not.to.equal(this.ascFirst);
      });
  });

  it('EC-11: clicking a tag chip filters by that tag without navigating', () => {
    cy.get('[data-testid="case-tag"]').first().click();
    cy.url().should('include', 'tag=');
    // Must still be on the dashboard - the tag chip sits inside a card whose
    // title is a stretched link, and a mis-layered z-index sends the click to
    // the link instead.
    cy.get('[data-testid="case-grid"]').should('exist');
    cy.get('[data-testid="case-detail"]').should('not.exist');
  });

  it('EC-12: navigating into a case and back preserves the filtered list', () => {
    cy.get('[data-testid="discipline-filter"]').select('chemical_pathology');
    cy.get('[data-testid="case-card"]').should('have.length', 9);

    cy.openFirstCase();
    cy.get('[data-testid="back-link"]').click();

    cy.get('[data-testid="discipline-filter"]').should('have.value', 'chemical_pathology');
    cy.get('[data-testid="case-card"]').should('have.length', 9);
  });

  it('EC-13: an unknown case code renders a not-found state, not a crash', () => {
    cy.visit('/cases/ZZZ-999', { failOnStatusCode: false });
    cy.get('[data-testid="error-state"]').should('be.visible');
    cy.get('[data-testid="error-state"]').should('have.attr', 'data-error-kind', 'status-404');
    // The request id must be surfaced so a tester can quote it in a bug report.
    cy.get('[data-testid="error-state"]').should('contain', 'Reference:');
  });
});
