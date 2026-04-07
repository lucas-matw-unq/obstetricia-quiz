import PyPDF2

file_path = 'Apunte Sol Modificado.pdf'
output_txt = 'apunte_sol_text_1.txt'

try:
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        with open(output_txt, 'w', encoding='utf-8') as out:
            # Extraemos de la pág 3 a la 47 (índice 2 a 46)
            for i in range(2, 47):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    out.write(f'\n--- Página {i+1} ---\n')
                    out.write(text + '\n')
    print("Texto extraído con éxito.")
except Exception as e:
    print(f'Error: {e}')
