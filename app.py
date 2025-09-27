# app.py
import streamlit as st
from copy import deepcopy
from utils import *
from apis import story_generation, image_generation


# ======================== SETUP ========================

# -----------------------------
# App Metadata
# -----------------------------
APP_TITLE = "Magical Story Builder"
APP_TAGLINE = "Create wonderful, illustrated stories from your imagination!"

st.set_page_config(page_title=APP_TITLE, page_icon="📖", layout="wide")

# -----------------------------
# Session state
# -----------------------------
if "story" not in st.session_state:
    st.session_state.story = None
if "cover_img_bytes" not in st.session_state:
    st.session_state.cover_img_bytes = None

# -----------------------------
# Styling
# -----------------------------
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

# -----------------------------
# Sidebar: Story settings
# -----------------------------
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

# -----------------------------
# Header
# -----------------------------
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


# ======================== LOGIC STARTS HERE ========================

# -----------------------------
# 1- Prompt area
# -----------------------------
col1, col2 = st.columns([2, 1], gap="large")
with col1:
    user_prompt = st.text_area(
        "Your idea (prompt)",
        placeholder="A brave cat who wants to touch the moon…",
        height=120,
    )
    title_hint = st.text_input(
        "Optional title override", placeholder="e.g., Luna and the Moon Ladder"
    )

with col2:
    st.markdown("### Advanced")
    show_guidance = st.checkbox("Show age guidance", value=True)
    if show_guidance:
        st.info(reading_level_for_age(age_group))
    safe_mode = st.checkbox("Kid-safe filter", value=True)
    add_cover = st.checkbox("Generate a cover image", value=True)

# -----------------------------
# 2- Generate story
# -----------------------------
btn1, btn2 = st.columns([1, 1])
gen = btn1.button("✨ Generate story")

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
        story = story_generation(
            prompt=user_prompt,
            title_hint=title_hint,
            age_group=age_group,
            language=language,
            style=style,
            n_chapters=n_chapters,
            seed=seed or None,
            extra_context={
                "char_name": char_name,
                "traits": char_traits,
                "setting": setting,
            },
        )

    with st.spinner("Painting illustrations…"):
        for ch in story.chapters:
            ch.image_bytes = image_generation(ch.title, ch.text, img_style)

        cover_img_bytes = None
        if add_cover:
            cover_ch = Chapter(
                title=f"{story.title}", text=f"A {style.lower()} story for {age_group}."
            )
            cover_img_bytes = image_generation(
                cover_ch.title, cover_ch.text, img_style + " (Cover)"
            )

    st.success("Story ready!")
    st.session_state.story = deepcopy(story)
    st.session_state.cover_img_bytes = cover_img_bytes

# -----------------------------
# 3- Render story
# -----------------------------
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
                st.markdown(
                    rtl_block(ch.text.replace("\n", "<br/>")), unsafe_allow_html=True
                )
            else:
                st.write(ch.text)
            if ch.image_bytes:
                st.image(
                    ch.image_bytes,
                    caption=f"Illustration – {img_style}",
                    use_column_width=True,
                )

    colA, colB, colC = st.columns(3)
    with colA:
        zip_bytes = package_story_downloads(story)
        st.download_button(
            "📦 Download story (ZIP)",
            data=zip_bytes,
            file_name=f"{story.title.replace(' ', '_').lower()}_story.zip",
            mime="application/zip",
        )
    with colC:
        pdf_bytes = build_pdf(story, cover_img_bytes if add_cover else None)
        st.download_button(
            "📄 Download as PDF",
            data=pdf_bytes,
            file_name=f"{story.title.replace(' ', '_').lower()}.pdf",
            mime="application/pdf",
        )
