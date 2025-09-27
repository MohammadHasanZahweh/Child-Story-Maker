# app.py
# ------------------------------------------
# Quick start:
#   pip install "streamlit>=1.36" pillow reportlab
#   streamlit run app.py
# ------------------------------------------

import io
import json
import random
import textwrap
import zipfile
from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# -----------------------------
# App Metadata
# -----------------------------
APP_TITLE = "Magical Story Builder"
APP_TAGLINE = "Create wonderful, illustrated stories from your imagination!"

# -----------------------------
# Data Models
# -----------------------------
@dataclass
class Chapter:
    title: str
    text: str
    image_bytes: Optional[bytes] = None

@dataclass
class Story:
    title: str
    author: str
    age_group: str
    language: str
    style: str
    reading_level: str
    chapters: List[Chapter]
    seed: Optional[int] = None

# -----------------------------
# Helpers / Constants
# -----------------------------
AGE_LEVEL_HINTS = {
    "3-5 (Pre-K)": "Very short sentences, lots of repetition, simple words, gentle plot.",
    "6-8 (Grades 1-3)": "Short paragraphs, clear events, simple dialogue, friendly tone.",
    "9-12 (Middle)": "Longer paragraphs, more detail and vocabulary, light suspense/conflict.",
}

LANG_CHOICES = ["English", "Arabic", "French"]
STYLE_CHOICES = [
    "Cozy bedtime",
    "Adventure",
    "Funny",
    "Mystery (gentle)",
    "Fantasy",
    "Sci-Fi (kid-safe)",
]
IMG_STYLE_CHOICES = ["Watercolor", "Cartoon", "Crayon", "Paper-cut", "Clay"]

SAFE_WORDS_BLOCKLIST = {
    # lightweight demo filter; replace with a policy service in production
    "violence": ["kill", "murder", "blood", "weapon", "gun", "knife"],
    "adult": ["alcohol", "drugs", "sex"],
}

FONT_CACHE: Dict[str, ImageFont.ImageFont] = {}

def get_font(size: int = 36) -> ImageFont.ImageFont:
    key = f"{size}"
    if key in FONT_CACHE:
        return FONT_CACHE[key]
    try:
        fnt = ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        fnt = ImageFont.load_default()
    FONT_CACHE[key] = fnt
    return fnt

def wrap_text(text: str, width: int = 36) -> str:
    return "\n".join(textwrap.wrap(text, width=width))

def kid_safe_prompt(prompt: str) -> Tuple[bool, str]:
    lowered = prompt.lower()
    hits = []
    for _, words in SAFE_WORDS_BLOCKLIST.items():
        for w in words:
            if w in lowered:
                hits.append(w)
    if hits:
        return False, f"Your prompt includes content not suitable for kids: {', '.join(sorted(set(hits)))}. Please rephrase."
    return True, ""

def reading_level_for_age(age_group: str) -> str:
    return AGE_LEVEL_HINTS.get(age_group, "Simple, positive tone with age-appropriate vocabulary.")

def is_arabic(lang: str) -> bool:
    return lang.lower().startswith("arab")

def rtl_block(s: str) -> str:
    return f"<div style='direction: rtl; text-align: right'>{s}</div>"

# -----------------------------
# Mock Generators (replace later)
# -----------------------------
def mock_generate_story(
    prompt: str,
    title_hint: str,
    age_group: str,
    language: str,
    style: str,
    n_chapters: int,
    seed: Optional[int],
    extra_context: Optional[Dict[str, str]] = None,
) -> Story:
    """Demo text generator. Replace with your LLM calls."""
    rng = random.Random(seed)

    # Simple title synthesis
    title = title_hint.strip() or (
        ("مغامرة " + prompt[:10]) if language == "Arabic"
        else f"The {style.split()[0]} of {prompt.split()[0].capitalize()}"
    )

    reading_level = reading_level_for_age(age_group)
    char_name = (extra_context or {}).get("char_name", "").strip()
    traits = (extra_context or {}).get("traits", "kind, curious").strip()
    setting = (extra_context or {}).get("setting", "a cozy town").strip()

    if not char_name:
        char_name = "Luna" if language != "Arabic" else "لونا"

    chapters: List[Chapter] = []
    for i in range(1, n_chapters + 1):
        base = (
            f"[{language}] Chapter {i}\n"
            f"Style: {style}. Setting: {setting}. Character: {char_name} ({traits}).\n"
            f"Our hero explores the idea: {prompt}.\n"
            f"Writing guide: {reading_level}\n"
            f"(Demo placeholder text — replace via your LLM output.)"
        )
        chapters.append(Chapter(title=f"Chapter {i}", text=base))

    return Story(
        title=title,
        author="Story Maker",
        age_group=age_group,
        language=language,
        style=style,
        reading_level=reading_level,
        chapters=chapters,
        seed=seed,
    )

def scene_prompt_from_chapter(ch: Chapter, lang: str, img_style: str) -> str:
    first_line = ch.text.split("\n", 1)[0]
    return (
        f"{first_line}. Illustration style: {img_style}. "
        f"Kid-friendly, bright colors, soft edges, simple background, "
        f"single focal subject, age-appropriate. Language: {lang}."
    )

def mock_generate_image_for_chapter(chapter: Chapter, img_style: str, seed: Optional[int]) -> bytes:
    """Create a simple PIL image with the chapter title and style label (demo)."""
    rng = random.Random((seed or 0) + sum(ord(c) for c in chapter.title))
    w, h = 1024, 768
    img = Image.new(
        "RGB",
        (w, h),
        color=(rng.randint(150, 230), rng.randint(150, 230), rng.randint(150, 230)),
    )
    draw = ImageDraw.Draw(img)
    title_wrapped = wrap_text(f"{chapter.title}\n({img_style})", width=18)
    text_wrapped = wrap_text(chapter.text.split("\n")[0][:140] + "…", width=28)

    draw.multiline_text((40, 40), title_wrapped, font=get_font(48), fill=(20, 20, 20), spacing=6)
    draw.multiline_text((40, 220), text_wrapped, font=get_font(28), fill=(30, 30, 30), spacing=4)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# Cache the illustration (useful when swapping to a real image model)
@st.cache_data(show_spinner=False)
def cached_image_bytes(chapter_title: str, chapter_text: str, img_style: str, seed: Optional[int]) -> bytes:
    ch = Chapter(title=chapter_title, text=chapter_text)
    return mock_generate_image_for_chapter(ch, img_style, seed)

# -----------------------------
# Packaging / Exports
# -----------------------------
def package_story_downloads(story: Story) -> bytes:
    """Create a ZIP with JSON story + images."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        story_dict: Dict[str, Any] = asdict(story)
        for ch in story_dict["chapters"]:
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
        flow = [Paragraph(f"<b>{title}</b>", heading), Paragraph(text.replace("\n", "<br/>"), body)]
        frame = Frame(2 * cm, 2 * cm, W - 4 * cm, H - 6 * cm, showBoundary=0)
        frame.addFromList(flow, c)

    if cover_img_bytes:
        c.drawImage(ImageReader(io.BytesIO(cover_img_bytes)), 0, 0, width=W, height=H, preserveAspectRatio=True, anchor="c")
        c.showPage()

    for ch in story.chapters:
        draw_text_page(ch.title, ch.text)
        c.showPage()
        if ch.image_bytes:
            c.drawImage(ImageReader(io.BytesIO(ch.image_bytes)), 0, 0, width=W, height=H, preserveAspectRatio=True, anchor="c")
            c.showPage()

    c.save()
    return buf.getvalue()

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="📖", layout="wide")

# Session state to persist results across reruns
if "story" not in st.session_state:
    st.session_state.story = None
if "cover_img_bytes" not in st.session_state:
    st.session_state.cover_img_bytes = None

# Styling
st.markdown(
    """
    <style>
    .main-bg {
        background: linear-gradient(120deg, #f0f4fa 60%, #e0e7ff 100%);
        padding: 2.0rem 1.5rem 1.5rem 1.5rem;
        border-radius: 18px;
        box-shadow: 0 4px 24px 0 rgba(99,102,241,0.08);
        margin-bottom: 1.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: #e0e7ff;
        color: #222;
        border-radius: 8px 8px 0 0;
        margin-right: 2px;
        font-weight: 500;
        font-size: 1.05rem;
        border: 1.5px solid #c7d2fe;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #6366f1 0%, #60a5fa 100%);
        color: #fff;
        border-bottom: 2.5px solid #6366f1;
    }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #60a5fa 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 1rem;
        padding: 0.55rem 1.2rem;
        box-shadow: 0 2px 8px 0 rgba(99,102,241,0.13);
        transition: 0.2s;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #60a5fa 0%, #6366f1 100%);
    }
    .stTextInput>div>div>input, .stTextArea textarea {
        background: #f0f4fa;
        border-radius: 8px;
        border: 1.5px solid #c7d2fe;
        color: #222;
        font-size: 1.05rem;
    }
    .stSelectbox>div>div>div>div { background: #f0f4fa; border-radius: 8px; color: #222; }
    .stSlider>div>div>div>div { background: #6366f1; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(
        """
        <div style='padding:0.5rem 0; display:flex; align-items:center;'>
            <span style='font-size:2rem; margin-right:0.5rem;'>📖</span>
            <span style='font-size:1.2rem; font-weight:700; color:#6366f1;'>Story Settings</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    age_group = st.selectbox("Target age", list(AGE_LEVEL_HINTS.keys()), index=0)
    language = st.selectbox("Language", LANG_CHOICES, index=0)
    style = st.selectbox("Tone / style", STYLE_CHOICES, index=0)
    img_style = st.selectbox("Image style", IMG_STYLE_CHOICES, index=1)
    n_chapters = st.slider("Chapters", 1, 8, 4)
    seed = st.number_input("Seed (optional)", value=0, min_value=0, step=1)

    st.markdown("### Character")
    char_name = st.text_input("Main character name", "")
    char_traits = st.text_input("2–3 traits (comma-separated)", "curious, kind")
    setting = st.text_input("Setting", "small seaside town")

    st.caption("Tip: Fix the seed to reproduce results when iterating.")

# Header / tagline
st.markdown(
    f"""
    <div class='main-bg'>
        <span style='font-size:1.3rem; font-weight:700; color:#6366f1; letter-spacing:0.5px;'>
            {APP_TAGLINE}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Prompt area
col1, col2 = st.columns([2, 1], gap="large")
with col1:
    user_prompt = st.text_area(
        "Your idea (prompt)",
        placeholder="A brave cat who wants to touch the moon…",
        height=120,
    )
    title_hint = st.text_input("Optional title override", placeholder="e.g., Luna and the Moon Ladder")

with col2:
    st.markdown("### Advanced")
    show_guidance = st.checkbox("Show age guidance", value=True)
    if show_guidance:
        st.info(reading_level_for_age(age_group))
    safe_mode = st.checkbox("Kid-safe filter", value=True)
    add_cover = st.checkbox("Generate a cover image", value=True)

# Buttons row

btn1, btn2 = st.columns([1, 1])
gen = btn1.button("✨ Generate story")
regen_imgs = btn2.button("🔄 Regenerate IMAGES only")



if gen:
    if not user_prompt.strip():
        st.warning("Please enter a prompt to start.")
        st.stop()
    if safe_mode:
        ok, err = kid_safe_prompt(user_prompt)
        if not ok:
            st.error(err)
            st.stop()

    with st.spinner("Creating your story…"):
        story = mock_generate_story(
            prompt=user_prompt,
            title_hint=title_hint,
            age_group=age_group,
            language=language,
            style=style,
            n_chapters=n_chapters,
            seed=seed or None,
            extra_context={"char_name": char_name, "traits": char_traits, "setting": setting},
        )

    with st.spinner("Painting illustrations…"):
        for ch in story.chapters:
            ch.image_bytes = cached_image_bytes(ch.title, ch.text, img_style, story.seed)

        cover_img_bytes = None
        if add_cover:
            cover_ch = Chapter(
                title=f"{story.title}",
                text=f"A {style.lower()} story for {age_group}.",
            )
            cover_img_bytes = cached_image_bytes(cover_ch.title, cover_ch.text, img_style + " (Cover)", (story.seed or 0) + 999)

    st.success("Story ready!")
    st.session_state.story = deepcopy(story)
    st.session_state.cover_img_bytes = cover_img_bytes

if regen_imgs and st.session_state.story:
    with st.spinner("Repainting illustrations…"):
        for ch in st.session_state.story.chapters:
            ch.image_bytes = cached_image_bytes(ch.title, ch.text, img_style, st.session_state.story.seed)
    st.success("Images updated.")
    st.rerun()

# Render persisted story (if any)
if st.session_state.story:
    story = st.session_state.story
    cover_img_bytes = st.session_state.cover_img_bytes

    if add_cover and cover_img_bytes:
        st.image(cover_img_bytes, caption="Cover", use_column_width=True)

    chapter_tabs = st.tabs([f"{i+1}. {c.title}" for i, c in enumerate(story.chapters)])
    for tab, ch in zip(chapter_tabs, story.chapters):
        with tab:
            st.markdown(f"### {ch.title}")
            if is_arabic(story.language):
                st.markdown(rtl_block(ch.text.replace("\n", "<br/>")), unsafe_allow_html=True)
            else:
                st.write(ch.text)
            if ch.image_bytes:
                st.image(ch.image_bytes, caption=f"Illustration – {img_style}", use_column_width=True)

    # Downloads
    colA, colB, colC = st.columns(3)
    with colA:
        zip_bytes = package_story_downloads(story)
        st.download_button(
            "📦 Download story (ZIP)",
            data=zip_bytes,
            file_name=f"{story.title.replace(' ', '_').lower()}_story.zip",
            mime="application/zip",
        )
    with colB:
        story_text = f"# {story.title}\n\n" + "\n\n".join([f"## {c.title}\n\n{c.text}" for c in story.chapters])
        # Only show ZIP download, remove Markdown text download
        colB = None  # Placeholder to maintain column structure
    with colC:
        pdf_bytes = build_pdf(story, cover_img_bytes if add_cover else None)
        st.download_button(
            "📄 Download as PDF",
            data=pdf_bytes,
            file_name=f"{story.title.replace(' ', '_').lower()}.pdf",
            mime="application/pdf",
        )

# -----------------------------
# Integration Notes (for developers)
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("#### Integration Notes")
st.sidebar.caption(
    "Replace the mock generators with your real model calls:\n"
    "• Text: llm_generate_story(...) -> Story\n"
    "• Images: image_generate(scene_prompt, style, seed) -> PNG bytes\n"
    "Keep seeds/styles for reproducibility."
)
