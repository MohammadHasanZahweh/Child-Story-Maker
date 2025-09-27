try:
    from core.story_core import generate_story as _gen_story, generate_image as _gen_image
except ImportError:
    async def _gen_story(prompt: str, *, age: int, language: str, style: str, sections: int):
        return {
            "title": "Stub: Brave Little Fox",
            "sections": [
                {"id": i, "text": f"Section {i} text.", "image_prompt": "A friendly fox, kids book style"}
                for i in range(1, sections + 1)
            ]
        }
    async def _gen_image(image_prompt: str, *, size: str = "1024x1024"):
        return b"\x89PNG\r\n\x1a\n"

async def generate_story_core(*, prompt: str, age: int, language: str, style: str, sections: int):
    return await _gen_story(prompt, age=age, language=language, style=style, sections=sections)

async def generate_image_core(image_prompt: str, *, size: str):
    return await _gen_image(image_prompt, size=size)
