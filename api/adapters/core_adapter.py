# core/story_core.py
from __future__ import annotations

import os
import json
import base64
from typing import Any, Dict

from openai import AsyncOpenAI, APIStatusError

# --- Configuration -----------------------------------------------------------
TEXT_MODEL = os.getenv("STORY_MODEL", "gpt-4.1-mini")   # good quality/cost balance
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")   # image generator
DEFAULT_IMAGE_SIZE = os.getenv("IMAGE_SIZE", "512x512")

# Create a single async client (httpx under the hood)
_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# --- Helpers -----------------------------------------------------------------
def _story_schema(sections: int) -> Dict[str, Any]:
    """
    JSON Schema to enforce the model returns exactly the structure your app expects.
    """
    return {
        "name": "Story",
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "sections": {
                    "type": "array",
                    "minItems": sections,
                    "maxItems": sections,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "id": {"type": "integer"},
                            "text": {"type": "string"},
                            "image_prompt": {"type": "string"},
                        },
                        "required": ["id", "text", "image_prompt"]
                    }
                }
            },
            "required": ["title", "sections"]
        }
    }

def _build_story_prompt(*, prompt: str, age: int, language: str, style: str, sections: int) -> str:
    return (
        "You are a children's story generator.\n\n"
        f"Target language: {language}\n"
        f"Target reader age: {age}\n"
        f"Narrative style/tone: {style}\n"
        f"Number of sections/pages: {sections}\n\n"
        "CONTENT GUIDELINES:\n"
        "- Keep vocabulary appropriate for the target age.\n"
        "- Make each section self-contained and ~2-5 sentences.\n"
        "- Gently educational, warm and engaging.\n"
        "- For each section include an 'image_prompt' that describes a single coherent scene "
        "in a kids-book illustration style (no text overlays), concise but specific.\n\n"
        "STORY IDEA / USER PROMPT:\n"
        f"{prompt}\n\n"
        "OUTPUT FORMAT:\n"
        "Return ONLY valid JSON that matches the provided JSON Schema. Do not include explanations."
    )

# --- Public API --------------------------------------------------------------
async def generate_story_core(prompt: str, *, age: int, language: str, style: str, sections: int):
    """
    Calls OpenAI Responses API to produce a structured story:
    {
      "title": "...",
      "sections": [
        {"id": 1, "text": "...", "image_prompt": "..."},
        ...
      ]
    }
    """
    sys_instructions = (
        "You generate children's stories and strictly follow JSON schemas. "
        "When asked for structured output, you ONLY produce JSON."
    )
    user_prompt = _build_story_prompt(
        prompt=prompt, age=age, language=language, style=style, sections=sections
    )

    try:
        resp = await _client.responses.create(
            model=TEXT_MODEL,
            instructions=sys_instructions,
            input=[{"role": "user", "content": user_prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": _story_schema(sections),
            },
            temperature=0.9,
        )

        # With response_format=json_schema, the model returns JSON text we can parse.
        # In SDK v1+, text is accessible via .output_text; to be robust, fallback to the raw path.
        raw_json = getattr(resp, "output_text", None)
        if not raw_json:
            # Fallback: dig into the first output item
            # (structure: resp.output[0].content[0].text)
            output = getattr(resp, "output", []) or []
            content_items = (output[0].content if output else []) or []
            raw_json = getattr(content_items[0], "text", "") if content_items else ""

        data = json.loads(raw_json)

        # Minimal post-validate / normalize ids 1..sections
        if "sections" in data:
            for i, sec in enumerate(data["sections"], start=1):
                sec["id"] = i

        return data

    except APIStatusError as e:
        # Surface a helpful error, but keep the function contract
        raise RuntimeError(f"OpenAI API error ({e.status_code}): {e.message}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate story: {e}") from e


async def generate_image_core(image_prompt: str, *, size: str = DEFAULT_IMAGE_SIZE) -> bytes:
    """
    Calls OpenAI Images API and returns PNG bytes for the first generated image.
    """
    try:
        img = await _client.images.generate(
            model=IMAGE_MODEL,
            prompt=image_prompt,
            size=size,
            response_format="b64_json",
        )
        b64 = img.data[0].b64_json  # type: ignore[attr-defined]
        return base64.b64decode(b64)
    except APIStatusError as e:
        raise RuntimeError(f"OpenAI Images API error ({e.status_code}): {e.message}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to generate image: {e}") from e

