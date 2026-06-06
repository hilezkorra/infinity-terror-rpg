import os
import glob
import fitz

pdf_dir = r"C:\laragon\www\terror-infinity"
out_dir = r"C:\laragon\www\terror-infinity-rpg\novel-md"
os.makedirs(out_dir, exist_ok=True)

pdfs = sorted(glob.glob(os.path.join(pdf_dir, "*.pdf")))
print(f"Found {len(pdfs)} PDFs")

for pdf_path in pdfs:
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(out_dir, f"{base}.md")
    print(f"Processing: {base}...")
    try:
        doc = fitz.open(pdf_path)
        total = len(doc)
        lines = []
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                lines.append(f"## Page {i+1}\n\n{text}\n")
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{total} pages")
        doc.close()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  Done: {total} pages -> {out_path}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("All done!")
