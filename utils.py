import io
import json
import zipfile
from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple

from constants import *

# unused
# def get_font(size: int = 36) -> ImageFont.ImageFont:
#     key = f"{size}"
#     if key in FONT_CACHE:
#         return FONT_CACHE[key]
#     try:
#         fnt = ImageFont.truetype("DejaVuSans.ttf", size)
#     except Exception:
#         fnt = ImageFont.load_default()
#     FONT_CACHE[key] = fnt
#     return fnt

# unused
# def wrap_text(text: str, width: int = 36) -> str:
#     return "\n".join(textwrap.wrap(text, width=width))


def kid_safe_prompt(prompt: str) -> Tuple[bool, str]:
    lowered = prompt.lower()
    hits = []
    for _, words in SAFE_WORDS_BLOCKLIST.items():
        for w in words:
            if w in lowered:
                hits.append(w)
    if hits:
        return (
            False,
            f"Your prompt includes content not suitable for kids: {', '.join(sorted(set(hits)))}. Please rephrase.",
        )
    return True, ""


def reading_level_for_age(age_group: str) -> str:
    return AGE_LEVEL_HINTS.get(
        age_group, "Simple, positive tone with age-appropriate vocabulary."
    )


def is_arabic(lang: str) -> bool:
    return lang.lower().startswith("arab")


def rtl_block(s: str) -> str:
    return f"<div style='direction: rtl; text-align: right'>{s}</div>"


# -----------------------------
# Packaging / Exports
# -----------------------------
def package_story_downloads(story: Story) -> bytes:
    """Create a ZIP with JSON story + images."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        story_dict: Dict[str, Any] = asdict(story)
        for ch in story_dict["sections"]:
            ch.pop("image_bytes", None)
        zf.writestr("story.json", json.dumps(story_dict, ensure_ascii=False, indent=2))
        for idx, ch in enumerate(story.chapters, start=1):
            if ch.image_bytes:
                zf.writestr(f"images/chapter_{idx:02d}.png", ch.image_bytes)
    return zip_buf.getvalue()


def build_pdf(story: Story, cover_img_bytes: Optional[bytes]) -> bytes:
    """Create a simple multi-page PDF (cover + chapter text + chapter image)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, Frame

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    c.setTitle(story.title)

    def draw_text_page(title: str, text: str):
        styles = getSampleStyleSheet()
        heading = styles["Heading2"]
        body = styles["BodyText"]
        body.fontSize = 12
        body.leading = 16
        flow = [
            Paragraph(f"<b>{title}</b>", heading),
            Paragraph(text.replace("\n", "<br/>"), body),
        ]
        frame = Frame(2 * cm, 2 * cm, W - 4 * cm, H - 6 * cm, showBoundary=0)
        frame.addFromList(flow, c)

    if cover_img_bytes:
        c.drawImage(
            ImageReader(io.BytesIO(cover_img_bytes)),
            0,
            0,
            width=W,
            height=H,
            preserveAspectRatio=True,
            anchor="c",
        )
        c.showPage()

    for ch in story.chapters:
        draw_text_page(ch.title, ch.text)
        c.showPage()
        if ch.image_bytes:
            c.drawImage(
                ImageReader(io.BytesIO(ch.image_bytes)),
                0,
                0,
                width=W,
                height=H,
                preserveAspectRatio=True,
                anchor="c",
            )
            c.showPage()

    c.save()
    return buf.getvalue()
