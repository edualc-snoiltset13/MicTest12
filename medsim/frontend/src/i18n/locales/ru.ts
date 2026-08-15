/**
 * Russian message catalogue.
 *
 * Notes for reviewers:
 *  - Russian CLDR has FOUR plural categories: one (1, 21, 31…), few (2-4,
 *    22-24…), many (0, 5-20, 25-30…) and other (fractions). Every countable
 *    entry below supplies all four. A naive `count === 1` check produces
 *    "1 случаев" and "3 случай", both wrong, which is precisely why the
 *    translator uses Intl.PluralRules rather than a ternary.
 *  - Genitive forms are required after numerals: "2 случая" (few) but
 *    "5 случаев" (many).
 *  - Clinical terminology follows Russian laboratory convention:
 *    "мазок периферической крови", "референсный интервал", "схема лечения".
 *  - Decimal separator is a comma, applied by Intl.
 */

import type { Messages } from '../types';

export const ru: Messages = {
  app: {
    name: 'MedSimQA',
    tagline: 'Симуляция клинического мышления и контроль качества',
    skipToContent: 'Перейти к основному содержимому',
    syntheticBanner:
      'Все пациенты в этом корпусе синтетические. Ничто здесь не является реальной медицинской картой или клинической рекомендацией.',
  },

  nav: {
    dashboard: 'Панель',
    cases: 'Клинические случаи',
    reference: 'Референсные интервалы',
    about: 'О системе',
    backToCases: 'Ко всем случаям',
  },

  actions: {
    search: 'Поиск',
    filter: 'Фильтр',
    clear: 'Очистить',
    clearAll: 'Очистить все фильтры',
    retry: 'Повторить',
    reload: 'Перезагрузить',
    close: 'Закрыть',
    expand: 'Показать больше',
    collapse: 'Показать меньше',
    copy: 'Копировать',
    copied: 'Скопировано',
    download: 'Скачать',
    print: 'Печать',
    viewChart: 'График',
    viewTable: 'Таблица',
    previous: 'Назад',
    next: 'Далее',
  },

  theme: {
    label: 'Тема',
    light: 'Светлая',
    dark: 'Тёмная',
    system: 'Системная',
    toggle: 'Переключить на {mode} тему',
  },

  language: {
    label: 'Язык',
    change: 'Изменить язык',
    current: 'Текущий язык: {language}',
    decimalNotice: 'Десятичный разделитель в этом языке: {separator}',
  },

  dashboard: {
    title: 'Библиотека случаев',
    subtitle: 'Синтетические клинические случаи для оценки клинического мышления',
    resultCount: {
      one: '{count} случай',
      few: '{count} случая',
      many: '{count} случаев',
      other: '{count} случая',
    },
    // Agreement follows {total}, not {count}: "1 из 25 случаев". The caller
    // passes pluralCount={total} so the selector uses the right number.
    resultCountFiltered: {
      one: '{count} из {total} случая',
      few: '{count} из {total} случаев',
      many: '{count} из {total} случаев',
      other: '{count} из {total} случаев',
    },
    noResults: 'Нет случаев, соответствующих этим фильтрам',
    noResultsHint: 'Попробуйте снять один из фильтров или расширить поисковый запрос.',
    loading: 'Загрузка случаев',
    stats: {
      totalCases: 'Случаи',
      totalPanels: 'Лабораторные панели',
      totalResults: 'Лабораторные результаты',
      disciplines: 'Дисциплины',
    },
  },

  filters: {
    title: 'Фильтры',
    searchPlaceholder: 'Поиск случаев, кодов, находок…',
    searchLabel: 'Поиск по клиническим случаям',
    discipline: 'Дисциплина',
    subspecialty: 'Раздел',
    difficulty: 'Сложность',
    status: 'Статус',
    tag: 'Метка',
    sortBy: 'Сортировать по',
    sortDirection: 'Порядок сортировки',
    ascending: 'По возрастанию',
    descending: 'По убыванию',
    all: 'Все',
    activeCount: {
      one: 'Активен {count} фильтр',
      few: 'Активны {count} фильтра',
      many: 'Активно {count} фильтров',
      other: 'Активно {count} фильтра',
    },
  },

  discipline: {
    chemical_pathology: 'Клиническая биохимия',
    microbiology: 'Микробиология',
    hematology: 'Гематология',
    pharmacology: 'Фармакология',
  },

  subspecialty: {
    thyroid: 'Щитовидная железа',
    haemolytic_anaemia: 'Гемолитическая анемия',
    mycobacteriology: 'Микобактериология',
    antimicrobial_chemotherapy: 'Антимикробная химиотерапия',
  },

  caseStatus: {
    draft: 'Черновик',
    in_review: 'На рецензии',
    published: 'Опубликован',
    retired: 'Изъят',
  },

  difficulty: {
    label: 'Сложность',
    level: 'Уровень {level} из 5',
    1: 'Базовый',
    2: 'Простой',
    3: 'Средний',
    4: 'Продвинутый',
    5: 'Экспертный',
  },

  sort: {
    case_code: 'Код случая',
    title: 'Название',
    difficulty: 'Сложность',
    updated_at: 'Дата обновления',
    created_at: 'Дата создания',
    discipline: 'Дисциплина',
  },

  case: {
    code: 'Код случая',
    version: 'Версия {version}',
    updated: 'Обновлено {date}',
    author: 'Автор',
    reviewedBy: 'Рецензент',
    tags: 'Метки',
    codes: 'Коды классификации',
    sections: {
      overview: 'Обзор',
      patient: 'Пациент',
      presentation: 'Обращение',
      labs: 'Лабораторные результаты',
      trends: 'Динамика',
      smear: 'Мазок периферической крови',
      microbiology: 'Микробиология',
      imaging: 'Визуализация',
      protocol: 'Схема лечения',
      diagnosis: 'Диагноз',
      teaching: 'Учебные положения',
      references: 'Источники',
    },
  },

  patient: {
    title: 'Пациент',
    age: 'Возраст',
    ageValue: '{age} лет',
    sex: 'Пол',
    weight: 'Масса тела',
    height: 'Рост',
    bmi: 'ИМТ',
    ancestry: 'Происхождение',
    pregnancy: 'Статус беременности',
    occupation: 'Профессия',
    region: 'Регион',
    pseudonym: 'Идентификатор',
  },

  sex: {
    female: 'Женский',
    male: 'Мужской',
    intersex: 'Интерсекс',
    unspecified: 'Не указан',
  },

  presentation: {
    chiefComplaint: 'Основная жалоба',
    history: 'Анамнез настоящего заболевания',
    pastMedical: 'Анамнез жизни',
    medications: 'Лекарственная терапия',
    allergies: 'Аллергии',
    familyHistory: 'Семейный анамнез',
    socialHistory: 'Социальный анамнез',
    reviewOfSystems: 'Опрос по системам',
    vitals: 'Витальные показатели',
    examination: 'Данные осмотра',
    none: 'Не зафиксировано',
    medication: {
      name: 'Препарат',
      dose: 'Доза',
      route: 'Путь введения',
      frequency: 'Кратность',
      indication: 'Показание',
      notes: 'Примечания',
    },
  },

  vitals: {
    heart_rate_bpm: 'Частота сердечных сокращений',
    blood_pressure_mmhg: 'Артериальное давление',
    respiratory_rate: 'Частота дыхания',
    temperature_c: 'Температура',
    spo2_percent: 'Сатурация кислорода',
    weight_kg: 'Масса тела',
    map_mmhg: 'Среднее артериальное давление',
    urine_output_ml_h: 'Диурез',
    rhythm: 'Ритм',
    gcs: 'Шкала комы Глазго',
  },

  labs: {
    title: 'Лабораторные результаты',
    panel: 'Панель',
    analyte: 'Аналит',
    value: 'Значение',
    unit: 'Единица',
    referenceRange: 'Референсный интервал',
    flag: 'Отметка',
    method: 'Метод',
    specimen: 'Биоматериал',
    laboratory: 'Лаборатория',
    analyser: 'Анализатор',
    collected: 'Забор',
    day: 'День {day}',
    dayZero: 'Обращение',
    note: 'Пояснение к интерпретации',
    criticalResult: 'Критическое значение',
    criticalWarning: 'Это значение выходит за пределы критического порога вмешательства.',
    noResults: 'Для этого случая лабораторные результаты не зафиксированы.',
    panelCount: {
      one: '{count} панель',
      few: '{count} панели',
      many: '{count} панелей',
      other: '{count} панели',
    },
    resultCount: {
      one: '{count} результат',
      few: '{count} результата',
      many: '{count} результатов',
      other: '{count} результата',
    },
  },

  flag: {
    N: 'Норма',
    H: 'Повышено',
    L: 'Понижено',
    HH: 'Критически повышено',
    LL: 'Критически понижено',
    A: 'Отклонение',
    // Краткие коды HL7 являются международными и не переводятся.
    short: { N: 'N', H: 'H', L: 'L', HH: 'HH', LL: 'LL', A: 'A' },
  },

  chart: {
    title: 'Динамика во времени',
    subtitle: 'Значения отложены относительно дней от момента обращения',
    selectAnalyte: 'Выбрать аналит',
    compare: 'Сравнить аналиты',
    compareLimit: 'Одновременно можно сравнивать до трёх аналитов.',
    axisX: 'Дней от обращения',
    axisY: 'Значение ({unit})',
    referenceBand: 'Референсный интервал',
    referenceBandDescription: 'Заштрихованная область показывает референсный интервал от {low} до {high} {unit}.',
    noData: 'Нет числовых результатов для построения графика.',
    notEnoughPoints: 'Для построения динамики нужно не менее двух измерений.',
    singlePoint: 'Доступно только одно измерение, показано точкой.',
    latest: 'Последнее',
    change: 'Изменение',
    changeFrom: 'по сравнению с {value} на день {day}',
    increased: 'выросло',
    decreased: 'снизилось',
    unchanged: 'без изменений',
    tableCaption: 'Таблица данных к графику динамики показателя {analyte}',
    tableView: 'Таблица данных',
    chartView: 'График',
    accessibleSummary:
      'Показатель {analyte} измерен {count} раз в период с дня {firstDay} по день {lastDay}. Первое значение {first} {unit}, последнее значение {last} {unit}. Референсный интервал от {low} до {high} {unit}.',
    pointDescription: 'День {day}: {value} {unit}, {flag}',
  },

  smear: {
    title: 'Мазок периферической крови',
    stain: 'Окраска',
    reportedBy: 'Заключение выдал',
    redCells: 'Морфология эритроцитов',
    whiteCells: 'Морфология лейкоцитов',
    platelets: 'Морфология тромбоцитов',
    narrative: 'Заключение',
    schistocytes: 'Шистоциты',
    schistocyteValue: '{value}% эритроцитов',
    schistocyteThreshold: 'Порог значимости по ICSH у взрослых составляет более 1%.',
    none: 'Для этого случая мазок не зафиксирован.',
  },

  microbiology: {
    title: 'Микробиология',
    specimen: 'Биоматериал',
    site: 'Локализация',
    organism: 'Возбудитель',
    microscopy: 'Микроскопия',
    bacterialIndex: 'Бактериальный индекс',
    morphologicalIndex: 'Морфологический индекс',
    bacterialIndexHelp:
      'Логарифмическая шкала Ридли, от 0 до 6+. На фоне эффективной терапии снижается примерно на 1 логарифм в год.',
    morphologicalIndexHelp:
      'Доля сплошь окрашивающихся, то есть жизнеспособных, бацилл. На фоне эффективной терапии должна достигать нуля.',
    molecular: 'Молекулярные находки',
    target: 'Мишень',
    method: 'Метод',
    result: 'Результат',
    interpretation: 'Интерпретация',
    susceptibility: 'Чувствительность к препаратам',
    agent: 'Препарат',
    susceptible: 'Чувствителен',
    resistant: 'Устойчив',
    none: 'Для этого случая микробиологические данные не зафиксированы.',
  },

  protocol: {
    title: 'Схема лечения',
    guideline: 'Источник рекомендаций',
    indication: 'Показание',
    duration: 'Длительность',
    durationMonths: {
      one: '{count} месяц',
      few: '{count} месяца',
      many: '{count} месяцев',
      other: '{count} месяца',
    },
    durationIndefinite: 'Постоянно',
    regimen: 'Режим',
    agent: 'Препарат',
    dose: 'Доза',
    route: 'Путь введения',
    frequency: 'Кратность',
    monitoring: 'Мониторинг',
    contraindications: 'Противопоказания',
    adverseEffects: 'Нежелательные явления',
    notes: 'Примечания',
    none: 'Для этого случая схема лечения не зафиксирована.',
  },

  diagnosis: {
    title: 'Диагноз',
    primary: 'Основной диагноз',
    differential: 'Дифференциальный диагноз',
    certainty: 'Степень достоверности',
    likelihood: 'Вероятность',
    discriminator: 'Дифференцирующий признак',
    supporting: 'Данные в пользу',
    refuting: 'Данные против',
    icd10: 'МКБ-10',
    none: 'Для этого случая диагноз не зафиксирован.',
  },

  certainty: {
    confirmed: 'Подтверждён',
    probable: 'Вероятен',
    possible: 'Возможен',
    excluded: 'Исключён',
  },

  imaging: {
    title: 'Визуализация',
    modality: 'Метод',
    region: 'Область',
    findings: 'Находки',
    impression: 'Заключение',
    none: 'Для этого случая данные визуализации не зафиксированы.',
  },

  teaching: {
    title: 'Учебные положения',
    pointCount: {
      one: '{count} учебное положение',
      few: '{count} учебных положения',
      many: '{count} учебных положений',
      other: '{count} учебных положения',
    },
  },

  references: {
    title: 'Источники',
    type: {
      guideline: 'Клинические рекомендации',
      review: 'Обзор',
      primary: 'Оригинальное исследование',
      trial: 'Клиническое исследование',
      cohort: 'Когортное исследование',
      consensus: 'Согласительный документ',
      surveillance: 'Данные надзора',
      regulatory: 'Уведомление регулятора',
    },
  },

  errors: {
    title: 'Произошла ошибка',
    generic: 'Не удалось выполнить запрос.',
    network: 'Сервер недоступен. Проверьте подключение и повторите попытку.',
    timeout: 'Сервер слишком долго не отвечал.',
    notFound: 'Этот случай не найден.',
    notFoundHint: 'Возможно, он был изъят, либо ссылка устарела.',
    server: 'Сервер сообщил об ошибке.',
    parse: 'Сервер вернул ответ, который не удалось прочитать.',
    parseHint:
      'Обычно это означает, что прокси-сервер или сетевое устройство изменило ответ. Исходный ответ записан в консоль.',
    offline: 'Похоже, вы не в сети. Показаны последние загруженные данные.',
    requestId: 'Идентификатор: {id}',
    statusCode: 'Статус {code}',
    boundary: 'Этот раздел не удалось отобразить, он изолирован, чтобы остальная часть страницы продолжала работать.',
    detail: 'Технические подробности',
  },

  empty: {
    noData: 'Нет данных',
    notRecorded: 'Не зафиксировано',
    none: 'Отсутствует',
  },

  a11y: {
    loading: 'Загрузка',
    sortedBy: 'Отсортировано по полю {field}, {direction}',
    selected: 'Выбрано',
    required: 'Обязательно',
    externalLink: 'Откроется в новой вкладке',
    chartDescription: 'График. Ниже приведена таблица с теми же значениями.',
    liveRegionUpdated: 'Результаты обновлены',
  },
};
