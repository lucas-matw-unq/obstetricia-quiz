import PyPDF2
import json

file_path = 'Apunte Sol Modificado.pdf'
output_txt = 'apunte_sol_map.txt'

try:
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        print(f'Total de páginas: {total_pages}')
        
        with open(output_txt, 'w', encoding='utf-8') as out:
            out.write(f'ESTRUCTURA DE {file_path}\n')
            out.write(f'Total de páginas: {total_pages}\n\n')
            
            # Extraemos una muestra de las primeras 100 páginas para mapear temas
            # (Si es necesario extraeremos más luego)
            for i in range(min(100, total_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                if text:
                    # Guardamos las primeras 2 líneas de cada página para el índice
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    header = " | ".join(lines[:3])
                    out.write(f'Pág {i+1}: {header}\n')
except Exception as e:
    print(f'Error: {e}')
