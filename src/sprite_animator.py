import pygame


class SpriteAnimator:
    def __init__(self, sheet_path, animations, frame_duration=6, scale=1):
        self.sheet_path = sheet_path
        self.animations = animations
        self.frame_duration = max(1, int(frame_duration))
        self.scale = max(1, int(scale))
        self.current_animation = next(iter(animations))
        self.current_frame_index = 0
        self._tick = 0
        self._cache = {}

        loaded_sheet = pygame.image.load(sheet_path)
        try:
            self.sheet = loaded_sheet.convert_alpha()
        except pygame.error:
            self.sheet = loaded_sheet.copy()
        self.frames = {
            name: [self._load_frame(rect) for rect in rects]
            for name, rects in animations.items()
        }

    def _load_frame(self, rect):
        frame = self.sheet.subsurface(pygame.Rect(rect)).copy()
        if self.scale != 1:
            size = (frame.get_width() * self.scale, frame.get_height() * self.scale)
            frame = pygame.transform.scale(frame, size)
        return frame

    def update(self, animation):
        if animation not in self.frames:
            animation = self.current_animation

        if animation != self.current_animation:
            self.current_animation = animation
            self.current_frame_index = 0
            self._tick = 0

        frame_count = len(self.frames[self.current_animation])
        if frame_count <= 1:
            return

        self._tick += 1
        if self._tick >= self.frame_duration:
            self._tick = 0
            self.current_frame_index = (self.current_frame_index + 1) % frame_count

    def draw(self, surface, bottom_center, facing=1, squash=(1.0, 1.0), alpha=255):
        frame = self.frames[self.current_animation][self.current_frame_index]
        image = self._transform(frame, facing, squash, alpha)
        rect = image.get_rect(midbottom=(int(bottom_center[0]), int(bottom_center[1])))
        surface.blit(image, rect)

    def _transform(self, frame, facing, squash, alpha):
        sx = max(0.2, float(squash[0]))
        sy = max(0.2, float(squash[1]))
        alpha = max(0, min(255, int(alpha)))
        flip = facing < 0
        key = (id(frame), flip, round(sx, 2), round(sy, 2), alpha)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        image = frame
        if flip:
            image = pygame.transform.flip(image, True, False)

        if sx != 1.0 or sy != 1.0:
            width = max(1, int(image.get_width() * sx))
            height = max(1, int(image.get_height() * sy))
            image = pygame.transform.scale(image, (width, height))

        if alpha < 255:
            image = image.copy()
            image.set_alpha(alpha)

        if len(self._cache) > 160:
            self._cache.clear()
        self._cache[key] = image
        return image
