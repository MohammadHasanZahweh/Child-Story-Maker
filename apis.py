import requests
# 1- Story generation: given prompt, title, age_group
def story_generation(
    prompt, title_hint, age_group, language, style, n_chapters, seed, extra_context
):
    print("writing story")
    resp = requests.post(
        "http://127.0.0.1:8000/story",
        json={
            "prompt": prompt,
            "sections": n_chapters,
            "age":age_group,
            "language": language,
            "style":style,
            "title":title_hint,
            "generate_image":False
        }
    )
    print(resp.json())
    story = Story()
    return story


# 2- Image generation in chat:
def image_generation(title, text, img_style):
    prompt = f"Illustration for the story titled '{title}'. Scene: {text}. Style: {img_style}."
    # image = generate_image(prompt)
    pass
    return image
