# Obstetricia Quiz — Project Guide

## What this is

Interactive multiple-choice quiz app for Obstetricia (UNQ Hospital de Clínicas).
Served via GitHub Pages: https://lucas-matw-unq.github.io/obstetricia-quiz/

---

## Directory structure

```
Obstetricia/
├── CLAUDE.md                              ← this file
├── index.html                             ← GitHub Pages redirect to Obstetricia_Quiz.html
├── Obstetricia_Quiz.html                  ← quiz app (built, served by GitHub Pages)
├── quiz_questions_pool_normalized.json    ← master question bank (539 questions)
├── documents_metadata.json                ← index of processed source files + extraction notes
├── question_schema.json                   ← schema reference for question objects
├── rebuild.sh                             ← rebuild quiz HTML from bank (bash rebuild.sh)
│
├── sources/                               ← all study material
│   ├── Apunte Sol Modificado.pdf         ← main apunte (Sol Lamanna, reedición 2024)
│   ├── OBSTETRICIA .pdf                  ← compilado de preguntas (source for extract_compilado.py)
│   ├── v3-2026-1 CRONOGRAMA.xlsx         ← course schedule and 30 official topics
│   ├── choices/                          ← exam question collections (parciales, finales)
│   │   ├── Compilado todos los choices obstetricia.pdf   ← main source (299 pages, 811+ Qs)
│   │   ├── Compilado_de_examenes_parciales_10_preguntas_UDH_Clínicas.pdf  ← NOT processed
│   │   ├── Choice por tema.docx.pdf                                        ← NOT processed
│   │   ├── Obstetricia CHOICES pdf-1.pdf                                   ← NOT processed
│   │   ├── Super compilado obstetricia done.pdf                            ← NOT processed
│   │   ├── Final octubre 2024.pdf        ← 10 questions (IDs 294-303)
│   │   ├── Final.pdf                     ← 27 questions (IDs 304-330)
│   │   ├── Parical.pdf                   ← duplicate of Final octubre 2024, skipped
│   │   ├── Parcial (1)-1.pdf             ← 0 questions (preguntas ilegibles)
│   │   ├── PHOTO-2024-11-28-00-31-28.pdf ← 5 questions (IDs 335-339)
│   │   └── 11-6/                         ← exam 11/06/2025 photos (1.jpg=4q, 2-4.jpg=0q duplicates)
│   └── slides/                           ← professor slides (Diapos extras)
│       ├── 19. 1CESAREA. DRA. CEPEDA.pdf
│       ├── 1FORCEPS.DR. DIDIA.pdf
│       ├── CARDIOPATÍAS Y EMBARAZO.v2025.PDF.MESSINA.pdf
│       ├── ECOGRAFIA 2 T. Y 3T.DRA. YABARRA.pdf
│       ├── HEMORRAGIA PUERPERAL. ETCHEPAREBORDA.pdf
│       ├── HIPOXIA FETAL AGUDA. DR. RUSCONI (1).pdf
│       ├── INDUCCION -CONDUCCION. DRA.VERA.pdf
│       ├── IVE - ILE. DRA. MORGANTI.pdf
│       ├── Mecanismo de Parto en Presentacion Cefalica de Vertice. pdf. NICHOLSON.pdf
│       └── Medicina mmaterno fetal..pdf
│
├── scripts/                               ← extraction & processing scripts
│   ├── extract_compilado.py              ← MAIN: extracts from OBSTETRICIA .pdf → tmp/questions_compilado_all.json
│   ├── remap_topics.py                   ← utility: reassign question topics by content rules
│   ├── extract.py                        ← legacy: early extraction attempt
│   ├── extract_part1.py                  ← legacy
│   ├── extract_part2.py                  ← legacy
│   └── map_apunte.py                     ← legacy: maps apunte sections
│
└── tmp/                                   ← generated / temporary files (not committed)
    ├── apunte_sol_text_1.txt             ← extracted text from Apunte Sol (part 1)
    ├── apunte_sol_text_2.txt             ← extracted text from Apunte Sol (part 2)
    ├── apunte_sol_map.txt                ← section map of apunte
    ├── cesarea.txt                        ← extracted cesárea section
    ├── questions_compilado_all.json      ← raw output of extract_compilado.py (before merge)
    └── questions_compilado_validated.json ← validated subset (superseded by bank)
```

---

## Question bank

**File:** `quiz_questions_pool_normalized.json`

| Stat | Value |
|------|-------|
| Total questions | 539 |
| Confirmed (`needs_review: false`) | 536 |
| Unvalidated (`needs_review: true`) | 3 (IDs: 396, 488, 507) |
| Topics | 30 (matches CRONOGRAMA) |
| Origins | `existing` (real exam Qs) + `generated` (AI from apunte) |

### needs_review behavior

Questions with `metadata.needs_review: true` are **shown in the quiz** with:
- Amber ⚠️ banner before options: "Pregunta sin respuesta validada"
- No green/red feedback after answering
- Excluded from score (score shows X/Y where Y = confirmed questions only)
- Results screen shows count of unvalidated questions separately

To confirm an answer: set `correct_index`, `correct_letter`, `metadata.needs_review: false` in the bank, then run `bash rebuild.sh`.

---

## 30 Official topics (CRONOGRAMA)

1. Diagnóstico de Embarazo y Semiología Obstétrica
2. Control Prenatal
3. Modificaciones Gravídicas, Nutrición y Emesis
4. Estática Fetal
5. Fenómenos del Trabajo de Parto
6. Atención del Trabajo de Parto
7. Puerperio y Alumbramiento
8. Lactancia Materna
9. Primeros 1000 Días
10. Ecografía Obstétrica
11. Doppler Obstétrico
12. Hemorragias del Embarazo
13. Placenta Previa y DPPNI
14. Embarazo Ectópico y Mola Hidatiforme
15. Amenaza de Parto Pretérmino
16. Rotura Prematura de Membranas
17. Embarazo Prolongado
18. Restricción del Crecimiento Intrauterino
19. Líquido Amniótico
20. Embarazo Gemelar
21. Diabetes y Embarazo
22. Hipertensión y Embarazo
23. Cardiopatías y Embarazo
24. Hipoxia Fetal Aguda
25. Enfermedad Hemolítica Perinatal
26. Infecciones en el Embarazo
27. IVE/ILE
28. Operación Cesárea
29. Distocias y Fórceps
30. Colestasis Intrahepática y Otras Patologías

---

## How to rebuild the quiz

```bash
bash rebuild.sh
```

This runs `build_html.py` from the quiz-builder skill with the correct arguments.
After rebuilding, commit + push to deploy to GitHub Pages:

```bash
git add Obstetricia_Quiz.html quiz_questions_pool_normalized.json
git commit -m "Update quiz: <description>"
git push
```

---

## How to extract more questions from sources

```bash
# From project root:
python3 scripts/extract_compilado.py
# Output → tmp/questions_compilado_all.json

# Then merge new questions into the bank manually (review for duplicates first)
# Run validate_questions.py only against the NEW questions file,
# NOT with quiz_questions_pool_normalized.json as the output path (that replaces the whole bank).
```

**Warning:** Never run `validate_questions.py questions_new.json quiz_questions_pool_normalized.json` —
the second argument is the OUTPUT path. This will replace the entire bank with only the new questions.
Merge manually or use `--existing` flag to append.

---

## Pending improvements

- [ ] Process 4 unprocessed choices PDFs in `sources/choices/` (may contain hundreds of new Qs)
- [ ] Generate questions from `sources/slides/` (currently extracted but 0 questions generated)
- [ ] Resolve 3 remaining `needs_review` questions (IDs 396, 488, 507)
- [ ] Re-examine `sources/choices/Parcial (1)-1.pdf` (has answer key but questions illegible)

---

## Quiz builder skill

Located at: `~/.claude/plugins/local/quiz-builder/skills/quiz-builder/`

Key scripts:
- `scripts/build_html.py` — builds the HTML app from bank + template
- `scripts/validate_questions.py` — deduplicates and validates a question batch
- `references/html-template.md` — Vue.js quiz app template
- `references/question-schema.md` — question object schema and generation rules
