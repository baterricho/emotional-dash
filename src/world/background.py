def palette_from_level(level):
    seed = int(level.get("level", 1))
    hue = (seed * 37) % 360
    top = (max(0, int(18 + hue % 50 - 25)), max(0, int(8 + hue % 38 - 19)), max(12, int(35 + hue % 80)))
    bottom = (max(0, int(35 + hue % 90 - 45)), max(0, int(20 + hue % 70 - 35)), max(20, int(80 + hue % 110)))
    return top, bottom
