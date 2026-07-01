DEFAULT_PROFILE = {
    "movement": 1.0,
    "dash_power": 1.0,
    "gravity": 1.0,
    "jump": 1.0,
    "extra_jumps": 0,
    "visibility": 1.0,
    "camera": 1.0,
    "animation": 1.0,
    "particle": 1.0,
    "mood": "balanced",
}

EMOTION_PROFILES = {
    "Fear": {
        "movement": 0.88, "dash_power": 0.94, "gravity": 1.0, "jump": 0.96,
        "extra_jumps": 0, "visibility": 0.72, "camera": 1.18,
        "animation": 0.92, "particle": 0.7, "mood": "nervous",
    },
    "Anger": {
        "movement": 1.08, "dash_power": 1.22, "gravity": 1.02, "jump": 1.0,
        "extra_jumps": 0, "visibility": 1.0, "camera": 1.25,
        "animation": 1.18, "particle": 1.35, "mood": "intense",
    },
    "Sadness": {
        "movement": 0.9, "dash_power": 0.9, "gravity": 1.04, "jump": 0.95,
        "extra_jumps": 0, "visibility": 0.88, "camera": 0.85,
        "animation": 0.82, "particle": 0.95, "mood": "heavy",
    },
    "Hope": {
        "movement": 1.02, "dash_power": 1.06, "gravity": 0.96, "jump": 1.08,
        "extra_jumps": 1, "visibility": 1.08, "camera": 0.95,
        "animation": 1.12, "particle": 1.25, "mood": "bright",
    },
    "Courage": {
        "movement": 1.0, "dash_power": 1.12, "gravity": 1.0, "jump": 1.04,
        "extra_jumps": 0, "visibility": 1.0, "camera": 1.12,
        "animation": 1.05, "particle": 1.15, "mood": "brave",
    },
    "Acceptance": {
        "movement": 1.0, "dash_power": 1.0, "gravity": 1.0, "jump": 1.0,
        "extra_jumps": 1, "visibility": 1.12, "camera": 0.9,
        "animation": 1.0, "particle": 1.1, "mood": "peaceful",
    },
    "Calm": {
        "movement": 0.96, "dash_power": 0.98, "gravity": 0.96, "jump": 1.02,
        "extra_jumps": 0, "visibility": 1.05, "camera": 0.78,
        "animation": 0.86, "particle": 0.75, "mood": "calm",
    },
    "Joy": {
        "movement": 1.08, "dash_power": 1.08, "gravity": 0.94, "jump": 1.1,
        "extra_jumps": 1, "visibility": 1.15, "camera": 0.92,
        "animation": 1.22, "particle": 1.4, "mood": "energetic",
    },

    # ── Nervous archetype (Fear siblings) ───────────────────────
    "Anxiety": {
        "movement": 0.85, "dash_power": 0.90, "gravity": 1.02, "jump": 0.94,
        "extra_jumps": 0, "visibility": 0.68, "camera": 1.22,
        "animation": 0.88, "particle": 0.65, "mood": "nervous",
    },
    "Doubt": {
        "movement": 0.87, "dash_power": 0.92, "gravity": 1.0, "jump": 0.95,
        "extra_jumps": 0, "visibility": 0.75, "camera": 1.15,
        "animation": 0.90, "particle": 0.72, "mood": "nervous",
    },
    "Vulnerability": {
        "movement": 0.86, "dash_power": 0.88, "gravity": 1.0, "jump": 0.97,
        "extra_jumps": 0, "visibility": 0.78, "camera": 1.12,
        "animation": 0.85, "particle": 0.68, "mood": "nervous",
    },
    "Confusion": {
        "movement": 0.82, "dash_power": 0.85, "gravity": 1.05, "jump": 0.90,
        "extra_jumps": 0, "visibility": 0.65, "camera": 1.30,
        "animation": 0.80, "particle": 0.60, "mood": "nervous",
    },

    # ── Heavy archetype (Sadness siblings) ──────────────────────
    "Grief": {
        "movement": 0.85, "dash_power": 0.85, "gravity": 1.08, "jump": 0.90,
        "extra_jumps": 0, "visibility": 0.82, "camera": 0.80,
        "animation": 0.75, "particle": 0.90, "mood": "heavy",
    },
    "Reflection": {
        "movement": 0.92, "dash_power": 0.92, "gravity": 1.02, "jump": 0.97,
        "extra_jumps": 0, "visibility": 0.90, "camera": 0.88,
        "animation": 0.85, "particle": 0.92, "mood": "heavy",
    },
    "Patience": {
        "movement": 0.88, "dash_power": 0.88, "gravity": 1.0, "jump": 0.98,
        "extra_jumps": 0, "visibility": 0.92, "camera": 0.82,
        "animation": 0.80, "particle": 0.85, "mood": "heavy",
    },

    # ── Bright archetype (Hope siblings) ────────────────────────
    "Curiosity": {
        "movement": 1.04, "dash_power": 1.04, "gravity": 0.94, "jump": 1.10,
        "extra_jumps": 1, "visibility": 1.12, "camera": 0.92,
        "animation": 1.15, "particle": 1.20, "mood": "bright",
    },
    "Wonder": {
        "movement": 1.0, "dash_power": 1.02, "gravity": 0.96, "jump": 1.06,
        "extra_jumps": 1, "visibility": 1.10, "camera": 0.90,
        "animation": 1.10, "particle": 1.18, "mood": "bright",
    },
    "Awe": {
        "movement": 0.98, "dash_power": 1.0, "gravity": 0.95, "jump": 1.08,
        "extra_jumps": 1, "visibility": 1.14, "camera": 0.88,
        "animation": 1.08, "particle": 1.22, "mood": "bright",
    },
    "Relief": {
        "movement": 1.05, "dash_power": 1.08, "gravity": 0.92, "jump": 1.12,
        "extra_jumps": 1, "visibility": 1.18, "camera": 0.90,
        "animation": 1.18, "particle": 1.30, "mood": "bright",
    },
    "Forgiveness": {
        "movement": 1.02, "dash_power": 1.05, "gravity": 0.94, "jump": 1.10,
        "extra_jumps": 1, "visibility": 1.15, "camera": 0.92,
        "animation": 1.14, "particle": 1.25, "mood": "bright",
    },

    # ── Brave archetype (Courage siblings) ──────────────────────
    "Determination": {
        "movement": 1.02, "dash_power": 1.14, "gravity": 1.0, "jump": 1.05,
        "extra_jumps": 0, "visibility": 1.02, "camera": 1.10,
        "animation": 1.08, "particle": 1.18, "mood": "brave",
    },
    "Strength": {
        "movement": 1.05, "dash_power": 1.18, "gravity": 1.02, "jump": 1.06,
        "extra_jumps": 0, "visibility": 1.0, "camera": 1.15,
        "animation": 1.10, "particle": 1.20, "mood": "brave",
    },
    "Persistence": {
        "movement": 1.0, "dash_power": 1.10, "gravity": 1.0, "jump": 1.04,
        "extra_jumps": 0, "visibility": 1.0, "camera": 1.08,
        "animation": 1.06, "particle": 1.12, "mood": "brave",
    },
    "Ambition": {
        "movement": 1.06, "dash_power": 1.16, "gravity": 1.0, "jump": 1.07,
        "extra_jumps": 0, "visibility": 1.05, "camera": 1.18,
        "animation": 1.12, "particle": 1.25, "mood": "brave",
    },
    "Confidence": {
        "movement": 1.04, "dash_power": 1.12, "gravity": 1.0, "jump": 1.08,
        "extra_jumps": 0, "visibility": 1.08, "camera": 1.10,
        "animation": 1.10, "particle": 1.15, "mood": "brave",
    },

    # ── Energetic archetype (Joy siblings) ──────────────────────
    "Excitement": {
        "movement": 1.10, "dash_power": 1.10, "gravity": 0.92, "jump": 1.12,
        "extra_jumps": 1, "visibility": 1.18, "camera": 0.90,
        "animation": 1.25, "particle": 1.45, "mood": "energetic",
    },
    "Playfulness": {
        "movement": 1.06, "dash_power": 1.06, "gravity": 0.96, "jump": 1.08,
        "extra_jumps": 1, "visibility": 1.12, "camera": 0.94,
        "animation": 1.18, "particle": 1.35, "mood": "energetic",
    },

    # ── Peaceful archetype (Acceptance siblings) ─────────────────
    "Peace": {
        "movement": 0.98, "dash_power": 0.98, "gravity": 0.98, "jump": 1.02,
        "extra_jumps": 1, "visibility": 1.14, "camera": 0.88,
        "animation": 0.96, "particle": 1.05, "mood": "peaceful",
    },
    "Trust": {
        "movement": 1.0, "dash_power": 1.0, "gravity": 1.0, "jump": 1.0,
        "extra_jumps": 1, "visibility": 1.10, "camera": 0.92,
        "animation": 1.02, "particle": 1.08, "mood": "peaceful",
    },
    "Growth": {
        "movement": 1.0, "dash_power": 1.02, "gravity": 0.98, "jump": 1.04,
        "extra_jumps": 1, "visibility": 1.12, "camera": 0.92,
        "animation": 1.04, "particle": 1.12, "mood": "peaceful",
    },

    # ── Calm archetype (Calm siblings) ──────────────────────────
    "Focus": {
        "movement": 0.94, "dash_power": 0.96, "gravity": 0.94, "jump": 1.04,
        "extra_jumps": 0, "visibility": 1.08, "camera": 0.75,
        "animation": 0.82, "particle": 0.70, "mood": "calm",
    },
    "Learning": {
        "movement": 0.95, "dash_power": 0.95, "gravity": 0.96, "jump": 1.03,
        "extra_jumps": 0, "visibility": 1.06, "camera": 0.80,
        "animation": 0.84, "particle": 0.78, "mood": "calm",
    },
}


def get_emotion_profile(emotion):
    profile = dict(DEFAULT_PROFILE)
    profile.update(EMOTION_PROFILES.get(emotion, {}))
    return profile
