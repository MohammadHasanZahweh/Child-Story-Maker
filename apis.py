# 1- Story generation: given prompt, title, age_group
def story_generation(
    prompt, title_hint, age_group, language, style, n_chapters, seed, extra_context
):
    pass
    return story


# 2- Image generation in chat:
def image_generation(title, text, img_style):
    prompt = f"Illustration for the story titled '{title}'. Scene: {text}. Style: {img_style}."
    # image = generate_image(prompt)
    pass
    return image
