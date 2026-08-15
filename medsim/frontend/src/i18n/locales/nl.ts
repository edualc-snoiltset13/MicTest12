/**
 * Dutch message catalogue.
 *
 * Notes for reviewers:
 *  - Netherlands Dutch (nl-NL) medical register. "Perifeer bloeduitstrijkje",
 *    "Referentiewaarden" and "Behandelschema" are the terms used in Dutch
 *    laboratory and clinical reports.
 *  - Dutch CLDR uses one/other, like English.
 *  - Dutch forms long compounds ("Thyreoidstimulerend hormoon",
 *    "Antimicrobiële chemotherapie") and is the second layout-stress locale
 *    after German.
 */

import type { Messages } from '../types';

export const nl: Messages = {
  app: {
    name: 'MedSimQA',
    tagline: 'Simulatie van klinisch redeneren en kwaliteitsborging',
    skipToContent: 'Naar hoofdinhoud springen',
    syntheticBanner:
      'Alle patiënten in dit corpus zijn synthetisch. Niets hiervan is een echt patiëntendossier of medisch advies.',
  },

  nav: {
    dashboard: 'Overzicht',
    cases: 'Casussen',
    reference: 'Referentiewaarden',
    about: 'Over',
    backToCases: 'Terug naar alle casussen',
  },

  actions: {
    search: 'Zoeken',
    filter: 'Filteren',
    clear: 'Wissen',
    clearAll: 'Alle filters wissen',
    retry: 'Opnieuw proberen',
    reload: 'Opnieuw laden',
    close: 'Sluiten',
    expand: 'Meer tonen',
    collapse: 'Minder tonen',
    copy: 'Kopiëren',
    copied: 'Gekopieerd',
    download: 'Downloaden',
    print: 'Afdrukken',
    viewChart: 'Grafiek',
    viewTable: 'Tabel',
    previous: 'Vorige',
    next: 'Volgende',
  },

  theme: {
    label: 'Thema',
    light: 'Licht',
    dark: 'Donker',
    system: 'Systeem',
    toggle: 'Overschakelen naar {mode} thema',
  },

  language: {
    label: 'Taal',
    change: 'Taal wijzigen',
    current: 'Huidige taal: {language}',
    decimalNotice: 'Decimaalteken in deze taal: {separator}',
  },

  dashboard: {
    title: 'Casusbibliotheek',
    subtitle: 'Synthetische casussen voor de beoordeling van klinisch redeneren',
    resultCount: {
      one: '{count} casus',
      other: '{count} casussen',
    },
    resultCountFiltered: {
      one: '{count} van {total} casus',
      other: '{count} van {total} casussen',
    },
    noResults: 'Geen casussen komen overeen met deze filters',
    noResultsHint: 'Probeer een filter te verwijderen of uw zoekopdracht te verbreden.',
    loading: 'Casussen laden',
    stats: {
      totalCases: 'Casussen',
      totalPanels: 'Laboratoriumpanels',
      totalResults: 'Laboratoriumuitslagen',
      disciplines: 'Vakgebieden',
    },
  },

  filters: {
    title: 'Filters',
    searchPlaceholder: 'Casussen, codes, bevindingen zoeken…',
    searchLabel: 'Casussen doorzoeken',
    discipline: 'Vakgebied',
    subspecialty: 'Aandachtsgebied',
    difficulty: 'Moeilijkheidsgraad',
    status: 'Status',
    tag: 'Label',
    sortBy: 'Sorteren op',
    sortDirection: 'Sorteervolgorde',
    ascending: 'Oplopend',
    descending: 'Aflopend',
    all: 'Alle',
    activeCount: {
      one: '{count} filter actief',
      other: '{count} filters actief',
    },
  },

  discipline: {
    chemical_pathology: 'Klinische chemie',
    microbiology: 'Microbiologie',
    hematology: 'Hematologie',
    pharmacology: 'Farmacologie',
  },

  subspecialty: {
    thyroid: 'Schildklier',
    haemolytic_anaemia: 'Hemolytische anemie',
    mycobacteriology: 'Mycobacteriologie',
    antimicrobial_chemotherapy: 'Antimicrobiële chemotherapie',
  },

  caseStatus: {
    draft: 'Concept',
    in_review: 'In beoordeling',
    published: 'Gepubliceerd',
    retired: 'Ingetrokken',
  },

  difficulty: {
    label: 'Moeilijkheidsgraad',
    level: 'Niveau {level} van 5',
    1: 'Basis',
    2: 'Eenvoudig',
    3: 'Gemiddeld',
    4: 'Gevorderd',
    5: 'Expert',
  },

  sort: {
    case_code: 'Casuscode',
    title: 'Titel',
    difficulty: 'Moeilijkheidsgraad',
    updated_at: 'Laatst bijgewerkt',
    created_at: 'Aangemaakt',
    discipline: 'Vakgebied',
  },

  case: {
    code: 'Casuscode',
    version: 'Versie {version}',
    updated: 'Bijgewerkt op {date}',
    author: 'Auteur',
    reviewedBy: 'Beoordeeld door',
    tags: 'Labels',
    codes: 'Classificatiecodes',
    sections: {
      overview: 'Overzicht',
      patient: 'Patiënt',
      presentation: 'Presentatie',
      labs: 'Laboratoriumuitslagen',
      trends: 'Beloop in de tijd',
      smear: 'Perifeer bloeduitstrijkje',
      microbiology: 'Microbiologie',
      imaging: 'Beeldvorming',
      protocol: 'Behandelschema',
      diagnosis: 'Diagnose',
      teaching: 'Leerpunten',
      references: 'Literatuur',
    },
  },

  patient: {
    title: 'Patiënt',
    age: 'Leeftijd',
    ageValue: '{age} jaar',
    sex: 'Geslacht',
    weight: 'Gewicht',
    height: 'Lengte',
    bmi: 'BMI',
    ancestry: 'Herkomst',
    pregnancy: 'Zwangerschapsstatus',
    occupation: 'Beroep',
    region: 'Regio',
    pseudonym: 'Identificatie',
  },

  sex: {
    female: 'Vrouw',
    male: 'Man',
    intersex: 'Intersekse',
    unspecified: 'Niet gespecificeerd',
  },

  presentation: {
    chiefComplaint: 'Hoofdklacht',
    history: 'Huidige ziektegeschiedenis',
    pastMedical: 'Voorgeschiedenis',
    medications: 'Medicatie',
    allergies: 'Allergieën',
    familyHistory: 'Familieanamnese',
    socialHistory: 'Sociale anamnese',
    reviewOfSystems: 'Tractusanamnese',
    vitals: 'Vitale functies',
    examination: 'Lichamelijk onderzoek',
    none: 'Niet vastgelegd',
    medication: {
      name: 'Geneesmiddel',
      dose: 'Dosis',
      route: 'Toedieningsweg',
      frequency: 'Frequentie',
      indication: 'Indicatie',
      notes: 'Opmerkingen',
    },
  },

  vitals: {
    heart_rate_bpm: 'Hartfrequentie',
    blood_pressure_mmhg: 'Bloeddruk',
    respiratory_rate: 'Ademfrequentie',
    temperature_c: 'Temperatuur',
    spo2_percent: 'Zuurstofsaturatie',
    weight_kg: 'Gewicht',
    map_mmhg: 'Gemiddelde arteriële druk',
    urine_output_ml_h: 'Urineproductie',
    rhythm: 'Ritme',
    gcs: 'Glasgow Coma Scale',
  },

  labs: {
    title: 'Laboratoriumuitslagen',
    panel: 'Panel',
    analyte: 'Analyt',
    value: 'Waarde',
    unit: 'Eenheid',
    referenceRange: 'Referentiewaarden',
    flag: 'Markering',
    method: 'Methode',
    specimen: 'Materiaal',
    laboratory: 'Laboratorium',
    analyser: 'Analyseapparaat',
    collected: 'Afgenomen',
    day: 'Dag {day}',
    dayZero: 'Presentatie',
    note: 'Interpretatieve opmerking',
    criticalResult: 'Kritieke uitslag',
    criticalWarning: 'Deze uitslag ligt buiten de kritieke actiegrens.',
    noResults: 'Voor deze casus zijn geen laboratoriumuitslagen vastgelegd.',
    panelCount: {
      one: '{count} panel',
      other: '{count} panels',
    },
    resultCount: {
      one: '{count} uitslag',
      other: '{count} uitslagen',
    },
  },

  flag: {
    N: 'Normaal',
    H: 'Verhoogd',
    L: 'Verlaagd',
    HH: 'Kritiek verhoogd',
    LL: 'Kritiek verlaagd',
    A: 'Afwijkend',
    // HL7-afkortingen zijn internationaal en worden niet vertaald.
    short: { N: 'N', H: 'H', L: 'L', HH: 'HH', LL: 'LL', A: 'A' },
  },

  chart: {
    title: 'Beloop in de tijd',
    subtitle: 'Waarden uitgezet tegen dagen sinds presentatie',
    selectAnalyte: 'Analyt selecteren',
    compare: 'Analyten vergelijken',
    compareLimit: 'Er kunnen maximaal drie analyten tegelijk worden vergeleken.',
    axisX: 'Dagen sinds presentatie',
    axisY: 'Waarde ({unit})',
    referenceBand: 'Referentiewaarden',
    referenceBandDescription: 'Het gearceerde gebied toont het referentie-interval {low} tot {high} {unit}.',
    noData: 'Geen numerieke uitslagen beschikbaar om weer te geven.',
    notEnoughPoints: 'Een beloop vereist ten minste twee metingen.',
    singlePoint: 'Er is slechts één meting beschikbaar, weergegeven als punt.',
    latest: 'Laatste',
    change: 'Verandering',
    changeFrom: 'ten opzichte van {value} op dag {day}',
    increased: 'gestegen',
    decreased: 'gedaald',
    unchanged: 'ongewijzigd',
    tableCaption: 'Gegevenstabel bij de beloopgrafiek van {analyte}',
    tableView: 'Gegevenstabel',
    chartView: 'Grafiek',
    accessibleSummary:
      '{analyte} is {count} keer gemeten tussen dag {firstDay} en dag {lastDay}. Eerste waarde {first} {unit}, laatste waarde {last} {unit}. Referentie-interval {low} tot {high} {unit}.',
    pointDescription: 'Dag {day}: {value} {unit}, {flag}',
  },

  smear: {
    title: 'Perifeer bloeduitstrijkje',
    stain: 'Kleuring',
    reportedBy: 'Beoordeeld door',
    redCells: 'Erytrocytenmorfologie',
    whiteCells: 'Leukocytenmorfologie',
    platelets: 'Trombocytenmorfologie',
    narrative: 'Verslag',
    schistocytes: 'Schistocyten',
    schistocyteValue: '{value}% van de erytrocyten',
    schistocyteThreshold: 'De ICSH-drempel voor betekenis bij volwassenen ligt boven 1%.',
    none: 'Voor deze casus is geen uitstrijkje vastgelegd.',
  },

  microbiology: {
    title: 'Microbiologie',
    specimen: 'Materiaal',
    site: 'Locatie',
    organism: 'Verwekker',
    microscopy: 'Microscopie',
    bacterialIndex: 'Bacteriële index',
    morphologicalIndex: 'Morfologische index',
    bacterialIndexHelp:
      'Logaritmische Ridley-schaal, 0 tot 6+. Daalt bij effectieve therapie met ongeveer 1 log per jaar.',
    morphologicalIndexHelp:
      'Percentage solide kleurende, levensvatbare bacillen. Moet bij effectieve therapie tot nul dalen.',
    molecular: 'Moleculaire bevindingen',
    target: 'Doelwit',
    method: 'Methode',
    result: 'Resultaat',
    interpretation: 'Interpretatie',
    susceptibility: 'Gevoeligheidsbepaling',
    agent: 'Middel',
    susceptible: 'Gevoelig',
    resistant: 'Resistent',
    none: 'Voor deze casus is geen microbiologie vastgelegd.',
  },

  protocol: {
    title: 'Behandelschema',
    guideline: 'Richtlijnbron',
    indication: 'Indicatie',
    duration: 'Duur',
    durationMonths: {
      one: '{count} maand',
      other: '{count} maanden',
    },
    durationIndefinite: 'Doorlopend',
    regimen: 'Schema',
    agent: 'Middel',
    dose: 'Dosis',
    route: 'Toedieningsweg',
    frequency: 'Frequentie',
    monitoring: 'Controle',
    contraindications: 'Contra-indicaties',
    adverseEffects: 'Bijwerkingen',
    notes: 'Opmerkingen',
    none: 'Voor deze casus is geen behandelschema vastgelegd.',
  },

  diagnosis: {
    title: 'Diagnose',
    primary: 'Hoofddiagnose',
    differential: 'Differentiaaldiagnose',
    certainty: 'Zekerheid',
    likelihood: 'Waarschijnlijkheid',
    discriminator: 'Onderscheidend kenmerk',
    supporting: 'Ondersteunende bevindingen',
    refuting: 'Tegenargumenten',
    icd10: 'ICD-10',
    none: 'Voor deze casus is geen diagnose vastgelegd.',
  },

  certainty: {
    confirmed: 'Bevestigd',
    probable: 'Waarschijnlijk',
    possible: 'Mogelijk',
    excluded: 'Uitgesloten',
  },

  imaging: {
    title: 'Beeldvorming',
    modality: 'Modaliteit',
    region: 'Regio',
    findings: 'Bevindingen',
    impression: 'Conclusie',
    none: 'Voor deze casus is geen beeldvorming vastgelegd.',
  },

  teaching: {
    title: 'Leerpunten',
    pointCount: {
      one: '{count} leerpunt',
      other: '{count} leerpunten',
    },
  },

  references: {
    title: 'Literatuur',
    type: {
      guideline: 'Richtlijn',
      review: 'Overzichtsartikel',
      primary: 'Origineel onderzoek',
      trial: 'Klinische studie',
      cohort: 'Cohortonderzoek',
      consensus: 'Consensusdocument',
      surveillance: 'Surveillancegegevens',
      regulatory: 'Regelgevende mededeling',
    },
  },

  errors: {
    title: 'Er is iets misgegaan',
    generic: 'Het verzoek kon niet worden voltooid.',
    network: 'De server is niet bereikbaar. Controleer uw verbinding en probeer het opnieuw.',
    timeout: 'De server reageerde te traag.',
    notFound: 'Die casus kon niet worden gevonden.',
    notFoundHint: 'De casus is mogelijk ingetrokken of de link is verouderd.',
    server: 'De server meldde een fout.',
    parse: 'De server gaf een antwoord terug dat niet gelezen kon worden.',
    parseHint:
      'Dit duidt meestal op een proxy of netwerkapparaat dat het antwoord heeft gewijzigd. Het onbewerkte antwoord is naar de console gelogd.',
    offline: 'U lijkt offline te zijn. De laatst geladen gegevens worden getoond.',
    requestId: 'Referentie: {id}',
    statusCode: 'Status {code}',
    boundary: 'Dit onderdeel kon niet worden weergegeven en is geïsoleerd zodat de rest van de pagina blijft werken.',
    detail: 'Technische details',
  },

  empty: {
    noData: 'Geen gegevens',
    notRecorded: 'Niet vastgelegd',
    none: 'Geen',
  },

  a11y: {
    loading: 'Laden',
    sortedBy: 'Gesorteerd op {field}, {direction}',
    selected: 'Geselecteerd',
    required: 'Verplicht',
    externalLink: 'Wordt geopend in een nieuw tabblad',
    chartDescription: 'Grafiek. Hieronder volgt een tabel met dezelfde waarden.',
    liveRegionUpdated: 'Resultaten bijgewerkt',
  },
};
