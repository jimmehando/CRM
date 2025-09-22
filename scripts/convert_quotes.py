from pathlib import Path
from pypdf import PdfReader

SOURCE_DIR = Path(r'c:/Users/James/Documents/CRM/samples/quotes')
OUTPUT_DIR = Path(r'c:/Users/James/Documents/CRM/samples/quotes_txt')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for pdf_path in sorted(SOURCE_DIR.glob('*.pdf')):
    reader = PdfReader(str(pdf_path))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or '')
    text = '\n'.join(text_parts)
    output_path = OUTPUT_DIR / (pdf_path.stem + '.txt')
    output_path.write_text(text, encoding='utf-8')
    print(f"Wrote {output_path.name} ({len(text)} chars)")
