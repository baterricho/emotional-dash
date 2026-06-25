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
}


def get_emotion_profile(emotion):
    profile = dict(DEFAULT_PROFILE)
    profile.update(EMOTION_PROFILES.get(emotion, {}))
    return profile
