/**
 * German message catalogue.
 *
 * Notes for reviewers:
 *  - German is the layout-stress locale for this dashboard. Compounds such as
 *    "Thyreoidea-stimulierendes Hormon" and "Antimikrobielle Chemotherapie"
 *    are 30-40% longer than their English source, and the Cypress layout suite
 *    asserts that no component clips or overflows at these lengths.
 *  - Clinical terms use the German medical convention, not a transliteration:
 *    "Blutausstrich" not "Peripherer Schmier", "Referenzbereich" not
 *    "Referenz-Reichweite".
 *  - Decimal separator is a comma; that is handled by Intl, not by the strings.
 */

import type { Messages } from '../types';

export const de: Messages = {
  app: {
    name: 'MedSimQA',
    tagline: 'Simulation klinischer Entscheidungsfindung und Qualitätssicherung',
    skipToContent: 'Zum Hauptinhalt springen',
    syntheticBanner:
      'Alle Patientinnen und Patienten in diesem Korpus sind synthetisch. Nichts hiervon ist eine echte Patientenakte oder eine medizinische Empfehlung.',
  },

  nav: {
    dashboard: 'Übersicht',
    cases: 'Fallstudien',
    reference: 'Referenzbereiche',
    about: 'Über',
    backToCases: 'Zurück zu allen Fällen',
  },

  actions: {
    search: 'Suchen',
    filter: 'Filtern',
    clear: 'Zurücksetzen',
    clearAll: 'Alle Filter zurücksetzen',
    retry: 'Erneut versuchen',
    reload: 'Neu laden',
    close: 'Schliessen',
    expand: 'Mehr anzeigen',
    collapse: 'Weniger anzeigen',
    copy: 'Kopieren',
    copied: 'Kopiert',
    download: 'Herunterladen',
    print: 'Drucken',
    viewChart: 'Diagramm',
    viewTable: 'Tabelle',
    previous: 'Zurück',
    next: 'Weiter',
  },

  theme: {
    label: 'Design',
    light: 'Hell',
    dark: 'Dunkel',
    system: 'System',
    toggle: 'Zu {mode} Design wechseln',
  },

  language: {
    label: 'Sprache',
    change: 'Sprache ändern',
    current: 'Aktuelle Sprache: {language}',
    decimalNotice: 'Dezimaltrennzeichen in dieser Sprache: {separator}',
  },

  dashboard: {
    title: 'Fallsammlung',
    subtitle: 'Synthetische Fallstudien zur Beurteilung klinischer Entscheidungsfindung',
    resultCount: {
      one: '{count} Fall',
      other: '{count} Fälle',
    },
    resultCountFiltered: {
      one: '{count} von {total} Fall',
      other: '{count} von {total} Fällen',
    },
    noResults: 'Keine Fälle entsprechen diesen Filtern',
    noResultsHint: 'Entfernen Sie einen Filter oder erweitern Sie Ihre Suche.',
    loading: 'Fälle werden geladen',
    stats: {
      totalCases: 'Fälle',
      totalPanels: 'Laborprofile',
      totalResults: 'Laborwerte',
      disciplines: 'Fachgebiete',
    },
  },

  filters: {
    title: 'Filter',
    searchPlaceholder: 'Fälle, Codes, Befunde durchsuchen…',
    searchLabel: 'Fallstudien durchsuchen',
    discipline: 'Fachgebiet',
    subspecialty: 'Schwerpunkt',
    difficulty: 'Schwierigkeitsgrad',
    status: 'Status',
    tag: 'Schlagwort',
    sortBy: 'Sortieren nach',
    sortDirection: 'Sortierreihenfolge',
    ascending: 'Aufsteigend',
    descending: 'Absteigend',
    all: 'Alle',
    activeCount: {
      one: '{count} Filter aktiv',
      other: '{count} Filter aktiv',
    },
  },

  discipline: {
    chemical_pathology: 'Klinische Chemie',
    microbiology: 'Mikrobiologie',
    hematology: 'Hämatologie',
    pharmacology: 'Pharmakologie',
  },

  subspecialty: {
    thyroid: 'Schilddrüse',
    haemolytic_anaemia: 'Hämolytische Anämie',
    mycobacteriology: 'Mykobakteriologie',
    antimicrobial_chemotherapy: 'Antimikrobielle Chemotherapie',
  },

  caseStatus: {
    draft: 'Entwurf',
    in_review: 'In Prüfung',
    published: 'Veröffentlicht',
    retired: 'Zurückgezogen',
  },

  difficulty: {
    label: 'Schwierigkeitsgrad',
    level: 'Stufe {level} von 5',
    1: 'Grundlagen',
    2: 'Unkompliziert',
    3: 'Mittel',
    4: 'Fortgeschritten',
    5: 'Experte',
  },

  sort: {
    case_code: 'Fallnummer',
    title: 'Titel',
    difficulty: 'Schwierigkeitsgrad',
    updated_at: 'Zuletzt aktualisiert',
    created_at: 'Erstellt',
    discipline: 'Fachgebiet',
  },

  case: {
    code: 'Fallnummer',
    version: 'Version {version}',
    updated: 'Aktualisiert am {date}',
    author: 'Verfasst von',
    reviewedBy: 'Geprüft von',
    tags: 'Schlagwörter',
    codes: 'Klassifikationscodes',
    sections: {
      overview: 'Überblick',
      patient: 'Patient',
      presentation: 'Vorstellung',
      labs: 'Laborwerte',
      trends: 'Verlauf',
      smear: 'Blutausstrich',
      microbiology: 'Mikrobiologie',
      imaging: 'Bildgebung',
      protocol: 'Therapieschema',
      diagnosis: 'Diagnose',
      teaching: 'Lernpunkte',
      references: 'Literatur',
    },
  },

  patient: {
    title: 'Patient',
    age: 'Alter',
    ageValue: '{age} Jahre',
    sex: 'Geschlecht',
    weight: 'Gewicht',
    height: 'Grösse',
    bmi: 'BMI',
    ancestry: 'Herkunft',
    pregnancy: 'Schwangerschaftsstatus',
    occupation: 'Beruf',
    region: 'Region',
    pseudonym: 'Kennung',
  },

  sex: {
    female: 'Weiblich',
    male: 'Männlich',
    intersex: 'Intergeschlechtlich',
    unspecified: 'Nicht angegeben',
  },

  presentation: {
    chiefComplaint: 'Hauptbeschwerde',
    history: 'Aktuelle Anamnese',
    pastMedical: 'Vorerkrankungen',
    medications: 'Medikation',
    allergies: 'Allergien',
    familyHistory: 'Familienanamnese',
    socialHistory: 'Sozialanamnese',
    reviewOfSystems: 'Systemanamnese',
    vitals: 'Vitalparameter',
    examination: 'Untersuchungsbefunde',
    none: 'Nicht dokumentiert',
    medication: {
      name: 'Wirkstoff',
      dose: 'Dosis',
      route: 'Applikationsweg',
      frequency: 'Häufigkeit',
      indication: 'Indikation',
      notes: 'Hinweise',
    },
  },

  vitals: {
    heart_rate_bpm: 'Herzfrequenz',
    blood_pressure_mmhg: 'Blutdruck',
    respiratory_rate: 'Atemfrequenz',
    temperature_c: 'Temperatur',
    spo2_percent: 'Sauerstoffsättigung',
    weight_kg: 'Gewicht',
    map_mmhg: 'Mittlerer arterieller Druck',
    urine_output_ml_h: 'Urinausscheidung',
    rhythm: 'Rhythmus',
    gcs: 'Glasgow-Koma-Skala',
  },

  labs: {
    title: 'Laborwerte',
    panel: 'Profil',
    analyte: 'Analyt',
    value: 'Wert',
    unit: 'Einheit',
    referenceRange: 'Referenzbereich',
    flag: 'Bewertung',
    method: 'Methode',
    specimen: 'Probenmaterial',
    laboratory: 'Labor',
    analyser: 'Analysegerät',
    collected: 'Entnommen',
    day: 'Tag {day}',
    dayZero: 'Vorstellung',
    note: 'Interpretationshinweis',
    criticalResult: 'Kritischer Wert',
    criticalWarning: 'Dieser Wert liegt ausserhalb der kritischen Interventionsgrenze.',
    noResults: 'Für diesen Fall sind keine Laborwerte dokumentiert.',
    panelCount: {
      one: '{count} Profil',
      other: '{count} Profile',
    },
    resultCount: {
      one: '{count} Wert',
      other: '{count} Werte',
    },
  },

  flag: {
    N: 'Normal',
    H: 'Erhöht',
    L: 'Erniedrigt',
    HH: 'Kritisch erhöht',
    LL: 'Kritisch erniedrigt',
    A: 'Auffällig',
    // The short codes are HL7 abbreviations and are deliberately NOT
    // translated. Localising them to "N" for niedrig would collide with "N"
    // for normal, which is a patient-safety problem, not a style choice.
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
    title: 'Zeitlicher Verlauf',
    subtitle: 'Werte aufgetragen gegen Tage seit Vorstellung',
    selectAnalyte: 'Analyt auswählen',
    compare: 'Analyten vergleichen',
    compareLimit: 'Es können bis zu drei Analyten gleichzeitig verglichen werden.',
    axisX: 'Tage seit Vorstellung',
    axisY: 'Wert ({unit})',
    referenceBand: 'Referenzbereich',
    referenceBandDescription: 'Die schattierte Fläche zeigt den Referenzbereich {low} bis {high} {unit}.',
    noData: 'Keine numerischen Werte zur Darstellung verfügbar.',
    notEnoughPoints: 'Ein Verlauf benötigt mindestens zwei Messungen.',
    singlePoint: 'Es liegt nur eine Messung vor, dargestellt als Punkt.',
    latest: 'Aktuell',
    change: 'Veränderung',
    changeFrom: 'gegenüber {value} an Tag {day}',
    increased: 'gestiegen',
    decreased: 'gefallen',
    unchanged: 'unverändert',
    tableCaption: 'Datentabelle zum Verlaufsdiagramm für {analyte}',
    tableView: 'Datentabelle',
    chartView: 'Diagramm',
    accessibleSummary:
      '{analyte} wurde {count}-mal zwischen Tag {firstDay} und Tag {lastDay} gemessen. Erster Wert {first} {unit}, letzter Wert {last} {unit}. Referenzbereich {low} bis {high} {unit}.',
    pointDescription: 'Tag {day}: {value} {unit}, {flag}',
  },

  smear: {
    title: 'Blutausstrich',
    stain: 'Färbung',
    reportedBy: 'Befundet von',
    redCells: 'Erythrozytenmorphologie',
    whiteCells: 'Leukozytenmorphologie',
    platelets: 'Thrombozytenmorphologie',
    narrative: 'Befund',
    schistocytes: 'Schistozyten',
    schistocyteValue: '{value}% der Erythrozyten',
    schistocyteThreshold: 'Der ICSH-Schwellenwert für Relevanz bei Erwachsenen liegt über 1%.',
    none: 'Für diesen Fall ist kein Ausstrich dokumentiert.',
  },

  microbiology: {
    title: 'Mikrobiologie',
    specimen: 'Probenmaterial',
    site: 'Entnahmeort',
    organism: 'Erreger',
    microscopy: 'Mikroskopie',
    bacterialIndex: 'Bakterieller Index',
    morphologicalIndex: 'Morphologischer Index',
    bacterialIndexHelp:
      'Logarithmische Ridley-Skala, 0 bis 6+. Fällt unter wirksamer Therapie um etwa 1 Logstufe pro Jahr.',
    morphologicalIndexHelp:
      'Anteil solide anfärbbarer, vitaler Bazillen. Sollte unter wirksamer Therapie auf null sinken.',
    molecular: 'Molekulare Befunde',
    target: 'Zielgen',
    method: 'Methode',
    result: 'Ergebnis',
    interpretation: 'Interpretation',
    susceptibility: 'Resistenzprüfung',
    agent: 'Wirkstoff',
    susceptible: 'Sensibel',
    resistant: 'Resistent',
    none: 'Für diesen Fall ist keine Mikrobiologie dokumentiert.',
  },

  protocol: {
    title: 'Therapieschema',
    guideline: 'Leitlinienquelle',
    indication: 'Indikation',
    duration: 'Dauer',
    durationMonths: {
      one: '{count} Monat',
      other: '{count} Monate',
    },
    durationIndefinite: 'Fortlaufend',
    regimen: 'Schema',
    agent: 'Wirkstoff',
    dose: 'Dosis',
    route: 'Applikationsweg',
    frequency: 'Häufigkeit',
    monitoring: 'Überwachung',
    contraindications: 'Kontraindikationen',
    adverseEffects: 'Nebenwirkungen',
    notes: 'Hinweise',
    none: 'Für diesen Fall ist kein Therapieschema dokumentiert.',
  },

  diagnosis: {
    title: 'Diagnose',
    primary: 'Hauptdiagnose',
    differential: 'Differenzialdiagnose',
    certainty: 'Sicherheit',
    likelihood: 'Wahrscheinlichkeit',
    discriminator: 'Unterscheidungsmerkmal',
    supporting: 'Belegende Befunde',
    refuting: 'Gegenargumente',
    icd10: 'ICD-10',
    none: 'Für diesen Fall ist keine Diagnose dokumentiert.',
  },

  certainty: {
    confirmed: 'Gesichert',
    probable: 'Wahrscheinlich',
    possible: 'Möglich',
    excluded: 'Ausgeschlossen',
  },

  imaging: {
    title: 'Bildgebung',
    modality: 'Modalität',
    region: 'Region',
    findings: 'Befund',
    impression: 'Beurteilung',
    none: 'Für diesen Fall ist keine Bildgebung dokumentiert.',
  },

  teaching: {
    title: 'Lernpunkte',
    pointCount: {
      one: '{count} Lernpunkt',
      other: '{count} Lernpunkte',
    },
  },

  references: {
    title: 'Literatur',
    type: {
      guideline: 'Leitlinie',
      review: 'Übersichtsarbeit',
      primary: 'Originalarbeit',
      trial: 'Klinische Studie',
      cohort: 'Kohortenstudie',
      consensus: 'Konsensuspapier',
      surveillance: 'Surveillance-Daten',
      regulatory: 'Behördliche Mitteilung',
    },
  },

  errors: {
    title: 'Es ist ein Fehler aufgetreten',
    generic: 'Die Anfrage konnte nicht abgeschlossen werden.',
    network: 'Der Server ist nicht erreichbar. Prüfen Sie Ihre Verbindung und versuchen Sie es erneut.',
    timeout: 'Der Server hat zu lange nicht geantwortet.',
    notFound: 'Dieser Fall wurde nicht gefunden.',
    notFoundHint: 'Er wurde möglicherweise zurückgezogen oder der Link ist veraltet.',
    server: 'Der Server hat einen Fehler gemeldet.',
    parse: 'Der Server hat eine Antwort gesendet, die nicht gelesen werden konnte.',
    parseHint:
      'Dies deutet meist darauf hin, dass ein Proxy oder eine Netzwerkkomponente die Antwort verändert hat. Die Rohantwort wurde in der Konsole protokolliert.',
    offline: 'Sie sind offline. Es werden die zuletzt geladenen Daten angezeigt.',
    requestId: 'Referenz: {id}',
    statusCode: 'Status {code}',
    boundary: 'Dieser Abschnitt konnte nicht dargestellt werden und wurde isoliert, damit die übrige Seite funktioniert.',
    detail: 'Technische Details',
  },

  empty: {
    noData: 'Keine Daten',
    notRecorded: 'Nicht dokumentiert',
    none: 'Keine',
  },

  a11y: {
    loading: 'Wird geladen',
    sortedBy: 'Sortiert nach {field}, {direction}',
    selected: 'Ausgewählt',
    required: 'Erforderlich',
    externalLink: 'Wird in einem neuen Tab geöffnet',
    chartDescription: 'Diagramm. Eine Datentabelle mit denselben Werten folgt.',
    liveRegionUpdated: 'Ergebnisse aktualisiert',
  },
};
