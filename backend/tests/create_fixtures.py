import fitz  # PyMuPDF
import os

fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(fixtures_dir, exist_ok=True)

# 1. PDF with text (untagged)
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "This is a tagged PDF with real text content.", fontsize=12)
doc.save(os.path.join(fixtures_dir, "untagged.pdf"))
doc.close()

# 2. Another PDF with text
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 72), "Another page of text.", fontsize=12)
doc.save(os.path.join(fixtures_dir, "has_text.pdf"))
doc.close()

# 3. Image-only PDF (no extractable text)
doc = fitz.open()
page = doc.new_page()
rect = fitz.Rect(72, 72, 200, 200)
page.draw_rect(rect, color=(0, 0, 0), fill=(0.8, 0.8, 0.8))
doc.save(os.path.join(fixtures_dir, "image_only.pdf"))
doc.close()

print("Fixtures created.")
