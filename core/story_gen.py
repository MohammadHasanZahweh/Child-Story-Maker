from openai import OpenAI
import base64

import os

client = OpenAI()

BASE_PROMPT = """
    I want you to write a children's bedtime storybook in a rhyming, lyrical style. Use simple, fun language suitable for kids aged 3–7. Structure the story in 10 pages, each page having 4 lines of rhyming text (AABB or ABAB). Add a playful title and a short intro subtitle like a real children’s book. The tone should be warm, cheerful, and gently educational. All Pages must start with ---- and a ###Page_i where i is the page number. Base the story on the following idea:
    """

def generate_story(story_description):
    story_prompt = BASE_PROMPT + story_description
    response = client.responses.create(
        model="gpt-5",
        input=story_prompt
        )
    return response.id, response.output_text

