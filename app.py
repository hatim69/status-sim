"""
Status - Sims But Social (prototype)

A self-contained social-media simulator in the spirit of "Status" by WishRoll:
create a persona, drop it into a fandom community, post to a feed, and get
reactions from AI-driven in-universe characters. Clout rises and falls with
what you post, and an energy system gates how often you can act.

No external services or API keys are required - character reactions are
generated from local template banks, not a live LLM.
"""
import os
import random
import secrets
import time

from flask import Flask, jsonify, render_template, request, session, send_from_directory

import ai_backend
from crowd import CROWD_HANDLES, crowd_avatar

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

MAX_POSTS_STORED = 15
POST_ENERGY_COST = 15
DEFAULT_MAX_ENERGY = 100
PREMIUM_MAX_ENERGY = 150
# How many of a post's reactions may use the live Claude API per post (rest use templates).
# Keeps API usage low even on a viral post that draws 3 reactors.
AI_REPLIES_PER_POST = int(os.environ.get("AI_REPLIES_PER_POST", "1"))

# --- FANDOM COMMUNITIES -----------------------------------------------------
# Each fandom has exactly one character per archetype so reply banks
# (ARCHETYPE_REPLIES) can be shared across every community.
FANDOMS = {
    "wizarding-academy": {
        "name": "Wizarding Academy",
        "emoji": "🪄",
        "desc": "A magic boarding school full of rivalries, secret spells, and prophecy drama.",
        "characters": [
            {"name": "Prof. Lyra Ashbourne", "avatar": "🧙‍♀️", "archetype": "mentor"},
            {"name": "Finch Holloway", "avatar": "😏", "archetype": "rival"},
            {"name": "Wren Sable", "avatar": "⭐", "archetype": "bestie"},
        ],
    },
    "galactic-uprising": {
        "name": "Galactic Uprising",
        "emoji": "🚀",
        "desc": "A rebellion against an empire, fought one viral broadcast at a time.",
        "characters": [
            {"name": "Commander Vex", "avatar": "🎖️", "archetype": "mentor"},
            {"name": "Nova Sarn", "avatar": "😎", "archetype": "rival"},
            {"name": "K-9RO", "avatar": "🤖", "archetype": "bestie"},
        ],
    },
    "neon-district": {
        "name": "Neon District",
        "emoji": "🌆",
        "desc": "Cyberpunk hackers, fixers, and streamers fighting for clout in the underground.",
        "characters": [
            {"name": "Ghost_Iri", "avatar": "👤", "archetype": "mentor"},
            {"name": "Dex Malone", "avatar": "🕶️", "archetype": "rival"},
            {"name": "Juno Cross", "avatar": "📡", "archetype": "bestie"},
        ],
    },
    "ever-after-high": {
        "name": "Ever After High",
        "emoji": "🦸",
        "desc": "A superhero teen drama where secret identities never stay secret for long.",
        "characters": [
            {"name": "Coach Blaze", "avatar": "🔥", "archetype": "mentor"},
            {"name": "Ivy Vane", "avatar": "🖤", "archetype": "rival"},
            {"name": "Milo Chen", "avatar": "😂", "archetype": "bestie"},
        ],
    },
    "undead-dawn": {
        "name": "Undead Dawn",
        "emoji": "🧟",
        "desc": "A zombie apocalypse survivor camp where every post could be your last.",
        "characters": [
            {"name": "Sarge Reyes", "avatar": "🪖", "archetype": "mentor"},
            {"name": "Raider Cole", "avatar": "🔪", "archetype": "rival"},
            {"name": "Pixel", "avatar": "🎮", "archetype": "bestie"},
        ],
    },
    "main-character-era": {
        "name": "Main Character Era",
        "emoji": "💅",
        "desc": "Fully fictional celebrity culture: red carpets, paparazzi, and clout that can vanish overnight. (No real public figures appear in this world.)",
        "characters": [
            {"name": "Coach Reyna Cole", "avatar": "🕶️", "archetype": "mentor"},
            {"name": "Zayne Kroix", "avatar": "🎤", "archetype": "rival"},
            {"name": "Peaches Monroe", "avatar": "💋", "archetype": "bestie"},
        ],
    },
}

ARCHETYPE_REPLIES = {
    "mentor": {
        "hype": [
            "okay {name} really said 'understood the assignment' 💅",
            "not me getting proud of you rn, you're so back",
            "this is giving main character energy, keep going {name}",
        ],
        "snark": [
            "{name}... bestie that's a lot of confidence for a mid move",
            "brave. reckless, but brave.",
            "hm. not the choice I'd have made but you do you",
        ],
        "drama": [
            "okay this is giving canon event, we need to talk {name}",
            "the council is NOT gonna let this rock",
            "you just opened a whole storyline {name}, hope you're ready",
        ],
        "cancel": [
            "{name} I told you this was giving 'about to be cooked' energy. damage control, now.",
            "this ain't the vibe rn, we gotta fix this",
            "we'll get through the L, but it's gonna be rough",
        ],
        "neutral": [
            "noted {name}, carry on",
            "keeping tabs, say less",
            "mid update but noted",
        ],
    },
    "rival": {
        "hype": [
            "...okay that was lowkey fire, {name}. don't let it get to your head tho",
            "fine. FINE. that was kinda goated",
            "lucky. running it back won't happen twice",
        ],
        "snark": [
            "lol sure {name}, whatever helps you sleep",
            "that's... a choice. bold of you",
            "big talk. we'll see if you're really that girl",
        ],
        "drama": [
            "WAIT this is so juicy I'm not even mad 🍿",
            "the way my jaw just hit the floor",
            "screenshotting this for the group chat, {name}",
        ],
        "cancel": [
            "called it. you're cooked 💀",
            "ratio'd. L. no notes.",
            "this ain't the redemption arc you think it is",
        ],
        "neutral": [
            "k.",
            "cool cool cool, npc behavior but ok",
            "noted, moving on with my day",
        ],
    },
    "bestie": {
        "hype": [
            "{name}!! you ATE. left zero crumbs. I'm sobbing 😭✨",
            "this is so unserious I'm obsessed, I'm SO proud of you",
            "screenshotting this, it's giving iconic",
        ],
        "snark": [
            "{name}... bestie we need to talk about your choices fr",
            "the audacity, I'm cackling",
            "no because why would you even- nvm I love you",
        ],
        "drama": [
            "WAIT WAIT WAIT explain right now no cap",
            "okay this is a whole season finale, I'm SO invested",
            "{name} the way I GASPED",
        ],
        "cancel": [
            "I got you no matter what {name}, ride or die fr",
            "the internet is WRONG about you and I will be saying that loudly",
            "don't spiral bestie, we ride at dawn",
        ],
        "neutral": [
            "saw this, love u, no thoughts",
            "okay noted lol, vibes are vibes",
            "👀👀👀 watching this unfold",
        ],
    },
}

CANCEL_WORDS = [
    "cancel", "expose", "exposed", "toxic", "cheat", "cheated", "lied", "liar", "scam", "betray",
    "ratioed", "ratio'd", "cooked", "flopped",
]
DRAMA_WORDS = [
    "drama", "fight", "breakup", "secret", "affair", "rumor", "beef", "shocking", "twist",
    "situationship", "soft launch", "hard launch", "canon event", "tea", "shady", "messy",
]
HYPE_WORDS = [
    "love", "amazing", "best", "proud", "excited", "blessed", "win", "grateful", "yay",
    "slay", "iconic", "goated", "valid", "understood the assignment", "fire", "obsessed",
    "main character", "ate",
]
SNARK_WORDS = ["boring", "meh", "whatever", "lame", "mid", "cringe", "npc", "basic"]

# Short, generic one-liners for the crowd (CROWD_HANDLES) - unlike ARCHETYPE_REPLIES
# these aren't tied to any one character, just background noise from randoms.
CROWD_REPLIES = {
    "hype": [
        "not me finding this at 2am 😭",
        "the algorithm blessed me fr",
        "screenshotting this for the group chat",
        "okay this is sending me",
        "living for this ngl",
    ],
    "drama": [
        "wait what did I just walk into",
        "the way I gasped, tell me more",
        "this is not the content I expected but okay",
        "someone please explain the timeline",
    ],
    "cancel": [
        "this you? 💀",
        "the replies are NOT gonna be nice",
        "oop-",
        "saw this coming ngl",
    ],
    "snark": [
        "...okay",
        "sure jan",
        "this is a lot",
    ],
    "neutral": [
        "real",
        "saw this, no thoughts",
        "mid but ok",
    ],
}

# How many random crowd members react, by clout tier - separate from (and in
# addition to) the fandom's 3 named cast members.
CROWD_COUNTS = {"Cancelled": 3, "Nobody": 0, "Rising": 1, "Viral": 3, "Famous": 4}

TIERS = [
    (float("-inf"), 0, "Cancelled", "💀"),
    (0, 50, "Nobody", "🌱"),
    (50, 150, "Rising", "✨"),
    (150, 350, "Viral", "🔥"),
    (350, float("inf"), "Famous", "👑"),
]


def classify_post(text):
    t = text.lower()
    if any(w in t for w in CANCEL_WORDS):
        return "cancel"
    if any(w in t for w in DRAMA_WORDS):
        return "drama"
    if any(w in t for w in HYPE_WORDS):
        return "hype"
    if any(w in t for w in SNARK_WORDS):
        return "snark"
    return random.choice(["neutral", "neutral", "hype", "snark"])


def clout_delta(category):
    if category == "hype":
        return random.randint(8, 20)
    if category == "drama":
        # consequence-driven: could go viral or backfire
        return random.choice([random.randint(15, 35), -random.randint(5, 15)])
    if category == "cancel":
        return -random.randint(20, 40)
    if category == "snark":
        return random.randint(-5, 5)
    return random.randint(1, 8)


def tier_for(clout):
    for lo, hi, label, icon in TIERS:
        if lo <= clout < hi:
            return {"label": label, "icon": icon}
    return {"label": "Nobody", "icon": "🌱"}


def reactors_for_tier(tier_label, characters):
    counts = {"Nobody": 1, "Rising": 2, "Viral": 3, "Famous": 3, "Cancelled": 3}
    n = min(counts.get(tier_label, 1), len(characters))
    return random.sample(characters, n)


def crowd_comments_for(tier_label, category):
    n = min(CROWD_COUNTS.get(tier_label, 0), len(CROWD_HANDLES))
    if n <= 0:
        return []
    pool = CROWD_REPLIES.get(category, CROWD_REPLIES["neutral"])
    handles = random.sample(CROWD_HANDLES, n)
    return [
        {"author": f"@{h}", "avatar": crowd_avatar(h), "text": random.choice(pool), "ai": False, "crowd": True}
        for h in handles
    ]


def liked_by_preview(likes):
    n = min(3, likes, len(CROWD_HANDLES))
    if n <= 0:
        return []
    return random.sample(CROWD_HANDLES, n)


def react_to_post(fandom_id, persona_name, category, tier_label, post_text="", exclude_name=None):
    fandom = FANDOMS[fandom_id]
    candidates = [c for c in fandom["characters"] if c["name"] != exclude_name]
    chosen = reactors_for_tier(tier_label, candidates)
    comments = []
    for i, char in enumerate(chosen):
        text = None
        is_ai = False
        if i < AI_REPLIES_PER_POST and post_text:
            text = ai_backend.generate_reply(char, fandom["name"], persona_name, post_text, category)
            is_ai = text is not None
        if not text:
            pool = ARCHETYPE_REPLIES[char["archetype"]][category]
            text = random.choice(pool).format(name=persona_name)
        comments.append({"author": char["name"], "avatar": char["avatar"], "text": text, "ai": is_ai, "crowd": False})
    comments.extend(crowd_comments_for(tier_label, category))
    base_likes = {"hype": (20, 60), "drama": (10, 90), "cancel": (0, 15), "snark": (5, 25), "neutral": (5, 30)}
    lo, hi = base_likes.get(category, (5, 20))
    likes = random.randint(lo, hi)
    liked_by = liked_by_preview(likes)
    return comments, likes, liked_by


def default_state():
    return {
        "persona": None,  # {name, avatar, bio}
        "fandom_id": None,
        "clout": 0,
        "energy": DEFAULT_MAX_ENERGY,
        "max_energy": DEFAULT_MAX_ENERGY,
        "premium": False,
        "posts": [],  # newest first
    }


def get_state():
    if "game" not in session:
        session["game"] = default_state()
    return session["game"]


def save_state(state):
    session["game"] = state
    session.modified = True


def public_state(state):
    tier = tier_for(state["clout"])
    fandom = FANDOMS.get(state["fandom_id"]) if state["fandom_id"] else None
    return {
        "persona": state["persona"],
        "fandom": {"id": state["fandom_id"], "name": fandom["name"], "emoji": fandom["emoji"]} if fandom else None,
        "clout": state["clout"],
        "tier": tier,
        "energy": state["energy"],
        "max_energy": state["max_energy"],
        "premium": state["premium"],
        "posts": state["posts"],
        "ai_enabled": ai_backend.is_enabled(),
    }


def seed_posts(state):
    fandom = FANDOMS[state["fandom_id"]]
    seeds = [
        ("hype", "just hit a new record and I'm still shaking, let's gooo"),
        ("drama", "okay something happened at practice today and I can't stop thinking about it"),
        ("neutral", "quiet day around here, regrouping for what's next"),
    ]
    posts = []
    for category, text in seeds:
        char = random.choice(fandom["characters"])
        comments, likes, liked_by = react_to_post(
            state["fandom_id"], char["name"], category, "Rising", exclude_name=char["name"]
        )
        # seed posts are from NPCs, so reroll one comment to keep it varied
        posts.append(
            {
                "id": secrets.token_hex(6),
                "author": char["name"],
                "avatar": char["avatar"],
                "is_user": False,
                "text": text,
                "category": category,
                "likes": likes,
                "liked_by": liked_by,
                "comments": comments[:2],
                "ts": time.time(),
            }
        )
    posts.reverse()
    state["posts"] = posts


# --- ROUTES ------------------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sw.js")
def service_worker():
    return send_from_directory(app.static_folder, "sw.js")


@app.route("/api/fandoms")
def api_fandoms():
    return jsonify(
        [{"id": fid, "name": f["name"], "emoji": f["emoji"], "desc": f["desc"]} for fid, f in FANDOMS.items()]
    )


@app.route("/api/state")
def api_state():
    return jsonify(public_state(get_state()))


@app.route("/api/persona", methods=["POST"])
def api_persona():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()[:24]
    avatar = (data.get("avatar") or "🙂").strip()[:4]
    bio = (data.get("bio") or "").strip()[:120]
    if not name:
        return jsonify({"error": "Name is required."}), 400

    state = get_state()
    state["persona"] = {"name": name, "avatar": avatar, "bio": bio}
    save_state(state)
    return jsonify(public_state(state))


@app.route("/api/fandom", methods=["POST"])
def api_fandom():
    data = request.get_json(force=True) or {}
    fandom_id = data.get("fandom_id")
    if fandom_id not in FANDOMS:
        return jsonify({"error": "Unknown fandom."}), 400

    state = get_state()
    if not state["persona"]:
        return jsonify({"error": "Create a persona first."}), 400

    state["fandom_id"] = fandom_id
    seed_posts(state)
    save_state(state)
    return jsonify(public_state(state))


@app.route("/api/post", methods=["POST"])
def api_post():
    data = request.get_json(force=True) or {}
    text = (data.get("text") or "").strip()[:280]
    if not text:
        return jsonify({"error": "Post can't be empty."}), 400

    state = get_state()
    if not state["persona"] or not state["fandom_id"]:
        return jsonify({"error": "Finish onboarding first."}), 400
    if state["energy"] < POST_ENERGY_COST:
        return jsonify({"error": "Not enough energy.", "code": "no_energy"}), 400

    state["energy"] -= POST_ENERGY_COST
    category = classify_post(text)
    state["clout"] += clout_delta(category)

    tier = tier_for(state["clout"])
    comments, likes, liked_by = react_to_post(
        state["fandom_id"], state["persona"]["name"], category, tier["label"], post_text=text
    )

    post = {
        "id": secrets.token_hex(6),
        "author": state["persona"]["name"],
        "avatar": state["persona"]["avatar"],
        "is_user": True,
        "text": text,
        "category": category,
        "likes": likes,
        "liked_by": liked_by,
        "comments": comments,
        "ts": time.time(),
    }
    state["posts"].insert(0, post)
    state["posts"] = state["posts"][:MAX_POSTS_STORED]
    save_state(state)
    return jsonify(public_state(state))


@app.route("/api/energy/watch_ad", methods=["POST"])
def api_watch_ad():
    state = get_state()
    gained = random.randint(10, 25)
    state["energy"] = min(state["max_energy"], state["energy"] + gained)
    save_state(state)
    resp = public_state(state)
    resp["gained"] = gained
    return jsonify(resp)


@app.route("/api/energy/coffee", methods=["POST"])
def api_coffee():
    # Simulated in-app purchase - no real payment is processed anywhere here.
    state = get_state()
    state["energy"] = min(state["max_energy"], state["energy"] + 20)
    save_state(state)
    return jsonify(public_state(state))


@app.route("/api/premium", methods=["POST"])
def api_premium():
    data = request.get_json(force=True) or {}
    state = get_state()
    state["premium"] = bool(data.get("premium"))
    state["max_energy"] = PREMIUM_MAX_ENERGY if state["premium"] else DEFAULT_MAX_ENERGY
    state["energy"] = state["max_energy"]
    save_state(state)
    return jsonify(public_state(state))


@app.route("/api/reset", methods=["POST"])
def api_reset():
    session["game"] = default_state()
    session.modified = True
    return jsonify(public_state(session["game"]))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    # Debug mode exposes an interactive, code-executing console on unhandled
    # errors - never turn it on for a publicly reachable deployment (Render, etc).
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
