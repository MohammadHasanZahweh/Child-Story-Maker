# api/app.py
import uuid
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict

from api.adapters.core_adapter import (
    generate_story_core,
    generate_image_core,
)
from api.storage.files import (
    ensure_media_dir,
    save_image_bytes,
    save_audio_bytes,
)
from api.services.tts import synthesize_tts


# -------------------------------
# FastAPI app & middleware
# -------------------------------
app = FastAPI(title="Children Storyteller API", version="1.1.0")

# CORS: wide-open for hackathon; restrict origins later if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for generated media
ensure_media_dir()
app.mount("/media", StaticFiles(directory="media"), name="media")


# -------------------------------
# In-memory "DB" (hackathon-simple)
# story_id -> {"title": str, "sections": [...], "status": str}
# -------------------------------
DB: Dict[str, Dict[str, Any]] = {}


# -------------------------------
# Pydantic models
# -------------------------------
class SectionResp(BaseModel):
    id: int
    text: str
    image_prompt: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None


class StoryResp(BaseModel):
    story_id: str
    title: str
    sections: List[SectionResp]
    status: str  # "ready" | "generating-images" | "generating-audio"


class CreateStoryReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=400)
    age: int = Field(ge=3, le=12)
    language: str = Field(default="en", min_length=2, max_length=10)
    style: Optional[str] = Field(default=None, max_length=60)
    sections: int = Field(default=5, ge=3, le=10)
    generate_images: bool = True
    image_size: str = Field(default="1024x1024", pattern=r"^\d{2,4}x\d{2,4}$")
    model_config = ConfigDict(extra="forbid")


class ImagesReq(BaseModel):
    size: str = Field(default="512x512", pattern=r"^\d{2,4}x\d{2,4}$")


class TTSReq(BaseModel):
    voice: str = Field(
        default="verse",
        description="OpenAI built-in voice (e.g., verse, alloy, nova, coral, shimmer)",
    )
    format: str = Field(
        default="mp3",
        pattern=r"^(mp3|wav|aac|flac|opus)$",
        description="Audio file format to save",
    )


# -------------------------------
# Routes
# -------------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.post("/story", response_model=StoryResp)
async def create_story(req: CreateStoryReq):
    """
    Create a story (and optionally its images).
    """
    try:
        story = await generate_story_core(
            prompt=req.prompt,
            age=req.age,
            language=req.language,
            style=req.style or "default",
            sections=req.sections,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Story provider error: {e}")

    story_id = f"st_{uuid.uuid4().hex[:8]}"

    # Normalize sections for the UI layer
    norm_sections: List[Dict[str, Any]] = [
        {
            "id": s["id"],
            "text": s["text"],
            "image_prompt": s["image_prompt"],
            "image_url": None,
            "audio_url": None,
        }
        for s in story["sections"]
    ]

    DB[story_id] = {
        "title": story["title"],
        "sections": norm_sections,
        "status": "ready",
    }

    if req.generate_images:
        DB[story_id]["status"] = "generating-images"
        try:
            for s in norm_sections:
                img_bytes = await generate_image_core(
                    s["image_prompt"], size=req.image_size
                )
                s["image_url"] = save_image_bytes(story_id, s["id"], img_bytes)
        except Exception as e:
            DB[story_id]["status"] = "ready"  # fail soft; client can retry images
            raise HTTPException(status_code=502, detail=f"Image provider error: {e}")
        DB[story_id]["status"] = "ready"

    return {
        "story_id": story_id,
        "title": DB[story_id]["title"],
        "sections": DB[story_id]["sections"],
        "status": DB[story_id]["status"],
    }


@app.get("/story/{story_id}", response_model=StoryResp)
def get_story(story_id: str):
    data = DB.get(story_id)
    if not data:
        raise HTTPException(status_code=404, detail="Story not found")
    return {
        "story_id": story_id,
        "title": data["title"],
        "sections": data["sections"],
        "status": data["status"],
    }


@app.post("/story/{story_id}/images", response_model=StoryResp)
async def generate_images(story_id: str, req: ImagesReq):
    """
    (Re)generate images for each section.
    """
    d = DB.get(story_id)
    if not d:
        raise HTTPException(status_code=404, detail="Story not found")

    d["status"] = "generating-images"
    try:
        for s in d["sections"]:
            img_bytes = await generate_image_core(s["image_prompt"], size=req.size)
            s["image_url"] = save_image_bytes(story_id, s["id"], img_bytes)
    except Exception as e:
        d["status"] = "ready"
        raise HTTPException(status_code=502, detail=f"Image provider error: {e}")

    d["status"] = "ready"
    return {
        "story_id": story_id,
        "title": d["title"],
        "sections": d["sections"],
        "status": d["status"],
    }

