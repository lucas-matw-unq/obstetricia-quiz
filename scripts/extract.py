import PyPDF2

with open('Diapos extras/19. 1CESAREA. DRA. CEPEDA.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    with open('cesarea.txt', 'w', encoding='utf-8') as out:
        for i, page in enumerate(reader.pages):
            out.write(f'\n--- Página {i+1} ---\n')
            text = page.extract_text()
            if text:
                out.write(text + '\n')
