from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


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
