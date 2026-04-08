#!/usr/bin/env python3
"""
extract_new_choices.py
Extracts questions from:
  - sources/choices/Super compilado obstetricia done.pdf  (88 Qs, 6-option format)
  - sources/choices/Obstetricia CHOICES pdf-1.pdf         (85 Qs, same format)
  - sources/choices/Compilado_de_examenes_parciales_10_preguntas_UDH_Clínicas.pdf

Only outputs questions NOT already in quiz_questions_pool_normalized.json
(checked by question text similarity).
"""

import re, json
import PyPDF2
from pathlib import Path
from difflib import SequenceMatcher

BANK_PATH = "quiz_questions_pool_normalized.json"
OUTPUT_PATH = "tmp/questions_new_choices.json"

OPTION_RE = re.compile(r'^([a-fA-F])[.)]\s*(.*)', re.DOTALL)
PAGINATION_RE = re.compile(r'^\s*Nueva\s+secci[oó]n\s+\d+\s+p[aá]gina\s+\d+\s*$', re.IGNORECASE)

TOPIC_MAP = {
    "1000 DÍAS": "Primeros 1000 Días",
    "TROFOBLASTO": "Hemorragias del Embarazo",
    "DX DE EMBARAZO": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "CONTROL PRENATAL": "Control Prenatal",
    "ESTÁTICA FETAL": "Estática Fetal",
    "TRABAJO DE PARTO": "Fenómenos del Trabajo de Parto",
    "ATENCIÓN DEL PARTO": "Atención del Trabajo de Parto",
    "ALUMBRAMIENTO": "Puerperio y Alumbramiento",
    "PUERPERIO": "Puerperio y Alumbramiento",
    "LACTANCIA": "Lactancia Materna",
    "ECOGRAFÍA": "Ecografía Obstétrica",
    "DOPPLER": "Doppler Obstétrico",
    "HEMORRAGIA": "Hemorragias del Embarazo",
    "PLACENTA PREVIA": "Placenta Previa y DPPNI",
    "EMBARAZO ECTÓPICO": "Embarazo Ectópico y Mola Hidatiforme",
    "MOLA": "Embarazo Ectópico y Mola Hidatiforme",
    "PRETÉRMINO": "Amenaza de Parto Pretérmino",
    "RPM": "Rotura Prematura de Membranas",
    "EMBARAZO PROLONGADO": "Embarazo Prolongado",
    "RCIU": "Restricción del Crecimiento Intrauterino",
    "LÍQUIDO AMNIÓTICO": "Líquido Amniótico",
    "GEMELAR": "Embarazo Gemelar",
    "DIABETES": "Diabetes y Embarazo",
    "HTA": "Hipertensión y Embarazo",
    "CARDIOPATÍAS": "Cardiopatías y Embarazo",
    "HIPOXIA": "Hipoxia Fetal Aguda",
    "ENFERMEDAD HEMOLÍTICA": "Enfermedad Hemolítica Perinatal",
    "INFECCIONES": "Infecciones en el Embarazo",
    "IVE": "IVE/ILE",
    "CESÁREA": "Operación Cesárea",
    "CESAREA": "Operación Cesárea",
    "DISTOCIAS": "Distocias y Fórceps",
    "FÓRCEPS": "Distocias y Fórceps",
    "COLESTASIS": "Colestasis Intrahepática y Otras Patologías",
    "MODIFICACIONES GRAVÍDICAS": "Modificaciones Gravídicas, Nutrición y Emesis",
}

def get_topic_from_context(text, current_topic):
    """Try to infer topic from question text."""
    t = text.lower()
    if any(w in t for w in ['1000 días', 'epigenética', 'microbiota', 'keklikian']):
        return "Primeros 1000 Días"
    if any(w in t for w in ['colestasis', 'ácidos biliares']):
        return "Colestasis Intrahepática y Otras Patologías"
    if any(w in t for w in ['preeclampsia', 'eclampsia', 'hellp', 'hipertens']):
        return "Hipertensión y Embarazo"
    if any(w in t for w in ['diabetes', 'glucemia', 'insulina', 'glucosa']):
        return "Diabetes y Embarazo"
    if any(w in t for w in ['cesárea', 'cesarea']):
        return "Operación Cesárea"
    if any(w in t for w in ['fórceps', 'forceps', 'distocia']):
        return "Distocias y Fórceps"
    if any(w in t for w in ['hipoxia', 'sufrimiento fetal', 'dips', 'desacelerac']):
        return "Hipoxia Fetal Aguda"
    if any(w in t for w in ['hemolítica', 'rh', 'anti d', 'anti-d']):
        return "Enfermedad Hemolítica Perinatal"
    if any(w in t for w in ['rpm', 'rotura prematura', 'membranas']):
        return "Rotura Prematura de Membranas"
    if any(w in t for w in ['pretérmino', 'parto pretermino', 'uteroinhibic']):
        return "Amenaza de Parto Pretérmino"
    if any(w in t for w in ['placenta previa', 'desprendimiento', 'dppni', 'couvelaire']):
        return "Placenta Previa y DPPNI"
    if any(w in t for w in ['puerperio', 'alumbramiento', 'placenta', 'loq']):
        return "Puerperio y Alumbramiento"
    if any(w in t for w in ['lactancia', 'lactante', 'telómeros', 'amamantar']):
        return "Lactancia Materna"
    if any(w in t for w in ['control prenatal', 'prenatal']):
        return "Control Prenatal"
    if any(w in t for w in ['ecografía', 'ecografia', 'doppler']):
        return "Ecografía Obstétrica"
    if any(w in t for w in ['infección', 'toxoplasma', 'sífilis', 'hiv', 'chagas']):
        return "Infecciones en el Embarazo"
    if any(w in t for w in ['rciu', 'restricción del crecimiento', 'pequeño para']):
        return "Restricción del Crecimiento Intrauterino"
    if any(w in t for w in ['líquido amniótico', 'polihidramnios', 'oligoamnios']):
        return "Líquido Amniótico"
    if any(w in t for w in ['modificaciones gravídicas', 'volemia', 'anemia']):
        return "Modificaciones Gravídicas, Nutrición y Emesis"
    if any(w in t for w in ['aborto', 'ectópico', 'mola', 'trofoblasto']):
        return "Hemorragias del Embarazo"
    if any(w in t for w in ['trabajo de parto', 'dilatación', 'contracciones', 'expulsivo']):
        return "Fenómenos del Trabajo de Parto"
    if any(w in t for w in ['insinuada', 'plano de hodge', 'presentación', 'situación fetal']):
        return "Estática Fetal"
    return current_topic or "Control Prenatal"


def extract_pdf_text(path):
    r = PyPDF2.PdfReader(path)
    pages_text = []
    for page in r.pages:
        text = page.extract_text() or ''
        pages_text.append(text)
    return pages_text


def parse_compilado(pages_text, source_name, file_path):
    """Parse questions from Super/CHOICES1 format: N) question text / a. option"""
    full = '\n'.join(pages_text)
    # Remove pagination artifacts
    lines = [l for l in full.split('\n') if not PAGINATION_RE.match(l)]
    full_clean = '\n'.join(lines)

    Q_RE = re.compile(r'(?m)^\s*(\d+)\s*\)\s+(.+?)(?=\n\s*\d+\s*\)|\Z)', re.DOTALL)
    results = []

    current_topic = "Control Prenatal"

    for m in Q_RE.finditer(full_clean):
        num = int(m.group(1))
        block = m.group(2).strip()

        # Split question text from options
        lines_block = block.split('\n')
        question_lines = []
        options = {}
        current_opt = None

        for line in lines_block:
            line = line.strip()
            if not line:
                continue
            opt_m = OPTION_RE.match(line)
            if opt_m:
                letter = opt_m.group(1).upper()
                current_opt = letter
                options[letter] = opt_m.group(2).strip()
            elif current_opt:
                # continuation of option text
                options[current_opt] += ' ' + line
            else:
                question_lines.append(line)

        question_text = ' '.join(question_lines).strip()
        if not question_text.endswith('?'):
            question_text = question_text.rstrip('.,:') + '?'

        if len(options) < 2:
            continue

        # Infer topic
        topic = get_topic_from_context(question_text + ' '.join(options.values()), current_topic)
        current_topic = topic

        option_list = [options.get(l, '') for l in sorted(options.keys())]

        results.append({
            "question": question_text,
            "options": option_list,
            "correct_index": 0,
            "correct_letter": "A",
            "topic": topic,
            "difficulty": 2,
            "source_info": {
                "source_name": source_name,
                "text_excerpt": f"Pregunta {num} del {source_name}",
                "page_number": None,
                "file_path": file_path
            },
            "metadata": {
                "citation_quality": "low",
                "needs_review": True
            },
            "origin": "existing"
        })

    return results


def parse_udh(pages_text, source_name, file_path):
    """Parse 10-question exams from UDH format: inline text '1- question a- opt b- opt'"""
    full = '\n'.join(pages_text)
    # UDH PDFs have all text inline per page — split on question number starts
    Q_SPLIT = re.compile(r'(?<!\w)(\d{1,2})[\-\.]\s+(?=[¿A-ZÁÉÍÓÚÜÑ])')
    OPTION_SPLIT = re.compile(r'\s+([a-e])[-]\s+')
    results = []
    seen_questions = set()

    parts = Q_SPLIT.split(full)
    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        block = parts[i + 1].strip()

        # Split options inline: 'question  a- opt1  b- opt2 ...'
        opt_split = OPTION_SPLIT.split(block)
        question_text = opt_split[0].strip()
        if not question_text or len(question_text) < 15:
            continue

        options = {}
        for j in range(1, len(opt_split) - 1, 2):
            letter = opt_split[j].upper()
            opt_text = opt_split[j + 1].strip().rstrip('.')
            # Stop if we hit the next question's header
            if re.search(r'\d{1,2}[-\.]\s+[¿A-Z]', opt_text):
                opt_text = opt_text.split(re.search(r'\d{1,2}[-\.]\s+[¿A-Z]', opt_text).group())[0].strip()
            if opt_text:
                options[letter] = opt_text

        if len(options) < 3:
            continue

        if not question_text.endswith('?'):
            question_text = question_text.rstrip('.,:') + '?'

        # Deduplicate within UDH (same question number may appear in multiple exam sets)
        q_key = question_text[:60].lower()
        if q_key in seen_questions:
            continue
        seen_questions.add(q_key)

        topic = get_topic_from_context(question_text + ' '.join(options.values()), "Control Prenatal")
        option_list = [options.get(l, '') for l in sorted(options.keys())]

        results.append({
            "question": question_text,
            "options": option_list,
            "correct_index": 0,
            "correct_letter": "A",
            "topic": topic,
            "difficulty": 2,
            "source_info": {
                "source_name": source_name,
                "text_excerpt": f"Pregunta {num} del {source_name}",
                "page_number": None,
                "file_path": file_path
            },
            "metadata": {
                "citation_quality": "low",
                "needs_review": True
            },
            "origin": "existing"
        })

    return results


def similarity(a, b):
    return SequenceMatcher(None, a[:80].lower(), b[:80].lower()).ratio()


def deduplicate_against_bank(questions, bank_questions, threshold=0.75):
    """Remove questions that are too similar to existing bank questions."""
    bank_texts = [q['question'] for q in bank_questions]
    new_qs = []
    skipped = 0
    for q in questions:
        max_sim = max((similarity(q['question'], bt) for bt in bank_texts), default=0)
        if max_sim < threshold:
            new_qs.append(q)
        else:
            skipped += 1
    return new_qs, skipped


def main():
    bank = json.load(open(BANK_PATH))
    bank_questions = bank['questions']

    all_new = []

    # 1. Super compilado
    print("Processing: Super compilado obstetricia done.pdf")
    pages = extract_pdf_text('sources/choices/Super compilado obstetricia done.pdf')
    qs = parse_compilado(pages, "Super Compilado Obstetricia", "sources/choices/Super compilado obstetricia done.pdf")
    qs_new, skipped = deduplicate_against_bank(qs, bank_questions)
    print(f"  Extracted: {len(qs)} | Already in bank: {skipped} | New: {len(qs_new)}")
    for q in qs_new:
        q['_source_file'] = 'SUPER'
    all_new.extend(qs_new)

    # 2. CHOICES1 - only questions not already covered by SUPER or bank
    print("Processing: Obstetricia CHOICES pdf-1.pdf")
    pages = extract_pdf_text('sources/choices/Obstetricia CHOICES pdf-1.pdf')
    qs = parse_compilado(pages, "Compilado Choice Obstetricia (v1)", "sources/choices/Obstetricia CHOICES pdf-1.pdf")
    # Deduplicate against bank AND super new questions
    combined_bank = bank_questions + all_new
    qs_new2, skipped2 = deduplicate_against_bank(qs, combined_bank)
    print(f"  Extracted: {len(qs)} | Duplicate: {skipped2} | New: {len(qs_new2)}")
    for q in qs_new2:
        q['_source_file'] = 'CHOICES1'
    all_new.extend(qs_new2)

    # 3. UDH
    print("Processing: Compilado_de_examenes_parciales_10_preguntas_UDH_Clínicas.pdf")
    pages = extract_pdf_text('sources/choices/Compilado_de_examenes_parciales_10_preguntas_UDH_Clínicas.pdf')
    qs = parse_udh(pages, "Compilado Exámenes Parciales 10 Preguntas UDH Clínicas", "sources/choices/Compilado_de_examenes_parciales_10_preguntas_UDH_Clínicas.pdf")
    combined_bank2 = bank_questions + all_new
    qs_new3, skipped3 = deduplicate_against_bank(qs, combined_bank2)
    print(f"  Extracted: {len(qs)} | Duplicate: {skipped3} | New: {len(qs_new3)}")
    for q in qs_new3:
        q['_source_file'] = 'UDH'
    all_new.extend(qs_new3)

    print(f"\nTotal new questions: {len(all_new)}")
    print("\nNew questions summary:")
    for q in all_new:
        print(f"  [{q['_source_file']}] {q['question'][:80]} | topic: {q['topic']}")

    # Clean _source_file before saving
    for q in all_new:
        q.pop('_source_file', None)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_new, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
