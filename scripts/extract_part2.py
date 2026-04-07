import PyPDF2

file_path = 'Apunte Sol Modificado.pdf'
output_txt = 'apunte_sol_text_2.txt'

# Rangos de interés basados en el mapeo previo:
# 60-68: Hemorragias 1ra mitad
# 96-114: Infecciones y Diabetes
# 117-127: HTA/Preeclampsia
# 147-174: RCIU, RPM, Parto Pretérmino

pages_to_extract = list(range(59, 68)) + list(range(95, 114)) + list(range(116, 127)) + list(range(146, 174))

try:
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        with open(output_txt, 'w', encoding='utf-8') as out:
            for i in pages_to_extract:
                if i < len(reader.pages):
                    page = reader.pages[i]
                    text = page.extract_text()
                    if text:
                        out.write(f'\n--- Página {i+1} ---\n')
                        out.write(text + '\n')
    print("Texto de la segunda mitad extraído con éxito.")
except Exception as e:
    print(f'Error: {e}')
