import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from api.adapters.core_adapter import generate_story_core, generate_image_core
from api.storage.files import ensure_media_dir, save_image_bytes

app = FastAPI(title="Children Storyteller API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

ensure_media_dir()
app.mount("/media", StaticFiles(directory="media"), name="media")

DB: dict[str, dict] = {}

class SectionResp(BaseModel):
    id: int
    text: str
    image_prompt: str
    image_url: Optional[str] = None

class StoryResp(BaseModel):
    story_id: str
    title: str
    sections: List[SectionResp]
    status: str

class CreateStoryReq(BaseModel):
    prompt: str = Field(min_length=3, max_length=400)
    age: int = Field(ge=3, le=12)
    language: str = Field(default="en", min_length=2, max_length=5)
    style: Optional[str] = Field(default=None, max_length=60)
    sections: int = Field(default=5, ge=3, le=10)
    generate_images: bool = True
    image_size: str = Field(default="1024x1024", pattern=r"^\d{2,4}x\d{2,4}$")
    model_config = ConfigDict(extra="forbid")

@app.get("/health")
def health(): return {"ok": True}

@app.post("/v1/story", response_model=StoryResp)
async def create_story(req: CreateStoryReq):
    story = await generate_story_core(
        prompt=req.prompt, age=req.age, language=req.language, style=req.style or "default", sections=req.sections
    )
    story_id = f"st_{uuid.uuid4().hex[:8]}"
    norm_sections = [
        {"id": s["id"], "text": s["text"], "image_prompt": s["image_prompt"], "image_url": None}
        for s in story["sections"]
    ]
    DB[story_id] = {"title": story["title"], "sections": norm_sections, "status": "ready"}

    if req.generate_images:
        DB[story_id]["status"] = "generating-images"
        for s in norm_sections:
            img_bytes = await generate_image_core(s["image_prompt"], size=req.image_size)
            s["image_url"] = save_image_bytes(story_id, s["id"], img_bytes)
        DB[story_id]["status"] = "ready"

    return {"story_id": story_id, "title": DB[story_id]["title"], "sections": DB[story_id]["sections"], "status": DB[story_id]["status"]}

@app.get("/v1/story/{story_id}", response_model=StoryResp)
def get_story(story_id: str):
    d = DB.get(story_id)
    if not d: raise HTTPException(404, "Story not found")
    return {"story_id": story_id, "title": d["title"], "sections": d["sections"], "status": d["status"]}

@app.post("/v1/story/{story_id}/images", response_model=StoryResp)
async def regenerate_images(story_id: str, size: str = "1024x1024"):
    d = DB.get(story_id)
    if not d: raise HTTPException(404, "Story not found")
    d["status"] = "generating-images"
    for s in d["sections"]:
        img_bytes = await generate_image_core(s["image_prompt"], size=size)
        s["image_url"] = save_image_bytes(story_id, s["id"], img_bytes)
    d["status"] = "ready"
    return {"story_id": story_id, "title": d["title"], "sections": d["sections"], "status": d["status"]}
