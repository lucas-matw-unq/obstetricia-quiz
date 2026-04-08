#!/usr/bin/env python3
"""
fix_topics.py
Apply content-based topic reassignments to quiz_questions_pool_normalized.json.
Uses keyword scoring; applies only high-confidence reassignments.
"""

import json
from pathlib import Path
from collections import Counter

BANK_PATH = "quiz_questions_pool_normalized.json"

TOPIC_SIGNALS = {
    'Hipertensión y Embarazo': [
        'preeclampsia','eclampsia','hellp','hipertens','labetalol',
        'magnesio','proteinuria','alfa metil','alfametil',
        'antihipertensiv','crisis hipertensiva','hta ','sulfato de magnesio',
        'presión arterial alta','tensión arterial elevada',
    ],
    'Operación Cesárea': [
        'cesárea','cesarea','pfannenstiel','munro kerr','histerotomía',
        'indicación de cesárea','indicacion de cesarea',
    ],
    'Distocias y Fórceps': [
        'fórceps','forceps','distocia de hombros','vacío obstétrico',
        'ventosa obstétrica','bracht','presentación pelviana','podálica',
        'maniobra de bracht','distocia de rotación',
    ],
    'Hipoxia Fetal Aguda': [
        'hipoxia fetal','sufrimiento fetal','dips','desacelerac',
        'bradicardia fetal','acidosis fetal','monitoreo fetal',
        'cardiotocografía','ctg','registro cardiotocográfico',
    ],
    'Enfermedad Hemolítica Perinatal': [
        'hemolítica','enfermedad hemolítica','incompatibilidad rh',
        'anti d','anti-d','isoinmunización','coombs','eritroblastosis',
    ],
    'Rotura Prematura de Membranas': [
        'rotura prematura','rpm','membranas rotas','amnionitis',
        'corioamnionitis','oligoamnios por rpm','test de arborización',
    ],
    'Amenaza de Parto Pretérmino': [
        'pretérmino','parto prematuro','uteroinhibic','tocolítico',
        'ritodrina','atosiban','nifedipina tocolítica','corticoides fetales',
        'betametasona madurez','maduracion pulmonar',
    ],
    'Puerperio y Alumbramiento': [
        'puerperio','alumbramiento','involución uterina','loquios',
        'hemorragia post parto','atonía uterina','retención placentaria',
        'mastitis','subinvolución','cuarta etapa del parto',
        'días de puerperio','endometritis puerperal',
    ],
    'Lactancia Materna': [
        'lactancia','amamantar','leche materna','calostro',
        'prolactina','oxitocina lactancia','tetada','succión',
        'mastitis lactacional',
    ],
    'Ecografía Obstétrica': [
        'ecografía','ecografia','ultrasonido obstétrico',
        'longitud cráneo-caudal','lcc','biometría fetal',
        'screening 1er trimestre','translucencia nucal','tn ',
        'pliegue nucal','nasal bone','marcador ecográfico',
    ],
    'Doppler Obstétrico': [
        'doppler','arteria uterina','arteria umbilical','diastole ausente',
        'diastole reversa','ip ','ir ','pulsatilidad','velocimetría doppler',
        'arteria cerebral media','acm ','ductus venoso',
    ],
    'Diabetes y Embarazo': [
        'diabetes','glucemia','insulina','glucosa','hba1c',
        'tolerancia oral a la glucosa','tog ','hipoglucemia',
        'macrosomía','diabetes gestacional',
    ],
    'Cardiopatías y Embarazo': [
        'cardiopatía','cardíaco','insuficiencia cardíaca','estenosis mitral',
        'clase funcional','nyha','cardiopatía materna','valvulopatía',
        'soplo cardíaco','arritmia','pericarditis',
    ],
    'Infecciones en el Embarazo': [
        'toxoplasma','sífilis','hiv','chagas','rubeola','citomegalovirus',
        'cmv','herpes','listeria','varicela','parvovirus','torch',
        'infección','vdrl','treponema','streptococcus agalactiae',
        'estreptococo grupo b','egb',
    ],
    'Restricción del Crecimiento Intrauterino': [
        'rciu','restricción del crecimiento','pequeño para la edad',
        'peg ','crecimiento intrauterino retard','feto pequeño',
        'percentil 10','doppler en rciu',
    ],
    'Líquido Amniótico': [
        'líquido amniótico','polihidramnios','oligoamnios','ila ','ila>',
        'índice de líquido amniótico','amniocentesis','bolsillo mayor',
    ],
    'Embarazo Gemelar': [
        'gemelar','gemelaridad','bicorial','monocorial','biamniót',
        'monoamniót','ttts','síndrome de transfusión feto fetal',
        'gemelar monocorial','embarazo múltiple','bigeminar',
    ],
    'Colestasis Intrahepática y Otras Patologías': [
        'colestasis','ácidos biliares','prurito gestacional',
        'colestasis intrahepática','ácido ursodesoxicólico','udca',
        'hepatopatía','esteatosis','cirrosis',
    ],
    'Hemorragias del Embarazo': [
        'aborto','ectópico','mola hidatiforme','enfermedad trofoblástica',
        'trofoblasto','metrotrexato','salpingectomía','legrado',
        'metrorragia','sangrado del primer trimestre',
    ],
    'Placenta Previa y DPPNI': [
        'placenta previa','desprendimiento de placenta','dppni',
        'couvelaire','abruptio placentae','hematoma retroplacentario',
        'placenta oclusiva','inserción placentaria',
    ],
    'Control Prenatal': [
        'control prenatal','visita prenatal','primera consulta',
        'semanas de gestación','fum ','fecha probable de parto',
        'altura uterina','maniobras de leopold','antropometría materna',
    ],
    'Diagnóstico de Embarazo y Semiología Obstétrica': [
        'diagnóstico de embarazo','test de embarazo','hcg ','beta hcg',
        'signo de hegar','signo de piskacek','signo de goodell',
        'latidos fetales','auscultación fetal',
    ],
    'Atención del Trabajo de Parto': [
        'trabajo de parto','dilatación','borramiento','contracciones',
        'expulsivo','período expulsivo','episiotomía','episiorrafia',
        'atención del parto','manejo activo del alumbramiento',
        'oxitocina en el parto','conducción del parto','inducción',
    ],
    'Modificaciones Gravídicas, Nutrición y Emesis': [
        'modificaciones','adaptación materna','volemia','hemodilución',
        'náuseas','vómitos del embarazo','hiperemesis gravídica',
        'nutrición materna','ganancia de peso','ácido fólico','hierro',
        'anemia','suplementación','vitamina',
    ],
    'IVE/ILE': [
        'ive ','ile ','interrupción voluntaria','interrupción legal',
        'aborto legal','misoprostol','mifepristona',
    ],
}

# False positives — keep their current topic unchanged
KEEP_CURRENT = {283, 85, 92, 132, 193}

# Manual overrides (algorithm suggested wrong topic → correct this)
OVERRIDES = {
    250: 'Restricción del Crecimiento Intrauterino',   # not Doppler
    316: 'Colestasis Intrahepática y Otras Patologías', # not HTA
}


def score(text, signals):
    text_l = text.lower()
    return sum(1 for kw in signals if kw in text_l)


def best_topic(text):
    scores = {t: score(text, sigs) for t, sigs in TOPIC_SIGNALS.items()}
    best = max(scores, key=scores.get)
    return best, scores[best]


def main():
    bank = json.load(open(BANK_PATH))
    questions = bank['questions']

    reassigned = []
    kept = []

    for q in questions:
        qid = q['id']
        current = q['topic']
        full_text = q['question'] + ' ' + ' '.join(q.get('options', []))

        # Manual keep
        if qid in KEEP_CURRENT:
            kept.append((qid, current, current, 'KEEP_CURRENT'))
            continue

        # Manual override
        if qid in OVERRIDES:
            new_topic = OVERRIDES[qid]
            if new_topic != current:
                reassigned.append((qid, current, new_topic, 'OVERRIDE'))
                q['topic'] = new_topic
            continue

        # Auto: only reassign when current topic scores 0 and best scores ≥ 2
        current_score = score(full_text, TOPIC_SIGNALS.get(current, []))
        bt, bt_score = best_topic(full_text)

        if current_score == 0 and bt_score >= 2 and bt != current:
            reassigned.append((qid, current, bt, f'auto(0→{bt_score})'))
            q['topic'] = bt

    print(f"\nReassigned: {len(reassigned)}")
    print(f"Kept (false positive overrides): {len(kept)}")
    print(f"\nDetail:")
    for qid, old, new, reason in reassigned:
        print(f"  ID {qid:4d}  [{reason}]  {old} → {new}")

    # Recount topics
    topic_counts = Counter(q['topic'] for q in questions)
    bank['metadata']['topics'] = dict(sorted(topic_counts.items()))
    bank['metadata']['total_questions'] = len(questions)

    with open(BANK_PATH, 'w', encoding='utf-8') as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Saved {len(questions)} questions to {BANK_PATH}")
    print("\nFinal topic distribution:")
    for t, c in sorted(topic_counts.items()):
        print(f"  {c:3d}  {t}")


if __name__ == '__main__':
    main()
