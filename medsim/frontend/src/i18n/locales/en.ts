/**
 * English message catalogue - the reference locale.
 *
 * This object's shape defines the `Messages` type, so every other locale is
 * checked against it at compile time. Adding a key here without adding it to
 * de/es/nl/ru is a type error, which is the mechanism that keeps the five
 * catalogues in step.
 *
 * Conventions for translators:
 *   - `{placeholder}` is interpolated; keep the name, translate around it.
 *   - Entries that are objects of `one`/`few`/`many`/`other` are plural forms
 *     selected by CLDR rules. Supply every category your language uses.
 *   - Clinical terms (analyte names, flags, diagnoses) are translated to the
 *     term a clinician in that language would actually use, not transliterated.
 *   - Units (mIU/L, pmol/L, g/L) are NOT translated. They are international.
 */

export const en = {
  app: {
    name: 'MedSimQA',
    tagline: 'Clinical reasoning simulation and QA',
    skipToContent: 'Skip to main content',
    syntheticBanner:
      'All patients in this corpus are synthetic. Nothing here is a real patient record or clinical advice.',
  },

  nav: {
    dashboard: 'Dashboard',
    cases: 'Case studies',
    reference: 'Reference intervals',
    about: 'About',
    backToCases: 'Back to all cases',
  },

  actions: {
    search: 'Search',
    filter: 'Filter',
    clear: 'Clear',
    clearAll: 'Clear all filters',
    retry: 'Try again',
    reload: 'Reload',
    close: 'Close',
    expand: 'Show more',
    collapse: 'Show less',
    copy: 'Copy',
    copied: 'Copied',
    download: 'Download',
    print: 'Print',
    viewChart: 'Chart',
    viewTable: 'Table',
    previous: 'Previous',
    next: 'Next',
  },

  theme: {
    label: 'Theme',
    light: 'Light',
    dark: 'Dark',
    system: 'System',
    toggle: 'Switch to {mode} theme',
  },

  language: {
    label: 'Language',
    change: 'Change language',
    current: 'Current language: {language}',
    decimalNotice: 'Decimal separator in this language: {separator}',
  },

  dashboard: {
    title: 'Case library',
    subtitle: 'Synthetic case studies for clinical reasoning assessment',
    resultCount: {
      one: '{count} case',
      other: '{count} cases',
    },
    resultCountFiltered: {
      one: '{count} of {total} case',
      other: '{count} of {total} cases',
    },
    noResults: 'No cases match these filters',
    noResultsHint: 'Try removing a filter or broadening your search.',
    loading: 'Loading cases',
    stats: {
      totalCases: 'Cases',
      totalPanels: 'Lab panels',
      totalResults: 'Lab results',
      disciplines: 'Disciplines',
    },
  },

  filters: {
    title: 'Filters',
    searchPlaceholder: 'Search cases, codes, findings…',
    searchLabel: 'Search case studies',
    discipline: 'Discipline',
    subspecialty: 'Subspecialty',
    difficulty: 'Difficulty',
    status: 'Status',
    tag: 'Tag',
    sortBy: 'Sort by',
    sortDirection: 'Sort direction',
    ascending: 'Ascending',
    descending: 'Descending',
    all: 'All',
    activeCount: {
      one: '{count} filter active',
      other: '{count} filters active',
    },
  },

  discipline: {
    chemical_pathology: 'Chemical pathology',
    microbiology: 'Microbiology',
    hematology: 'Haematology',
    pharmacology: 'Pharmacology',
  },

  subspecialty: {
    thyroid: 'Thyroid',
    haemolytic_anaemia: 'Haemolytic anaemia',
    mycobacteriology: 'Mycobacteriology',
    antimicrobial_chemotherapy: 'Antimicrobial chemotherapy',
  },

  caseStatus: {
    draft: 'Draft',
    in_review: 'In review',
    published: 'Published',
    retired: 'Retired',
  },

  difficulty: {
    label: 'Difficulty',
    level: 'Level {level} of 5',
    1: 'Foundational',
    2: 'Straightforward',
    3: 'Intermediate',
    4: 'Advanced',
    5: 'Expert',
  },

  sort: {
    case_code: 'Case code',
    title: 'Title',
    difficulty: 'Difficulty',
    updated_at: 'Last updated',
    created_at: 'Created',
    discipline: 'Discipline',
  },

  case: {
    code: 'Case code',
    version: 'Version {version}',
    updated: 'Updated {date}',
    author: 'Author',
    reviewedBy: 'Reviewed by',
    tags: 'Tags',
    codes: 'Classification codes',
    sections: {
      overview: 'Overview',
      patient: 'Patient',
      presentation: 'Presentation',
      labs: 'Laboratory results',
      trends: 'Trends over time',
      smear: 'Peripheral blood smear',
      microbiology: 'Microbiology',
      imaging: 'Imaging',
      protocol: 'Treatment protocol',
      diagnosis: 'Diagnosis',
      teaching: 'Teaching points',
      references: 'References',
    },
  },

  patient: {
    title: 'Patient',
    age: 'Age',
    ageValue: '{age} years',
    sex: 'Sex',
    weight: 'Weight',
    height: 'Height',
    bmi: 'BMI',
    ancestry: 'Ancestry',
    pregnancy: 'Pregnancy status',
    occupation: 'Occupation',
    region: 'Region',
    pseudonym: 'Identifier',
  },

  sex: {
    female: 'Female',
    male: 'Male',
    intersex: 'Intersex',
    unspecified: 'Not specified',
  },

  presentation: {
    chiefComplaint: 'Presenting complaint',
    history: 'History of presenting illness',
    pastMedical: 'Past medical history',
    medications: 'Medications',
    allergies: 'Allergies',
    familyHistory: 'Family history',
    socialHistory: 'Social history',
    reviewOfSystems: 'Review of systems',
    vitals: 'Observations',
    examination: 'Examination findings',
    none: 'None recorded',
    medication: {
      name: 'Drug',
      dose: 'Dose',
      route: 'Route',
      frequency: 'Frequency',
      indication: 'Indication',
      notes: 'Notes',
    },
  },

  vitals: {
    heart_rate_bpm: 'Heart rate',
    blood_pressure_mmhg: 'Blood pressure',
    respiratory_rate: 'Respiratory rate',
    temperature_c: 'Temperature',
    spo2_percent: 'Oxygen saturation',
    weight_kg: 'Weight',
    map_mmhg: 'Mean arterial pressure',
    urine_output_ml_h: 'Urine output',
    rhythm: 'Rhythm',
    gcs: 'Glasgow Coma Scale',
  },

  labs: {
    title: 'Laboratory results',
    panel: 'Panel',
    analyte: 'Analyte',
    value: 'Value',
    unit: 'Unit',
    referenceRange: 'Reference range',
    flag: 'Flag',
    method: 'Method',
    specimen: 'Specimen',
    laboratory: 'Laboratory',
    analyser: 'Analyser',
    collected: 'Collected',
    day: 'Day {day}',
    dayZero: 'Presentation',
    note: 'Interpretive note',
    criticalResult: 'Critical result',
    criticalWarning: 'This result is outside the critical action limit.',
    noResults: 'No laboratory results recorded for this case.',
    panelCount: {
      one: '{count} panel',
      other: '{count} panels',
    },
    resultCount: {
      one: '{count} result',
      other: '{count} results',
    },
  },

  flag: {
    N: 'Normal',
    H: 'High',
    L: 'Low',
    HH: 'Critically high',
    LL: 'Critically low',
    A: 'Abnormal',
    short: {
      N: 'N',
      H: 'H',
      L: 'L',
      HH: 'HH',
      LL: 'LL',
      A: 'A',
    },
  },

  chart: {
    title: 'Trend over time',
    subtitle: 'Values plotted against days from presentation',
    selectAnalyte: 'Select analyte',
    compare: 'Compare analytes',
    compareLimit: 'Up to three analytes can be compared at once.',
    axisX: 'Days from presentation',
    axisY: 'Value ({unit})',
    referenceBand: 'Reference range',
    referenceBandDescription: 'Shaded area shows the reference interval {low} to {high} {unit}.',
    noData: 'No numeric results available to plot.',
    notEnoughPoints: 'A trend needs at least two measurements.',
    singlePoint: 'Only one measurement is available, shown as a point.',
    latest: 'Latest',
    change: 'Change',
    changeFrom: 'from {value} on day {day}',
    increased: 'increased',
    decreased: 'decreased',
    unchanged: 'unchanged',
    tableCaption: 'Data table for the {analyte} trend chart',
    tableView: 'Data table',
    chartView: 'Chart',
    accessibleSummary:
      '{analyte} measured {count} times between day {firstDay} and day {lastDay}. First value {first} {unit}, last value {last} {unit}. Reference range {low} to {high} {unit}.',
    pointDescription: 'Day {day}: {value} {unit}, {flag}',
  },

  smear: {
    title: 'Peripheral blood smear',
    stain: 'Stain',
    reportedBy: 'Reported by',
    redCells: 'Red cell morphology',
    whiteCells: 'White cell morphology',
    platelets: 'Platelet morphology',
    narrative: 'Report',
    schistocytes: 'Schistocytes',
    schistocyteValue: '{value}% of red cells',
    schistocyteThreshold: 'ICSH threshold for significance in adults is above 1%.',
    none: 'No smear reported for this case.',
  },

  microbiology: {
    title: 'Microbiology',
    specimen: 'Specimen',
    site: 'Site',
    organism: 'Organism',
    microscopy: 'Microscopy',
    bacterialIndex: 'Bacterial index',
    morphologicalIndex: 'Morphological index',
    bacterialIndexHelp: 'Ridley logarithmic scale, 0 to 6+. Falls by roughly 1 log per year on effective therapy.',
    morphologicalIndexHelp: 'Percentage of solidly staining, viable bacilli. Should reach zero on effective therapy.',
    molecular: 'Molecular findings',
    target: 'Target',
    method: 'Method',
    result: 'Result',
    interpretation: 'Interpretation',
    susceptibility: 'Drug susceptibility',
    agent: 'Agent',
    susceptible: 'Susceptible',
    resistant: 'Resistant',
    none: 'No microbiology reported for this case.',
  },

  protocol: {
    title: 'Treatment protocol',
    guideline: 'Guideline source',
    indication: 'Indication',
    duration: 'Duration',
    durationMonths: {
      one: '{count} month',
      other: '{count} months',
    },
    durationIndefinite: 'Ongoing',
    regimen: 'Regimen',
    agent: 'Agent',
    dose: 'Dose',
    route: 'Route',
    frequency: 'Frequency',
    monitoring: 'Monitoring',
    contraindications: 'Contraindications',
    adverseEffects: 'Adverse effects',
    notes: 'Notes',
    none: 'No treatment protocol recorded for this case.',
  },

  diagnosis: {
    title: 'Diagnosis',
    primary: 'Primary diagnosis',
    differential: 'Differential diagnosis',
    certainty: 'Certainty',
    likelihood: 'Likelihood',
    discriminator: 'Discriminating feature',
    supporting: 'Supporting evidence',
    refuting: 'Evidence against',
    icd10: 'ICD-10',
    none: 'No diagnosis recorded for this case.',
  },

  certainty: {
    confirmed: 'Confirmed',
    probable: 'Probable',
    possible: 'Possible',
    excluded: 'Excluded',
  },

  imaging: {
    title: 'Imaging',
    modality: 'Modality',
    region: 'Region',
    findings: 'Findings',
    impression: 'Impression',
    none: 'No imaging recorded for this case.',
  },

  teaching: {
    title: 'Teaching points',
    pointCount: {
      one: '{count} teaching point',
      other: '{count} teaching points',
    },
  },

  references: {
    title: 'References',
    type: {
      guideline: 'Guideline',
      review: 'Review',
      primary: 'Primary research',
      trial: 'Clinical trial',
      cohort: 'Cohort study',
      consensus: 'Consensus statement',
      surveillance: 'Surveillance data',
      regulatory: 'Regulatory notice',
    },
  },

  errors: {
    title: 'Something went wrong',
    generic: 'The dashboard could not complete that request.',
    network: 'Could not reach the server. Check your connection and try again.',
    timeout: 'The server took too long to respond.',
    notFound: 'That case could not be found.',
    notFoundHint: 'It may have been retired, or the link may be out of date.',
    server: 'The server reported an error.',
    parse: 'The server returned a response the dashboard could not read.',
    parseHint:
      'This usually means a proxy or network appliance altered the response. The raw response has been logged to the console.',
    offline: 'You appear to be offline. Showing the last data loaded.',
    requestId: 'Reference: {id}',
    statusCode: 'Status {code}',
    boundary: 'This section failed to render and has been isolated so the rest of the page still works.',
    detail: 'Technical detail',
  },

  empty: {
    noData: 'No data',
    notRecorded: 'Not recorded',
    none: 'None',
  },

  a11y: {
    loading: 'Loading',
    sortedBy: 'Sorted by {field}, {direction}',
    selected: 'Selected',
    required: 'Required',
    externalLink: 'Opens in a new tab',
    chartDescription: 'Chart. A data table with the same values follows.',
    liveRegionUpdated: 'Results updated',
  },
} as const;
