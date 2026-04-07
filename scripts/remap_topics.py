#!/usr/bin/env python3
"""
remap_topics.py
Remaps topic fields on existing questions to match the official CRONOGRAMA topics.
Does NOT regenerate or modify any other fields.
"""

import json
import re
from datetime import date

INPUT_FILE = "quiz_questions_pool_normalized.json"

# Simple renames and merges
TOPIC_MAP = {
    "Control prenatal": "Control Prenatal",
    "Cardiopatías y embarazo": "Cardiopatías y Embarazo",
    "Hipoxia fetal aguda": "Hipoxia Fetal Aguda",
    "Cesárea": "Cesárea",
    "Hemorragia puerperal": "Hemorragia Puerperal",
    "Fórceps": "Fórceps",
    "Infecciones en el embarazo": "Infecciones en el Embarazo",
    "Trabajo de parto prematuro": "Amenaza de Parto Pretérmino",
    "Preeclampsia/HTA": "Hipertensión Inducida por el Embarazo",
    "Anemia en el embarazo": "Anemia",
    "Diabetes gestacional": "Diabetes y Embarazo",
    "Medicina materno-fetal": "Medicina Materno Fetal",
    "IVE/ILE": "IVE/ILE",
    # Merges
    "Embarazo normal": "Modificaciones Gravídicas, Nutrición y Emesis",
    "Fisiología del embarazo": "Modificaciones Gravídicas, Nutrición y Emesis",
    "Diagnóstico de embarazo": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "Presentaciones fetales": "Diagnóstico de Embarazo y Semiología Obstétrica",
    "Parto normal": "Trabajo de Parto y Parto",
    "Mecanismo de parto": "Trabajo de Parto y Parto",
    "Aborto": "Hemorragias del Embarazo",
}

# Keywords for Ecografía split
PRIMER_TRIMESTRE_KEYWORDS = [
    r"\b1er trimestre\b", r"\bprimer trimestre\b", r"\bNT\b", r"\bnucal\b",
    r"\btraslucencia\b", r"\bCRL\b", r"\bhueso nasal\b", r"\bsemana 1[01234]\b",
    r"\bscreening\b", r"\bcribado\b", r"\bdoppler de ductus\b", r"\btrisomía 21\b",
    r"\btrisomia 21\b", r"\baneuploíd",
]

SEGUNDO_TERCER_KEYWORDS = [
    r"\b2do trimestre\b", r"\b3er trimestre\b", r"\bsegundo trimestre\b",
    r"\btercer trimestre\b", r"\bbiomet", r"\banomali", r"\bmorfológ",
    r"\bperfil biofísico\b", r"\bdoppler\b", r"\bsemana 1[89]\b", r"\bsemana 2\d\b",
    r"\bsemana 3\d\b", r"\bplacenta\b", r"\bpresentación\b",
]


def classify_ecografia(q):
    """Split Ecografía questions into 1er trimestre or 2do/3er trimestre."""
    text = (q.get("question", "") + " " + q.get("source_info", {}).get("text_excerpt", "")).lower()
    # Build combined text including options
    text += " " + " ".join(q.get("options", []))

    score_1 = sum(1 for pat in PRIMER_TRIMESTRE_KEYWORDS if re.search(pat, text, re.IGNORECASE))
    score_23 = sum(1 for pat in SEGUNDO_TERCER_KEYWORDS if re.search(pat, text, re.IGNORECASE))

    if score_1 > score_23:
        return "Screening y Ecografía 1er Trimestre"
    elif score_23 > score_1:
        return "Ecografía 2do y 3er Trimestre"
    else:
        # Default ambiguous to 2do/3er (more common in the course)
        return "Ecografía 2do y 3er Trimestre"


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    remapped = {t: 0 for t in set(TOPIC_MAP.values())}
    remapped["Screening y Ecografía 1er Trimestre"] = 0
    remapped["Ecografía 2do y 3er Trimestre"] = 0
    unknown = []

    for q in questions:
        original = q["topic"]
        if original == "Ecografía":
            new_topic = classify_ecografia(q)
            q["topic"] = new_topic
            remapped[new_topic] += 1
        elif original in TOPIC_MAP:
            q["topic"] = TOPIC_MAP[original]
            remapped[TOPIC_MAP[original]] = remapped.get(TOPIC_MAP[original], 0) + 1
        else:
            unknown.append(original)

    # Report
    print(f"Processed {len(questions)} questions")
    print("\nNew topic distribution:")
    topic_counts = {}
    for q in questions:
        t = q["topic"]
        topic_counts[t] = topic_counts.get(t, 0) + 1
    for t, c in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:3d}  {t}")

    if unknown:
        print(f"\nWARNING: {len(unknown)} questions had unrecognized topics:")
        for u in set(unknown):
            print(f"  - {u}")

    # Update metadata
    data["metadata"]["topics"] = topic_counts
    data["metadata"]["total_questions"] = len(questions)
    data["metadata"]["last_updated"] = str(date.today())

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to {INPUT_FILE}")


if __name__ == "__main__":
    main()
