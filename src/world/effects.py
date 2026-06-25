WEATHER_BY_EFFECT = {
    "rain": "rain",
    "snow": "snow",
    "fire_particles": "embers",
    "glowing_particles": "sparkle",
    "glitch": "glitch",
    "sand": "sand",
}


def weather_for(level):
    for effect in level.get("visual_effects", []):
        if effect in WEATHER_BY_EFFECT:
            return WEATHER_BY_EFFECT[effect]
    return "sparkle"
