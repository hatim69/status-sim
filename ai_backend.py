"""
Optional Claude-backed in-character reply generator.

If ANTHROPIC_API_KEY is set in the environment, a small number of AI
character replies per post are generated live by Claude; every other
reply (and all replies when no key is set, or on any API error) falls
back to the local template banks in app.py. Uses the cheapest/fastest
model and a tight output cap to keep this inexpensive to run.
"""
import os

_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 60

_client = None
_client_checked = False

ARCHETYPE_VOICE = {
    "mentor": "a sharp, supportive mentor figure who keeps their protege in line but always has their back",
    "rival": "a petty, competitive rival who never fully admits when they're impressed",
    "bestie": "an unhinged, ride-or-die best friend who is always 100% in your corner",
}


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    try:
        _client = anthropic.Anthropic()
    except Exception:
        _client = None
    return _client


def is_enabled():
    return _get_client() is not None


def generate_reply(character, fandom_name, persona_name, post_text, category):
    """Returns a short in-character reply string, or None to fall back to templates."""
    client = _get_client()
    if client is None:
        return None

    voice = ARCHETYPE_VOICE.get(character["archetype"], "an in-character social media follower")
    system = (
        f"You are {character['name']}, {voice}, inside the fictional world '{fandom_name}'. "
        "Reply to a friend's social media post in-character, in one short sentence (under 140 "
        "characters), using current casual internet slang naturally, not forced. Never break "
        f"character and never mention being an AI. The post's vibe is categorized as '{category}'."
    )
    try:
        resp = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": f'{persona_name} posted: "{post_text}"\n\nReply in character, one short line.',
                }
            ],
        )
        text = "".join(block.text for block in resp.content if getattr(block, "type", None) == "text").strip()
        return text[:280] or None
    except Exception:
        return None
