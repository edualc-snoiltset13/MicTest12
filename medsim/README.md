# MedSimQA

A medical diagnosis simulation and QA testing framework: a curated corpus of
synthetic clinical case studies, a clinician dashboard that renders them in five
languages, a three-layer test harness, and a grader that scores LLM diagnostic
reasoning against the same corpus.

> **Every patient in this corpus is synthetic.** Values are constructed to be
> internally consistent and pedagogically useful. Nothing here is a real patient
> record, and nothing here is clinical advice.

---

## What is here

| Path | What it is |
|---|---|
| `backend/` | FastAPI service, SQLAlchemy models, 25-case JSON corpus, 78 tests |
| `frontend/` | React + TypeScript + Tailwind dashboard, five locales, SVG lab charts |
| `qa/` | 50 Cypress edge cases, proxy fault-injection configs, Samsung ADB scripts |
| `ml/` | Clinical media annotation schema, LLM evaluator, 42 tests |
| `deploy/` | Ubuntu deployment script, systemd units, nginx config, OBS profile |
| `docs/ADR.md` | Architectural decision record: 28 decisions, with the rejected alternatives |

## The corpus

25 cases, 119 lab panels, 494 results, across four disciplines.

**Thyroid (9)** — Graves disease, Hashimoto with its reversible secondary
derangements, serial subclinical progression, non-thyroidal illness versus
central hypothyroidism, amiodarone type 1 versus type 2, biotin assay
interference, thyrotoxicosis factitia, postpartum thyroiditis, and THRB
resistance versus a TSH-secreting adenoma.

**Haemolytic anaemia (9)** — deliberately split immune (warm AIHA, cold
agglutinin disease, delayed haemolytic transfusion reaction, paroxysmal cold
haemoglobinuria) against non-immune (G6PD deficiency, hereditary spherocytosis,
TTP, prosthetic valve haemolysis, PNH), each with full peripheral smear
morphology. Several are paired on purpose: HEM-001 and HEM-004 produce nearly
identical films, and only the direct antiglobulin test separates them.

**Leprosy and antimicrobial chemotherapy (7)** — rifampicin-resistant relapse
with an rpoB mutation, triple-resistant folP1/rpoB/gyrA disease built from three
documented episodes of functional monotherapy, both reaction types, paediatric
paucibacillary disease, HIV and pregnancy drug interactions, and VNTR-confirmed
reinfection.

Every case carries five-locale titles and summaries, reference intervals, ICD-10
and SNOMED codes, treatment protocols with monitoring and contraindications, a
scored differential, teaching points, and a machine-readable reasoning key with
safety rules.

## Running it

```bash
# Backend
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m app.seed
./.venv/bin/python -m uvicorn app.main:app --port 8000

# Frontend
cd frontend
npm install && npm run build && npm run preview     # http://localhost:4173

# Tests
cd backend && ./.venv/bin/python -m pytest tests/ -q     # 78
cd ml      && python -m pytest tests/ -q                 # 42
cd qa      && npm test                                   # 50 Cypress edge cases
cd frontend && npm run test:i18n                         # locale parity
```

Deploy to Ubuntu 22.04/24.04:

```bash
sudo ./deploy/deploy-ubuntu.sh --domain medsim.example.org --with-tls
```

## What the tests actually check

The test suites are written to catch the failures this kind of system really
has, not to inflate a count.

The **corpus tests** assert clinical invariants: that every result flag agrees
with its reference interval, that every case has exactly one primary diagnosis,
that every haemolysis case reports a DAT, that every MDR leprosy case carries
resistance genotyping, and that no translation is a copy of the English. They
caught six mis-flagged critical values during authoring.

The **QA suite** covers 50 numbered edge cases, weighted towards localized
layout and network faults. Running its assertions against the application found
six real defects, all fixed and documented in `qa/README.md` — including
visually-hidden labels escaping a scroll container to add 172px of horizontal
page scroll in German, and Russian plural agreement following the wrong number.

The **evaluator tests** are mostly about ways a scorer can be wrong while
looking right: crediting a negated mention, matching a substring, or passing a
response that recommends a contraindicated drug. Writing them found three
weaknesses in the negation detector.

## Design decisions worth knowing before reading the code

- **JSON is the source of truth**, the database is a projection. Clinical
  content has to be reviewable in a pull request diff.
- **One y-axis, always.** Analytes with different units get their own panel;
  the compare view normalises rather than drawing a second axis.
- **Colour never carries clinical meaning alone.** Flags render a wash, a
  directional glyph and a translated name.
- **HL7 flag codes are not translated.** Localising `L` to `N` for *niedrig*
  collides with `N` for *normal*.
- **A safety violation is disqualifying** in the evaluator, whatever the
  content score.

The reasoning behind each, and the alternatives rejected, is in
[`docs/ADR.md`](docs/ADR.md).
