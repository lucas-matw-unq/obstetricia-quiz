#!/usr/bin/env python3
"""
extract_compilado.py
Extracts ALL questions from 'Compilado todos los choices obstetricia.pdf'.
Questions without a clear correct answer are marked needs_review=True.
"""

import re
import json
import PyPDF2
from pathlib import Path

PDF_PATH = "choices/Compilado todos los choices obstetricia.pdf"
OUTPUT_PATH = "questions_compilado_all.json"

# Topic map: section headers in PDF → official CRONOGRAMA topic names
TOPIC_MAP = {
    "1000 DÍAS": "Modificaciones Gravídicas, Nutrición y Emesis",
    "TROFOBLASTO": "Hemorragias del Embarazo",
    "DX DE EMBARAZO": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "DIAGNÓSTICO DE EMBARAZO": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "CONTROL PRENATAL": "Control Prenatal",
    "ECOGRAFÍA": "Ecografía 2do y 3er Trimestre",
    "TRABAJO DE PARTO": "Trabajo de Parto y Parto",
    "PRESENTACIÓN PELVIANA": "Trabajo de Parto y Parto",
    "DISTOCIAS": "Trabajo de Parto y Parto",
    "DICTOSIAS": "Trabajo de Parto y Parto",
    "ALUMBRAMIENTO": "Puerperio y Alumbramiento",
    "PLACENTA": "Hemorragias del Embarazo",
    "CESÁREA": "Cesárea",
    "PUERPERIO": "Puerperio y Alumbramiento",
    "EMBARAZO GEMELAR": "Embarazo Gemelar",
    "LÍQUIDO AMNIÓTICO": "Líquido Amniótico",
    "EMBARAZO PROLONGADO": "Control Prenatal",
    "PRETÉRMINO": "Amenaza de Parto Pretérmino",
    "APP": "Amenaza de Parto Pretérmino",
    "INFECCIONES": "Infecciones en el Embarazo",
    "HIPERÉMESIS": "Modificaciones Gravídicas, Nutrición y Emesis",
    "DIABETES": "Diabetes y Embarazo",
    "DBT": "Diabetes y Embarazo",
    "ENFERMEDAD HEMOLÍTICA": "Enfermedad Hemolítica Feto-Neonatal",
    "RCIU": "Restricción del Crecimiento Intrauterino",
    "SFA": "Hipoxia Fetal Aguda",
    "HIPOXIA": "Hipoxia Fetal Aguda",
    "TERATOGÉNICOS": "Modificaciones Gravídicas, Nutrición y Emesis",
    "HTA": "Hipertensión Inducida por el Embarazo",
    "HIPERTENSIÓN": "Hipertensión Inducida por el Embarazo",
    "HEMORRAGÍAS DEL 2°": "Hemorragias del Embarazo",
    "HEMORRAGÍAS DEL 1°": "Hemorragias del Embarazo",
    "MODIFICACIONES GRAVÍDICAS": "Modificaciones Gravídicas, Nutrición y Emesis",
    "ESTÁTICA FETAL": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "FÓRCEPS": "Fórceps",
    "FORCEPS": "Fórceps",
    "ANEMIA": "Anemia",
    "LACTANCIA": "Lactancia",
    "IVE": "IVE/ILE",
    "ILE": "IVE/ILE",
    "CARDIOPATÍAS": "Cardiopatías y Embarazo",
    "RPM": "Rotura Prematura de Membranas",
    "ROTURA PREMATURA": "Rotura Prematura de Membranas",
    "COLESTASIS": "Colestasis Intrahepática Gestacional",
    "DOPPLER": "Doppler Materno Fetal y Monitoreo",
    "TROMBOFILIA": "Trombofilias",
    "HEMORRAGIA PUERPERAL": "Hemorragia Puerperal",
    "EPIGENÉTICA": "Modificaciones Gravídicas, Nutrición y Emesis",
    "MICROBIOTA": "Modificaciones Gravídicas, Nutrición y Emesis",
}

# Header patterns (all-caps lines that indicate topic changes)
HEADER_RE = re.compile(
    r'^([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ\s/\(\)°º\-]{3,50})\s*$',
    re.MULTILINE
)

# Correct-answer markers
ANSWER_MARKERS = [
    r'\bESTA\b', r'ESTA\?', r'SALE ESTA', r'CORRECTA\b', r'\bCORRECTO\b',
    r'ESTA ES', r'CREO QUE ESTA', r'YO PONDRÍA ESTA',
]
MARKER_RE = re.compile('|'.join(ANSWER_MARKERS), re.IGNORECASE)

# RTA: pattern
RTA_RE = re.compile(r'RTA\s*[:=]\s*(.+)', re.IGNORECASE)

LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Option letter: a-h, uppercase or lowercase, followed by ) or . (with or without space)
OPTION_LETTER_RE = re.compile(r'^([a-hA-H])[).]\s*(.*)')

# Detect a numbered question start
Q_START_RE = re.compile(r'^\s*(\d+)\)\s+(.+)', re.MULTILINE)

# Pagination artifacts to strip (Word section/page markers embedded in PDF text)
PAGINATION_RE = re.compile(r'^\s*Nueva secci[oó]n\s+\d+\s+p[aá]gina\s+\d+\s*$', re.IGNORECASE)


def extract_text(pdf_path):
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
    return pages


def detect_topic(text_block, current_topic):
    """Detect if this text block starts a new topic section."""
    for line in text_block.split('\n'):
        line = line.strip()
        for key, val in TOPIC_MAP.items():
            if line.upper() == key.upper() or re.match(rf'^{re.escape(key)}\s*$', line, re.IGNORECASE):
                return val
    return current_topic


def normalize_option_text(text):
    """Clean up option text."""
    # Remove answer markers
    text = MARKER_RE.sub('', text)
    # Remove parenthetical topic labels like "(mediato)", "(es de poli)"
    text = re.sub(r'\s*\([^)]{1,30}\)\s*', ' ', text)
    # Clean trailing punctuation/spaces
    text = text.strip().rstrip('.')
    return text.strip()


def has_answer_marker(text):
    return bool(MARKER_RE.search(text))


def is_option_line(line):
    """Return True if line looks like an option (a. / a) / a.Text style)."""
    return bool(OPTION_LETTER_RE.match(line.strip()))

def is_section_header(line):
    """Return True if line is an all-caps section header (not a topic, just a divider)."""
    s = line.strip()
    return (s.upper() == s and len(s) > 5 and
            not any(c.isdigit() for c in s) and
            not OPTION_LETTER_RE.match(s))

def split_same_line_options(opt_letter, opt_text):
    """
    If an option line contains multiple options (e.g. 'a. 7 días. b. 20 días'),
    split them. Returns list of (letter, text) tuples.
    """
    result = [(opt_letter, opt_text)]
    # Look for embedded next option letter within the text
    # Pattern: space + [b-h]. + space
    sub = re.split(r'\s+([b-hB-H])\.\s+', opt_text)
    if len(sub) > 1:
        result = [(opt_letter, sub[0].strip())]
        for i in range(1, len(sub), 2):
            if i + 1 < len(sub):
                result.append((sub[i].upper(), sub[i+1].strip()))
    return result

def collect_options(lines, j):
    """Collect option lines starting at index j. Returns (options, rta_text, next_j)."""
    options = []
    rta_text = None

    while j < len(lines):
        opt_line = lines[j].strip()

        # Skip pagination artifacts
        if PAGINATION_RE.match(opt_line):
            j += 1
            continue

        # Check for RTA line
        rta_match = RTA_RE.match(opt_line)
        if rta_match:
            rta_text = rta_match.group(1).strip()
            j += 1
            continue

        # Check for option line (a-h, with or without space after period)
        opt_match = OPTION_LETTER_RE.match(opt_line)
        if opt_match:
            opt_letter = opt_match.group(1).upper()
            opt_text = opt_match.group(2).strip()

            # Collect multi-line option text
            k = j + 1
            while k < len(lines):
                cont = lines[k].strip()
                if PAGINATION_RE.match(cont):
                    k += 1
                    continue
                if is_option_line(cont):
                    break
                if re.match(r'^\d{1,3}\)\s+', cont):
                    break
                if not cont:
                    break
                if is_section_header(cont):
                    break
                opt_text += ' ' + cont
                k += 1

            # Handle same-line options (e.g. "a. 7 días. b. 20 días")
            for letter, text in split_same_line_options(opt_letter, opt_text):
                options.append({
                    'letter': letter,
                    'text': text,
                    'has_marker': has_answer_marker(text),
                })
            j = k
            continue

        # Stop if we hit another numbered question
        if re.match(r'^\d{1,3}\)\s+', opt_line):
            break

        # Stop on section header (topic change)
        if is_section_header(opt_line):
            break

        # Allow up to 2 blank lines within options (handles page breaks with trailing blanks)
        if not opt_line:
            blank_count = 0
            k = j
            while k < len(lines) and not lines[k].strip():
                blank_count += 1
                k += 1
            if blank_count <= 2 and k < len(lines) and is_option_line(lines[k].strip()):
                j = k  # skip the blanks, continue with next option
                continue
            elif blank_count > 0:
                break  # too many blanks or no option follows

        j += 1

    return options, rta_text, j


def parse_questions_from_text(full_text):
    """
    Parse questions from the full extracted text.
    Returns list of raw question dicts.
    Handles:
    - Numbered questions: N) text
    - Unnumbered questions: text ending with ? or : followed by options
    - Options with no space after period: a.Text
    - Options G and H
    - Same-line options: a. text. b. text
    - Pagination artifacts: "Nueva sección X página Y"
    """
    questions = []

    # Pre-filter: remove pagination artifacts line by line
    clean_lines = []
    for line in full_text.split('\n'):
        if not PAGINATION_RE.match(line.strip()):
            clean_lines.append(line)
    lines = clean_lines

    current_topic = "Control Prenatal"
    i = 0
    seen_positions = set()  # avoid re-parsing the same line as question start

    while i < len(lines):
        line = lines[i].strip()

        # Detect topic header
        for key, val in TOPIC_MAP.items():
            if line.upper().strip() == key.upper() or (len(line) > 3 and line.upper() == key):
                current_topic = val
                break

        # ── NUMBERED question: "N) text" ──────────────────────────────────
        q_match = re.match(r'^\s*(\d{1,3})\)\s+(.+)', line)

        if q_match and i not in seen_positions:
            seen_positions.add(i)
            q_num = q_match.group(1)
            q_text = q_match.group(2).strip()

            # Collect multi-line question text
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if PAGINATION_RE.match(next_line):
                    j += 1
                    continue
                # Stop if we hit an option line (including no-space format)
                if is_option_line(next_line):
                    break
                if re.match(r'^\d{1,3}\)\s+', next_line):
                    break
                if is_section_header(next_line):
                    break
                if next_line:
                    q_text += ' ' + next_line
                j += 1

            options, rta_text, j = collect_options(lines, j)

            if options and len(options) >= 2:
                questions.append({
                    'num': int(q_num),
                    'question': q_text.strip(),
                    'options': options,
                    'rta': rta_text,
                    'topic': current_topic,
                    'numbered': True,
                })

            i = j

        # ── UNNUMBERED question: text ending with ? or : + option lines ───
        elif (not q_match and
              len(line) > 20 and
              (line.endswith('?') or line.endswith(':') or line.endswith('una:') or 'seleccione' in line.lower()) and
              not is_option_line(line) and
              not is_section_header(line) and
              i not in seen_positions):
            # Peek: next non-empty line should be an option
            j = i + 1
            # Collect possible multi-line question text
            q_text = line
            while j < len(lines):
                next_line = lines[j].strip()
                if PAGINATION_RE.match(next_line):
                    j += 1
                    continue
                if is_option_line(next_line):
                    break
                if re.match(r'^\d{1,3}\)\s+', next_line):
                    break  # hit a numbered question without finding options
                if is_section_header(next_line):
                    break
                if next_line:
                    q_text += ' ' + next_line
                else:
                    break  # blank line before options → probably not a question
                j += 1

            options, rta_text, j = collect_options(lines, j)

            if options and len(options) >= 2:
                seen_positions.add(i)
                questions.append({
                    'num': None,
                    'question': q_text.strip(),
                    'options': options,
                    'rta': rta_text,
                    'topic': current_topic,
                    'numbered': False,
                })
            i += 1  # advance only 1 even if no options (don't skip to j)

        else:
            i += 1

    return questions


def reassign_topic_by_content(question_text, options_text, current_topic):
    """
    Override topic assignment based on question content keywords.
    Only overrides if we find a strong content signal.
    """
    combined = (question_text + ' ' + options_text).lower()

    content_rules = [
        (r'\bdesprendimiento normoplacentario\b|\bdppni\b|\bdpni\b', 'Hemorragias del Embarazo'),
        (r'\bplacenta previa\b', 'Hemorragias del Embarazo'),
        (r'\batonía uterina\b|\bpost.?alumbramiento\b|\bmaniobra de dublin\b|\bmaniobra de küstner\b|\bpuerperio inmediato\b|\binvolución uterina\b|\bloquios\b', 'Puerperio y Alumbramiento'),
        (r'\baborto incompleto\b|\baborto espontáneo\b|\btrofoblasto\b|\bmola\b', 'Hemorragias del Embarazo'),
        (r'\bhellp\b|\beclampsia\b|\bpreeclampsia\b|\bhipertensión.*embarazo\b|\bsulfato de magnesio\b', 'Hipertensión Inducida por el Embarazo'),
        (r'\bhipoxia fetal\b|\bsufrimiento fetal\b|\bdip ii\b|\bdesaceleraciones tardías\b|\brecuperación intraútero\b', 'Hipoxia Fetal Aguda'),
        (r'\benfermedad hemolítica\b|\bisoinmuniz\b|\brh negativa?\b.*sensibiliz|\banticuerpos.*rh\b', 'Enfermedad Hemolítica Feto-Neonatal'),
        (r'\bdiabetes gestacional\b|\bdbt.*embarazo\b|\binsuliniz\b|\bhidratos de carbono.*embarazada\b|\bglucemia.*ayunas.*embarazo\b', 'Diabetes y Embarazo'),
        (r'\brpm\b|\brotura prematura de membranas\b|\bcorioamnionitis\b|\bperiodo de latencia\b', 'Rotura Prematura de Membranas'),
        (r'\brciu\b|\bcrecimiento intrauterino restringi\b|\bpequeño para edad gestacional\b', 'Restricción del Crecimiento Intrauterino'),
        (r'\btoxoplasmosis\b|\bvdrl\b|\bsífilis.*embarazo\b|\bhiv.*embarazo\b|\bstreptococo.*grupo b\b|\begb\b', 'Infecciones en el Embarazo'),
        (r'\bparto pretérmino\b|\bamenaza de parto prematuro\b|\bmaduración pulmonar\b|\bbetametasona\b|\bdexametasona.*fetal\b|\bapp\b.*contraccion|\buteroinhibi', 'Amenaza de Parto Pretérmino'),
        (r'\bcesárea\b|\bpfannenstiel\b|\bhisterotomía\b', 'Cesárea'),
        (r'\bfórceps\b|\bkjelland\b|\bsimpson\b.*fórceps\b', 'Fórceps'),
        (r'\becografía.*trimestre\b|\bbiometría fetal\b|\bdbp\b|\bca fetal\b', 'Ecografía 2do y 3er Trimestre'),
        (r'\bscreening.*1er trimestre\b|\btraslucencia nucal\b|\bnt\b.*semana 1[0-3]\b|\bscreening.*cromosóm', 'Screening y Ecografía 1er Trimestre'),
        (r'\bhiperémesis\b|\bhiperemesis\b', 'Modificaciones Gravídicas, Nutrición y Emesis'),
        (r'\b1000 días\b|\bepigenétic\b|\bmicrobiota\b|\btelomeros\b', 'Modificaciones Gravídicas, Nutrición y Emesis'),
        (r'\bcontrol prenatal\b|\bembarazo de alto riesgo\b|\bconsulta.*embarazada\b', 'Control Prenatal'),
        (r'\bdoppler.*umbilical\b|\barteria cerebral media\b|\bductus venoso\b|\bmonitoreo.*fetal\b|\bnst\b|\bip de arteria uterina\b|\bip umbilical\b', 'Doppler Materno Fetal y Monitoreo'),
        (r'\bteratogén\b|\bteratogenos\b|\bteratogenico\b', 'Modificaciones Gravídicas, Nutrición y Emesis'),
        (r'\bfibronectina fetal\b|\bcuello uterino.*trabajo de parto\b|\bmodificaciones cervicales\b', 'Amenaza de Parto Pretérmino'),
        (r'\btromboflebitis pélvica\b|\btromboflebitis.*ovár\b', 'Puerperio y Alumbramiento'),
        (r'\bglobulos blancos.*embarazada\b|\bleucocitos.*embarazo\b|\bleucocitosis.*embarazo\b|\bhematocrito.*embarazada\b|\bhematocrito.*embarazo\b', 'Modificaciones Gravídicas, Nutrición y Emesis'),
        (r'\blactancia materna\b|\bmastitis\b|\bocitocina.*lactancia\b', 'Lactancia'),
        (r'\banemia.*embarazo\b|\bhemoglobin.*embarazo\b', 'Anemia'),
        (r'\bgemela[r]?\b|\bbicorial\b|\bmonocorial\b', 'Embarazo Gemelar'),
        (r'\bcolestasis intrahepática\b|\bácidos biliares.*embarazo\b|\bprurito.*embarazo\b', 'Colestasis Intrahepática Gestacional'),
        (r'\bive\b|\bile\b|\binterrupción.*embarazo\b|\bley 27.610\b', 'IVE/ILE'),
        (r'\bcardiopatía.*embarazo\b|\bclasificación.*aha.*embarazo\b', 'Cardiopatías y Embarazo'),
        (r'\bdiagnóstico de certeza.*embarazo\b|\bhcg\b.*embarazo\b|\bsigno de hegar\b|\bsigno de chadwick\b', 'Diagnóstico de Embarazo y Semiología Obstétrica'),
        (r'\bpresentación cefálica\b|\bplano de hodge\b|\bestática fetal\b|\bmaniobra de leopold\b', 'Diagnóstico de Embarazo y Semiología Obstétrica'),
        (r'\blíquido amniótico\b|\bila\b.*polihidramnios\b|\boligoamnios\b|\bpolihidramnios\b', 'Líquido Amniótico'),
        (r'\btrombofilias?\b|\bsaf\b|\bsíndrome antifosfolípido\b|\bheparina.*profilaxis\b', 'Trombofilias'),
        (r'\bpuerperio\b', 'Puerperio y Alumbramiento'),
        (r'\bhemorragia puerperal\b|\batonía\b', 'Hemorragia Puerperal'),
    ]

    for pattern, topic in content_rules:
        if re.search(pattern, combined, re.IGNORECASE):
            return topic

    return current_topic


def determine_correct_index(q):
    """
    Try to determine the correct answer index.
    Returns (index, confidence) where confidence is 'high' or 'unknown'.
    ESTA markers are unreliable (students often annotate wrong answers),
    so we only use them if explicitly labelled "RTA:" which is more reliable.
    """
    options = q['options']

    # Only trust explicit "RTA:" answers
    if q.get('rta'):
        rta = q['rta'].lower().strip()
        for i, o in enumerate(options):
            opt_clean = normalize_option_text(o['text']).lower()
            if len(rta) > 8 and (rta in opt_clean or opt_clean.startswith(rta[:min(len(rta), 20)])):
                return i, 'high'

    return 0, 'unknown'  # placeholder — will be filled in via review


def build_question_objects(raw_qs):
    """Convert raw parsed questions to bank schema."""
    result = []

    for raw in raw_qs:
        opts = raw['options']
        if len(opts) < 2 or len(opts) > 6:
            continue

        q_text = raw['question'].strip()
        if len(q_text) < 20:
            continue
        # Skip if question text looks like garbage
        if re.match(r'^[^a-záéíóúñüA-ZÁÉÍÓÚÑÜ]+$', q_text):
            continue
        # Skip student annotation noise
        if re.search(r'(a{3,}|o{3,}|e{3,}|u{3,}|noséeee|ayuda{2,}|nosee{2,}|\?{3,})', q_text, re.IGNORECASE):
            continue
        # For unnumbered questions: require that the question starts with a capital letter or ¿
        # to filter out page-continuation fragments that start mid-sentence
        if not raw.get('numbered', True):
            if not re.match(r'^[¿A-ZÁÉÍÓÚÑÜ]', q_text):
                continue
            # Also filter likely fragments: very short questions or ones starting with verb fragments
            fragment_starts = r'^(cómo|cuál|cuáles|del|de la|de las|de los|en un|en una|durante|genera|a fin|perfil para|que se|que es|que le|informa |desde|desde el|desde la|de parto|contracciones|oclusiva|inmediata|alteración|normoplacentario)'
            if re.match(fragment_starts, q_text, re.IGNORECASE):
                continue

        # Clean option texts
        clean_opts = [normalize_option_text(o['text']) for o in opts]

        # Reassign topic using question+options content (more reliable than section headers)
        raw['topic'] = reassign_topic_by_content(q_text, ' '.join(clean_opts), raw['topic'])
        # Skip if any option is too short or identical
        if any(len(o) < 2 for o in clean_opts):
            continue
        if len(set(o.lower() for o in clean_opts)) < len(clean_opts):
            continue

        # Determine correct answer
        correct_idx, confidence = determine_correct_index(raw)
        if correct_idx >= len(clean_opts):
            correct_idx = 0
            confidence = 'unknown'

        needs_review = confidence == 'unknown'

        obj = {
            "question": q_text if q_text.endswith('?') else q_text,
            "options": clean_opts,
            "correct_index": correct_idx,
            "correct_letter": LETTERS[correct_idx],
            "topic": raw['topic'],
            "difficulty": 2,
            "source_info": {
                "source_name": "Compilado choices Obstetricia",
                "text_excerpt": q_text[:150],
                "page_number": None,
                "file_path": "choices/Compilado todos los choices obstetricia.pdf"
            },
            "origin": "existing",
            "metadata": {
                "citation_quality": "medium" if not needs_review else "low",
                "needs_review": needs_review,
                "answer_confidence": confidence,
            }
        }
        result.append(obj)

    return result


def deduplicate(questions, similarity_threshold=0.85):
    """Remove near-duplicate questions (same text)."""
    from difflib import SequenceMatcher

    kept = []
    seen_texts = []
    removed = 0

    for q in questions:
        q_text = q['question'].lower()
        is_dup = False
        for existing_text in seen_texts:
            ratio = SequenceMatcher(None, q_text, existing_text).ratio()
            if ratio >= similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(q)
            seen_texts.append(q_text)
        else:
            removed += 1

    return kept, removed


def main():
    print(f"Reading {PDF_PATH}...")
    pages = extract_text(PDF_PATH)
    full_text = '\n'.join(pages)
    print(f"  {len(pages)} pages, {len(full_text):,} chars")

    print("Parsing questions...")
    raw_qs = parse_questions_from_text(full_text)
    print(f"  Found {len(raw_qs)} raw question blocks")

    print("Building question objects...")
    questions = build_question_objects(raw_qs)
    print(f"  Built {len(questions)} question objects")

    print("Deduplicating...")
    questions, removed = deduplicate(questions)
    print(f"  Removed {removed} duplicates → {len(questions)} remaining")

    # Stats
    high = sum(1 for q in questions if q['metadata']['answer_confidence'] == 'high')
    low  = sum(1 for q in questions if q['metadata']['answer_confidence'] == 'low')
    unk  = sum(1 for q in questions if q['metadata']['answer_confidence'] == 'unknown')
    print(f"\n  Answer confidence: high={high}, low={low}, unknown={unk}")

    topic_counts = {}
    for q in questions:
        t = q['topic']
        topic_counts[t] = topic_counts.get(t, 0) + 1
    print("\n  By topic:")
    for t, c in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"    {c:3d}  {t}")

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
