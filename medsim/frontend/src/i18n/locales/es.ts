/**
 * Spanish message catalogue.
 *
 * Notes for reviewers:
 *  - Peninsular Spanish (es-ES) medical register. "Frotis de sangre periférica"
 *    and "Intervalo de referencia" are the terms a Spanish clinician expects.
 *  - Spanish CLDR uses one/many/other. "many" applies to large round numbers
 *    (millions); we supply it for completeness even though case counts never
 *    reach it.
 *  - Decimal separator is a comma, applied by Intl rather than by these strings.
 */

import type { Messages } from '../types';

export const es: Messages = {
  app: {
    name: 'MedSimQA',
    tagline: 'Simulación de razonamiento clínico y control de calidad',
    skipToContent: 'Saltar al contenido principal',
    syntheticBanner:
      'Todos los pacientes de este corpus son sintéticos. Nada de lo aquí mostrado es una historia clínica real ni una recomendación médica.',
  },

  nav: {
    dashboard: 'Panel',
    cases: 'Casos clínicos',
    reference: 'Intervalos de referencia',
    about: 'Acerca de',
    backToCases: 'Volver a todos los casos',
  },

  actions: {
    search: 'Buscar',
    filter: 'Filtrar',
    clear: 'Limpiar',
    clearAll: 'Limpiar todos los filtros',
    retry: 'Reintentar',
    reload: 'Recargar',
    close: 'Cerrar',
    expand: 'Mostrar más',
    collapse: 'Mostrar menos',
    copy: 'Copiar',
    copied: 'Copiado',
    download: 'Descargar',
    print: 'Imprimir',
    viewChart: 'Gráfico',
    viewTable: 'Tabla',
    previous: 'Anterior',
    next: 'Siguiente',
  },

  theme: {
    label: 'Tema',
    light: 'Claro',
    dark: 'Oscuro',
    system: 'Sistema',
    toggle: 'Cambiar al tema {mode}',
  },

  language: {
    label: 'Idioma',
    change: 'Cambiar idioma',
    current: 'Idioma actual: {language}',
    decimalNotice: 'Separador decimal en este idioma: {separator}',
  },

  dashboard: {
    title: 'Biblioteca de casos',
    subtitle: 'Casos clínicos sintéticos para la evaluación del razonamiento clínico',
    resultCount: {
      one: '{count} caso',
      many: '{count} de casos',
      other: '{count} casos',
    },
    resultCountFiltered: {
      one: '{count} de {total} caso',
      many: '{count} de {total} de casos',
      other: '{count} de {total} casos',
    },
    noResults: 'Ningún caso coincide con estos filtros',
    noResultsHint: 'Pruebe a quitar un filtro o a ampliar la búsqueda.',
    loading: 'Cargando casos',
    stats: {
      totalCases: 'Casos',
      totalPanels: 'Perfiles analíticos',
      totalResults: 'Resultados analíticos',
      disciplines: 'Especialidades',
    },
  },

  filters: {
    title: 'Filtros',
    searchPlaceholder: 'Buscar casos, códigos, hallazgos…',
    searchLabel: 'Buscar casos clínicos',
    discipline: 'Especialidad',
    subspecialty: 'Subespecialidad',
    difficulty: 'Dificultad',
    status: 'Estado',
    tag: 'Etiqueta',
    sortBy: 'Ordenar por',
    sortDirection: 'Sentido de ordenación',
    ascending: 'Ascendente',
    descending: 'Descendente',
    all: 'Todos',
    activeCount: {
      one: '{count} filtro activo',
      many: '{count} de filtros activos',
      other: '{count} filtros activos',
    },
  },

  discipline: {
    chemical_pathology: 'Bioquímica clínica',
    microbiology: 'Microbiología',
    hematology: 'Hematología',
    pharmacology: 'Farmacología',
  },

  subspecialty: {
    thyroid: 'Tiroides',
    haemolytic_anaemia: 'Anemia hemolítica',
    mycobacteriology: 'Micobacteriología',
    antimicrobial_chemotherapy: 'Quimioterapia antimicrobiana',
  },

  caseStatus: {
    draft: 'Borrador',
    in_review: 'En revisión',
    published: 'Publicado',
    retired: 'Retirado',
  },

  difficulty: {
    label: 'Dificultad',
    level: 'Nivel {level} de 5',
    1: 'Básico',
    2: 'Sencillo',
    3: 'Intermedio',
    4: 'Avanzado',
    5: 'Experto',
  },

  sort: {
    case_code: 'Código del caso',
    title: 'Título',
    difficulty: 'Dificultad',
    updated_at: 'Última actualización',
    created_at: 'Creación',
    discipline: 'Especialidad',
  },

  case: {
    code: 'Código del caso',
    version: 'Versión {version}',
    updated: 'Actualizado el {date}',
    author: 'Autor',
    reviewedBy: 'Revisado por',
    tags: 'Etiquetas',
    codes: 'Códigos de clasificación',
    sections: {
      overview: 'Resumen',
      patient: 'Paciente',
      presentation: 'Presentación',
      labs: 'Resultados de laboratorio',
      trends: 'Evolución temporal',
      smear: 'Frotis de sangre periférica',
      microbiology: 'Microbiología',
      imaging: 'Pruebas de imagen',
      protocol: 'Pauta de tratamiento',
      diagnosis: 'Diagnóstico',
      teaching: 'Puntos docentes',
      references: 'Bibliografía',
    },
  },

  patient: {
    title: 'Paciente',
    age: 'Edad',
    ageValue: '{age} años',
    sex: 'Sexo',
    weight: 'Peso',
    height: 'Talla',
    bmi: 'IMC',
    ancestry: 'Ascendencia',
    pregnancy: 'Estado gestacional',
    occupation: 'Ocupación',
    region: 'Región',
    pseudonym: 'Identificador',
  },

  sex: {
    female: 'Mujer',
    male: 'Hombre',
    intersex: 'Intersexual',
    unspecified: 'No especificado',
  },

  presentation: {
    chiefComplaint: 'Motivo de consulta',
    history: 'Enfermedad actual',
    pastMedical: 'Antecedentes personales',
    medications: 'Tratamiento habitual',
    allergies: 'Alergias',
    familyHistory: 'Antecedentes familiares',
    socialHistory: 'Historia social',
    reviewOfSystems: 'Anamnesis por aparatos',
    vitals: 'Constantes vitales',
    examination: 'Exploración física',
    none: 'No registrado',
    medication: {
      name: 'Fármaco',
      dose: 'Dosis',
      route: 'Vía',
      frequency: 'Frecuencia',
      indication: 'Indicación',
      notes: 'Observaciones',
    },
  },

  vitals: {
    heart_rate_bpm: 'Frecuencia cardíaca',
    blood_pressure_mmhg: 'Presión arterial',
    respiratory_rate: 'Frecuencia respiratoria',
    temperature_c: 'Temperatura',
    spo2_percent: 'Saturación de oxígeno',
    weight_kg: 'Peso',
    map_mmhg: 'Presión arterial media',
    urine_output_ml_h: 'Diuresis',
    rhythm: 'Ritmo',
    gcs: 'Escala de coma de Glasgow',
  },

  labs: {
    title: 'Resultados de laboratorio',
    panel: 'Perfil',
    analyte: 'Analito',
    value: 'Valor',
    unit: 'Unidad',
    referenceRange: 'Intervalo de referencia',
    flag: 'Marca',
    method: 'Método',
    specimen: 'Muestra',
    laboratory: 'Laboratorio',
    analyser: 'Analizador',
    collected: 'Extracción',
    day: 'Día {day}',
    dayZero: 'Presentación',
    note: 'Nota interpretativa',
    criticalResult: 'Valor crítico',
    criticalWarning: 'Este resultado está fuera del límite crítico de actuación.',
    noResults: 'No hay resultados de laboratorio registrados para este caso.',
    panelCount: {
      one: '{count} perfil',
      many: '{count} de perfiles',
      other: '{count} perfiles',
    },
    resultCount: {
      one: '{count} resultado',
      many: '{count} de resultados',
      other: '{count} resultados',
    },
  },

  flag: {
    N: 'Normal',
    H: 'Elevado',
    L: 'Bajo',
    HH: 'Críticamente elevado',
    LL: 'Críticamente bajo',
    A: 'Anormal',
    // HL7 short codes are international and are not translated.
    short: { N: 'N', H: 'H', L: 'L', HH: 'HH', LL: 'LL', A: 'A' },
  },

  chart: {
    title: 'Evolución temporal',
    subtitle: 'Valores representados frente a los días desde la presentación',
    selectAnalyte: 'Seleccionar analito',
    compare: 'Comparar analitos',
    compareLimit: 'Se pueden comparar hasta tres analitos a la vez.',
    axisX: 'Días desde la presentación',
    axisY: 'Valor ({unit})',
    referenceBand: 'Intervalo de referencia',
    referenceBandDescription: 'El área sombreada muestra el intervalo de referencia de {low} a {high} {unit}.',
    noData: 'No hay resultados numéricos disponibles para representar.',
    notEnoughPoints: 'Una evolución requiere al menos dos determinaciones.',
    singlePoint: 'Solo se dispone de una determinación, representada como un punto.',
    latest: 'Último',
    change: 'Variación',
    changeFrom: 'respecto a {value} el día {day}',
    increased: 'ha aumentado',
    decreased: 'ha disminuido',
    unchanged: 'sin cambios',
    tableCaption: 'Tabla de datos del gráfico de evolución de {analyte}',
    tableView: 'Tabla de datos',
    chartView: 'Gráfico',
    accessibleSummary:
      '{analyte} determinado {count} veces entre el día {firstDay} y el día {lastDay}. Primer valor {first} {unit}, último valor {last} {unit}. Intervalo de referencia de {low} a {high} {unit}.',
    pointDescription: 'Día {day}: {value} {unit}, {flag}',
  },

  smear: {
    title: 'Frotis de sangre periférica',
    stain: 'Tinción',
    reportedBy: 'Informado por',
    redCells: 'Morfología eritrocitaria',
    whiteCells: 'Morfología leucocitaria',
    platelets: 'Morfología plaquetaria',
    narrative: 'Informe',
    schistocytes: 'Esquistocitos',
    schistocyteValue: '{value}% de los hematíes',
    schistocyteThreshold: 'El umbral de significación del ICSH en adultos es superior al 1%.',
    none: 'No hay frotis registrado para este caso.',
  },

  microbiology: {
    title: 'Microbiología',
    specimen: 'Muestra',
    site: 'Localización',
    organism: 'Microorganismo',
    microscopy: 'Microscopía',
    bacterialIndex: 'Índice bacteriano',
    morphologicalIndex: 'Índice morfológico',
    bacterialIndexHelp:
      'Escala logarítmica de Ridley, de 0 a 6+. Desciende aproximadamente 1 logaritmo al año con tratamiento eficaz.',
    morphologicalIndexHelp:
      'Porcentaje de bacilos de tinción sólida, es decir viables. Debe llegar a cero con tratamiento eficaz.',
    molecular: 'Hallazgos moleculares',
    target: 'Diana',
    method: 'Método',
    result: 'Resultado',
    interpretation: 'Interpretación',
    susceptibility: 'Sensibilidad antimicrobiana',
    agent: 'Antimicrobiano',
    susceptible: 'Sensible',
    resistant: 'Resistente',
    none: 'No hay microbiología registrada para este caso.',
  },

  protocol: {
    title: 'Pauta de tratamiento',
    guideline: 'Guía de referencia',
    indication: 'Indicación',
    duration: 'Duración',
    durationMonths: {
      one: '{count} mes',
      many: '{count} de meses',
      other: '{count} meses',
    },
    durationIndefinite: 'Indefinida',
    regimen: 'Régimen',
    agent: 'Fármaco',
    dose: 'Dosis',
    route: 'Vía',
    frequency: 'Frecuencia',
    monitoring: 'Seguimiento',
    contraindications: 'Contraindicaciones',
    adverseEffects: 'Efectos adversos',
    notes: 'Observaciones',
    none: 'No hay pauta de tratamiento registrada para este caso.',
  },

  diagnosis: {
    title: 'Diagnóstico',
    primary: 'Diagnóstico principal',
    differential: 'Diagnóstico diferencial',
    certainty: 'Certeza',
    likelihood: 'Probabilidad',
    discriminator: 'Dato discriminante',
    supporting: 'Datos a favor',
    refuting: 'Datos en contra',
    icd10: 'CIE-10',
    none: 'No hay diagnóstico registrado para este caso.',
  },

  certainty: {
    confirmed: 'Confirmado',
    probable: 'Probable',
    possible: 'Posible',
    excluded: 'Excluido',
  },

  imaging: {
    title: 'Pruebas de imagen',
    modality: 'Modalidad',
    region: 'Región',
    findings: 'Hallazgos',
    impression: 'Impresión diagnóstica',
    none: 'No hay pruebas de imagen registradas para este caso.',
  },

  teaching: {
    title: 'Puntos docentes',
    pointCount: {
      one: '{count} punto docente',
      many: '{count} de puntos docentes',
      other: '{count} puntos docentes',
    },
  },

  references: {
    title: 'Bibliografía',
    type: {
      guideline: 'Guía clínica',
      review: 'Revisión',
      primary: 'Investigación original',
      trial: 'Ensayo clínico',
      cohort: 'Estudio de cohortes',
      consensus: 'Documento de consenso',
      surveillance: 'Datos de vigilancia',
      regulatory: 'Comunicación regulatoria',
    },
  },

  errors: {
    title: 'Se ha producido un error',
    generic: 'No se ha podido completar la solicitud.',
    network: 'No se ha podido contactar con el servidor. Compruebe su conexión e inténtelo de nuevo.',
    timeout: 'El servidor ha tardado demasiado en responder.',
    notFound: 'No se ha encontrado ese caso.',
    notFoundHint: 'Es posible que haya sido retirado o que el enlace esté obsoleto.',
    server: 'El servidor ha notificado un error.',
    parse: 'El servidor ha devuelto una respuesta que no se ha podido leer.',
    parseHint:
      'Esto suele indicar que un proxy o un dispositivo de red ha alterado la respuesta. La respuesta original se ha registrado en la consola.',
    offline: 'Parece que está sin conexión. Se muestran los últimos datos cargados.',
    requestId: 'Referencia: {id}',
    statusCode: 'Estado {code}',
    boundary: 'Esta sección no se ha podido mostrar y se ha aislado para que el resto de la página siga funcionando.',
    detail: 'Detalle técnico',
  },

  empty: {
    noData: 'Sin datos',
    notRecorded: 'No registrado',
    none: 'Ninguno',
  },

  a11y: {
    loading: 'Cargando',
    sortedBy: 'Ordenado por {field}, {direction}',
    selected: 'Seleccionado',
    required: 'Obligatorio',
    externalLink: 'Se abre en una pestaña nueva',
    chartDescription: 'Gráfico. A continuación se ofrece una tabla con los mismos valores.',
    liveRegionUpdated: 'Resultados actualizados',
  },
};
