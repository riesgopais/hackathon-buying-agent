import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are an art curator specializing in Van Gogh's aesthetic.
Evaluate if a piece matches Van Gogh's style based on:
- Swirling brushstrokes and dynamic movement
- Bold, saturated colors (deep blues, vibrant yellows, rich greens)
- Thick impasto-style texture
- Subjects: landscapes, night skies, sunflowers, portraits, wheat fields
- Post-impressionist feel

Respond ONLY with valid JSON: {"match": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}"""

def evaluate_aesthetic(title: str, description: str, image_url: str = "") -> dict:
    """Use Claude to evaluate if artwork matches Van Gogh aesthetic."""
    content = f"Title: {title}\nDescription: {description}"

    messages = [{"role": "user", "content": content}]

    # Use vision if image available
    if image_url:
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": image_url},
                },
                {"type": "text", "text": content},
            ],
        }]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    import json
    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {"match": False, "confidence": 0.0, "reason": "Parse error"}
