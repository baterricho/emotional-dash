"""
╔══════════════════════════════════════════════════════════════════╗
║         EMOTION ARCHITECT: ULTIMATE HARDCORE EDITION            ║
║         20 Worlds of Pure Suffering. Good luck.                 ║
╚══════════════════════════════════════════════════════════════════╝

Controls:
  WASD / Arrow Keys  →  Move
  ESC                →  Pause / Menu
  Mouse Joystick     →  Alternative movement (bottom-left)

Notes:
  - ALL emotion sliders are automatically at 100%. No manual control.
  - The WORLD itself reacts to your emotions dynamically.
  - Survive 20 increasingly brutal worlds to win.
  - 5 lives total. Die 5 times → complete wipe. Start over.
  - Each world introduces new mechanics, traps, and horrors.
"""

import math, random, sys, os, json, time
import pygame
from pygame import gfxdraw

# ──────────────────────────────────────────────────────────────────
#  BOOTSTRAP
# ──────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

W, H = 1200, 700
FPS  = 60
SAVE = "ea_ultimate_save.json"

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("EMOTION ARCHITECT: ULTIMATE HARDCORE")
clock = pygame.time.Clock()

# ──────────────────────────────────────────────────────────────────
#  FONTS
# ──────────────────────────────────────────────────────────────────
def try_font(names, size, bold=False):
    for n in names:
        try:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f: return f
        except: pass
    return pygame.font.SysFont("arial", size, bold=bold)

FONT_TINY   = try_font(["Consolas","Courier New","monospace"], 14)
FONT_SM     = try_font(["Consolas","Courier New","monospace"], 18)
FONT_MD     = try_font(["Segoe UI","Helvetica Neue","Arial"],  22, bold=True)
FONT_LG     = try_font(["Segoe UI","Helvetica Neue","Arial"],  38, bold=True)
FONT_XL     = try_font(["Impact","Arial Black","Arial"],       72, bold=True)
FONT_TITLE  = try_font(["Impact","Arial Black","Arial"],       96, bold=True)

# ──────────────────────────────────────────────────────────────────
#  SAVE SYSTEM
# ──────────────────────────────────────────────────────────────────
def load_save():
    if os.path.exists(SAVE):
        try:
            with open(SAVE) as f: return json.load(f)
        except: pass
    return {"level": 0, "best": 0, "deaths": 0, "runs": 0}

def write_save(d):
    with open(SAVE, "w") as f: json.dump(d, f)

save_data = load_save()

# ──────────────────────────────────────────────────────────────────
#  UTILITY
# ──────────────────────────────────────────────────────────────────
def clamp(x, a, b): return max(a, min(b, x))
def lerp(a, b, t):  return a + (b - a) * t

def lerpC(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def hsv(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r*255), int(g*255), int(b*255))

def draw_text(surf, txt, pos, color=(255,255,255), font=None, center=False, shadow=False):
    f = font or FONT_SM
    if shadow:
        sr = f.render(txt, True, (0,0,0))
        ox = pos[0] + (- sr.get_width()//2 if center else 0)
        surf.blit(sr, (ox+2, pos[1]+2))
    r = f.render(txt, True, color)
    x = pos[0] - r.get_width()//2 if center else pos[0]
    surf.blit(r, (x, pos[1]))

def circle_aa(surf, color, pos, radius):
    x, y = int(pos[0]), int(pos[1])
    r = int(radius)
    if r <= 0: return
    try:
        gfxdraw.aacircle(surf, x, y, r, color)
        gfxdraw.filled_circle(surf, x, y, r, color)
    except:
        pygame.draw.circle(surf, color, (x,y), r)

# ──────────────────────────────────────────────────────────────────
#  PARTICLE SYSTEM
# ──────────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ["x","y","vx","vy","life","maxlife","color","size","grav","fade"]
    def __init__(self, x, y, vx, vy, life, color, size=3, grav=0.0, fade=True):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = self.maxlife = life
        self.color = color
        self.size  = size
        self.grav  = grav
        self.fade  = fade

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.grav
        self.vx *= 0.97
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        t = self.life / self.maxlife
        alpha = int(255 * t) if self.fade else 255
        s = max(1, int(self.size * t))
        c = tuple(min(255, max(0, int(self.color[i]))) for i in range(3))
        try:
            gfxdraw.filled_circle(surf, int(self.x), int(self.y), s,
                                  c + (alpha,))
        except:
            pygame.draw.circle(surf, c, (int(self.x), int(self.y)), s)

class ParticleSystem:
    def __init__(self, max_particles=2000):
        self.pool = []
        self.max  = max_particles

    def emit(self, x, y, vx=0, vy=0, spread=3, count=5,
             life=40, color=(255,200,100), size=4, grav=0.05, fade=True):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(0, spread)
            self.pool.append(Particle(
                x + random.uniform(-3,3),
                y + random.uniform(-3,3),
                vx + math.cos(angle)*speed,
                vy + math.sin(angle)*speed,
                life + random.randint(-life//4, life//4),
                color, size, grav, fade
            ))
        if len(self.pool) > self.max:
            self.pool = self.pool[-self.max:]

    def update_draw(self, surf):
        self.pool = [p for p in self.pool if p.update()]
        for p in self.pool:
            p.draw(surf)

ps = ParticleSystem(3000)

# ──────────────────────────────────────────────────────────────────
#  SOUND GENERATION  (procedural beeps — no files needed)
# ──────────────────────────────────────────────────────────────────
def gen_sound(freq=440, duration=0.12, vol=0.4, waveform="sine"):
    rate = 44100
    n    = int(rate * duration)
    buf  = bytearray(n * 2)
    for i in range(n):
        t  = i / rate
        env= min(1.0, (n-i)/max(1,n*0.1))  # fade out
        if   waveform == "sine":   s = math.sin(2*math.pi*freq*t)
        elif waveform == "square": s = 1.0 if math.sin(2*math.pi*freq*t) > 0 else -1.0
        elif waveform == "saw":    s = 2*(freq*t % 1) - 1
        else:                      s = random.uniform(-1,1)
        v  = int(s * env * vol * 32767)
        v  = clamp(v, -32768, 32767)
        buf[i*2]   = v & 0xFF
        buf[i*2+1] = (v >> 8) & 0xFF
    sound = pygame.mixer.Sound(buffer=bytes(buf))
    sound.set_volume(vol)
    return sound

try:
    SND_JUMP  = gen_sound(600, 0.08, 0.3, "sine")
    SND_DIE   = gen_sound(120, 0.5,  0.5, "square")
    SND_WIN   = gen_sound(880, 0.3,  0.4, "sine")
    SND_PORTAL= gen_sound(440, 0.2,  0.3, "saw")
    SND_HIT   = gen_sound(200, 0.15, 0.4, "square")
    SOUND_OK  = True
except:
    SOUND_OK  = False

def play(snd):
    if SOUND_OK:
        try: snd.play()
        except: pass

# ──────────────────────────────────────────────────────────────────
#  CAMERA
# ──────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.shake = 0.0
        self.ox, self.oy = 0.0, 0.0

    def hit(self, strength=12):
        self.shake = max(self.shake, strength)

    def update(self):
        if self.shake > 0.1:
            self.ox = random.uniform(-self.shake, self.shake)
            self.oy = random.uniform(-self.shake, self.shake)
            self.shake *= 0.78
        else:
            self.shake = 0
            self.ox = self.oy = 0

    def apply(self, surf):
        if self.shake > 0.5:
            dst = pygame.Surface((W, H))
            dst.blit(surf, (int(self.ox), int(self.oy)))
            surf.blit(dst, (0, 0))

cam = Camera()

# ──────────────────────────────────────────────────────────────────
#  TILE MAP LAYER
# ──────────────────────────────────────────────────────────────────
class Platform:
    def __init__(self, x, y, w, h, color=(60, 80, 120), deadly=False,
                 moving=False, mx=0, my=0, mrange=100, mspeed=1.5,
                 bounce=False, phase=False, phase_time=90):
        self.rect   = pygame.Rect(x, y, w, h)
        self.ox, self.oy = x, y
        self.color  = color
        self.deadly = deadly
        self.moving = moving
        self.mx, self.my = mx, my
        self.mrange = mrange
        self.mspeed = mspeed
        self.bounce = bounce
        self.phase  = phase
        self.phase_time = phase_time
        self.phase_timer = random.randint(0, phase_time)
        self.visible = True
        self.t = 0.0

    def update(self):
        self.t += 0.02
        if self.moving:
            s = math.sin(self.t * self.mspeed)
            self.rect.x = int(self.ox + self.mx * s * self.mrange)
            self.rect.y = int(self.oy + self.my * s * self.mrange)
        if self.phase:
            self.phase_timer = (self.phase_timer + 1) % (self.phase_time * 2)
            self.visible = self.phase_timer < self.phase_time

    def draw(self, surf, tick):
        if not self.visible: 
            # ghost flash
            if self.phase and (self.phase_time*2 - self.phase_timer) < 20:
                alpha_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
                t = (self.phase_time*2 - self.phase_timer) / 20
                alpha_surf.fill((*self.color, int(80*t)))
                surf.blit(alpha_surf, self.rect.topleft)
            return
        c = self.color
        if self.deadly:
            pulse = (math.sin(tick * 0.08) + 1) / 2
            c = lerpC((200, 20, 20), (255, 100, 50), pulse)
        elif self.moving:
            c = lerpC(self.color, (180, 220, 255), 0.4)
        pygame.draw.rect(surf, c, self.rect, border_radius=4)
        # Highlight edge
        pygame.draw.rect(surf, lerpC(c, (255,255,255), 0.3),
                         pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 3))

# ──────────────────────────────────────────────────────────────────
#  ENEMIES
# ──────────────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, x, y, etype="patrol", color=(200,50,50),
                 patrol_x1=0, patrol_x2=0, speed=2.0, size=18,
                 orbit_cx=0, orbit_cy=0, orbit_r=80, orbit_speed=0.02,
                 shoot_interval=0):
        self.x, self.y = float(x), float(y)
        self.etype  = etype
        self.color  = color
        self.speed  = speed
        self.size   = size
        self.px1, self.px2 = patrol_x1, patrol_x2
        self.dir    = 1
        self.ocx, self.ocy = float(orbit_cx), float(orbit_cy)
        self.or_    = orbit_r
        self.ospeed = orbit_speed
        self.angle  = random.uniform(0, math.tau)
        self.shoot_interval = shoot_interval
        self.shoot_timer    = 0
        self.bullets = []
        self.alive   = True
        self.t       = 0.0

    def update(self, player_x=0, player_y=0):
        self.t += 1
        if self.etype == "patrol":
            self.x += self.speed * self.dir
            if self.x < self.px1: self.dir =  1
            if self.x > self.px2: self.dir = -1
        elif self.etype == "orbit":
            self.angle += self.ospeed
            self.x = self.ocx + math.cos(self.angle) * self.or_
            self.y = self.ocy + math.sin(self.angle) * self.or_
        elif self.etype == "chase":
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += (dx/dist) * self.speed
                self.y += (dy/dist) * self.speed
        elif self.etype == "sine":
            self.x += self.speed
            self.y = self.ocy + math.sin(self.t * 0.05) * self.or_
            if self.x > self.px2: self.x = self.px1
        
        if self.shoot_interval > 0:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                self.shoot_timer = 0
                dx = player_x - self.x
                dy = player_y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    spd = 4.5
                    self.bullets.append({
                        "x": self.x, "y": self.y,
                        "vx": (dx/dist)*spd, "vy": (dy/dist)*spd,
                        "life": 180
                    })
        for b in self.bullets:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            b["life"] -= 1
        self.bullets = [b for b in self.bullets if b["life"] > 0]

    def get_rect(self):
        return pygame.Rect(int(self.x - self.size//2), int(self.y - self.size//2),
                           self.size, self.size)

    def draw(self, surf, tick):
        if not self.alive: return
        pulse = (math.sin(tick * 0.1) + 1) / 2
        c = lerpC(self.color, (255, 255, 255), pulse * 0.3)
        r = self.get_rect()
        # Glow
        glow_surf = pygame.Surface((r.w*4, r.h*4), pygame.SRCALPHA)
        gc = (*self.color, 40)
        pygame.draw.ellipse(glow_surf, gc, (0, 0, r.w*4, r.h*4))
        surf.blit(glow_surf, (r.x - r.w*1.5, r.y - r.h*1.5))
        # Body
        circle_aa(surf, c, (self.x, self.y), self.size//2)
        # Eyes
        ex = self.x + self.size//5
        ey = self.y - self.size//6
        circle_aa(surf, (255,255,255), (ex, ey), 3)
        circle_aa(surf, (0,0,0), (ex+1, ey), 2)
        # Bullets
        for b in self.bullets:
            circle_aa(surf, (255, 220, 50), (b["x"], b["y"]), 5)
            # bullet trail
            ps.emit(b["x"], b["y"], count=1, life=8, color=(255,180,0), size=3, spread=0.5)

# ──────────────────────────────────────────────────────────────────
#  PORTAL / COLLECTIBLE
# ──────────────────────────────────────────────────────────────────
class Portal:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.r  = 30
        self.t  = 0.0

    def update(self):
        self.t += 0.04
        ps.emit(self.x + math.cos(self.t)*self.r*0.7,
                self.y + math.sin(self.t)*self.r*0.7,
                count=1, life=30, color=hsv(self.t/(math.pi*2), 0.8, 1.0), size=4, spread=1)

    def draw(self, surf):
        for ring in range(4, 0, -1):
            alpha = 80 - ring*15
            c = (*hsv(self.t/(math.pi*2) + ring*0.1, 0.9, 1.0), alpha)
            s = self.r + ring * 6 + int(math.sin(self.t*2)*4)
            gls = pygame.Surface((s*2+4, s*2+4), pygame.SRCALPHA)
            pygame.draw.circle(gls, c, (s+2, s+2), s)
            surf.blit(gls, (self.x - s - 2, self.y - s - 2))
        circle_aa(surf, hsv(self.t/(math.pi*2), 0.6, 1.0), (self.x, self.y), self.r)
        draw_text(surf, "EXIT", (self.x, self.y - self.r - 20),
                  (255,255,200), font=FONT_TINY, center=True)

# ──────────────────────────────────────────────────────────────────
#  LEVEL DEFINITIONS — 20 WORLDS
# ──────────────────────────────────────────────────────────────────
def mk_plat(*args, **kw): return Platform(*args, **kw)
def mk_enemy(*args, **kw): return Enemy(*args, **kw)

# Color palettes per world
PALETTES = [
    ((10,5,20),   (60,40,120)),    # 0  Void
    ((5,15,5),    (30,80,30)),     # 1  Forest
    ((20,5,5),    (100,20,20)),    # 2  Fire
    ((5,20,30),   (20,80,130)),    # 3  Ocean
    ((20,15,0),   (100,80,0)),     # 4  Desert
    ((0,15,20),   (0,70,90)),      # 5  Ice
    ((15,0,15),   (70,0,70)),      # 6  Neon
    ((20,10,0),   (90,40,0)),      # 7  Lava
    ((0,0,20),    (0,0,100)),      # 8  Space
    ((15,15,15),  (80,80,80)),     # 9  Glitch
    ((10,0,20),   (50,0,100)),     # 10 Dream
    ((0,20,0),    (0,100,0)),      # 11 Toxic
    ((20,0,10),   (100,0,50)),     # 12 Blood Moon
    ((5,5,20),    (25,25,100)),    # 13 Crystal
    ((20,5,0),    (100,25,0)),     # 14 Volcanic
    ((0,20,20),   (0,100,100)),    # 15 Cyber
    ((10,10,0),   (60,60,0)),      # 16 Ruins
    ((15,0,5),    (80,0,25)),      # 17 Nightmare
    ((0,5,15),    (0,25,80)),      # 18 Abyss
    ((15,15,15),  (200,200,200)),  # 19 FINAL
]

PLAT_COLS = [
    (70, 60, 130), (50, 100, 60),  (140, 60, 40),  (50, 100, 160),
    (150, 130, 50),(50, 140, 160), (160, 50, 160),  (160, 100, 40),
    (40, 40, 160), (100,100,100),  (100, 50, 160),  (50, 160, 50),
    (160, 50, 80), (60, 60, 180),  (180, 80, 40),   (40, 180, 180),
    (130, 120, 50),(140, 40, 60),  (40, 60, 150),   (200, 200, 200),
]

LEVEL_MSGS = [
    "Welcome. This is where hope comes to die.",
    "The forest whispers your failures.",
    "Everything burns. Including your chances.",
    "The tides care nothing for your struggle.",
    "The desert devours the weak.",
    "One wrong step and the ice shatters.",
    "The neon maze has no escape.",
    "Lava remembers everyone who falls in.",
    "In space, no one hears you restart.",
    "Reality is a lie. So is this platform.",
    "Dreams decay into nightmares at this level.",
    "The toxins are patient. You are not.",
    "The blood moon rises on your suffering.",
    "Crystal clear: you're going to die here.",
    "The volcano has erupted before. Often.",
    "Cyber demons don't forgive. Neither do we.",
    "Ancient ruins. Ancient traps. Ancient pain.",
    "This nightmare was designed for you.",
    "The abyss has been waiting for you.",
    "FINAL WORLD. This is everything. Good luck.",
]

def build_level(idx):
    pc = PLAT_COLS[idx % len(PLAT_COLS)]
    dc = (200, 30, 30)   # deadly platform color
    mc = (100, 200, 255) # moving platform color
    
    platforms = []
    enemies   = []
    
    # Floor and walls for all levels
    def floor():
        return [
            mk_plat(0, H-30, W, 30, pc),           # floor
            mk_plat(0, 0, 20, H, pc),               # left wall
            mk_plat(W-20, 0, 20, H, pc),            # right wall
        ]

    # ─── WORLD 1 ─────────────────────────────────────────────────
    if idx == 0:
        platforms = floor() + [
            mk_plat(100, 560, 200, 18, pc),
            mk_plat(350, 490, 200, 18, pc),
            mk_plat(600, 420, 200, 18, pc),
            mk_plat(850, 350, 200, 18, pc),
            mk_plat(600, 260, 200, 18, pc),
            mk_plat(350, 170, 200, 18, pc),
            mk_plat(100, 100, 220, 18, pc),
        ]
        enemies = [
            mk_enemy(350, 460, "patrol", (200,50,50), 350, 540, speed=2.5),
            mk_enemy(600, 390, "patrol", (220,80,30), 600, 790, speed=3.0),
        ]
        start = (50, 520); goal = (200, 60)

    # ─── WORLD 2 ─────────────────────────────────────────────────
    elif idx == 1:
        platforms = floor() + [
            mk_plat(80,  560, 160, 18, pc),
            mk_plat(300, 500, 120, 18, pc, moving=True, mx=1, mrange=80, mspeed=1.2),
            mk_plat(500, 440, 120, 18, pc),
            mk_plat(680, 380, 100, 18, pc, moving=True, mx=1, mrange=60, mspeed=1.8),
            mk_plat(850, 320, 180, 18, pc),
            mk_plat(680, 230, 120, 18, pc),
            mk_plat(450, 160, 200, 18, pc),
            mk_plat(200, 100, 180, 18, pc),
            mk_plat(400, 540, 60, 18, dc, deadly=True),
            mk_plat(760, 400, 60, 18, dc, deadly=True),
        ]
        enemies = [
            mk_enemy(500, 410, "patrol", (200,80,50), 500, 620, speed=3.0),
            mk_enemy(850, 290, "patrol", (180,50,200), 850, 1030, speed=2.5),
        ]
        start = (50, 530); goal = (250, 60)

    # ─── WORLD 3 ─────────────────────────────────────────────────
    elif idx == 2:
        platforms = floor() + [
            mk_plat(80,  560, 140, 18, pc),
            mk_plat(280, 490, 100, 18, pc, moving=True, mx=1, mrange=100, mspeed=2.0),
            mk_plat(480, 430, 100, 18, dc, deadly=True),
            mk_plat(630, 380, 140, 18, pc),
            mk_plat(830, 310, 80, 18, pc, moving=True, mx=1, mrange=80, mspeed=2.5),
            mk_plat(650, 240, 120, 18, pc),
            mk_plat(430, 180, 100, 18, pc),
            mk_plat(220, 130, 160, 18, pc),
            mk_plat(50,  80,  200, 18, pc),
            mk_plat(500, 560, 80,  18, dc, deadly=True),
            mk_plat(750, 560, 80,  18, dc, deadly=True),
        ]
        enemies = [
            mk_enemy(630, 350, "patrol", (230,60,60), 630, 770, speed=3.5),
            mk_enemy(430, 150, "orbit",  (180,60,230), orbit_cx=430, orbit_cy=180, orbit_r=60, orbit_speed=0.04),
        ]
        start = (50, 530); goal = (100, 50)

    # ─── WORLD 4 ─────────────────────────────────────────────────
    elif idx == 3:
        platforms = floor() + [
            mk_plat(80,  560, 120, 18, pc),
            mk_plat(260, 490, 80,  18, pc, phase=True, phase_time=70),
            mk_plat(420, 430, 100, 18, pc),
            mk_plat(580, 360, 80,  18, pc, phase=True, phase_time=60),
            mk_plat(740, 290, 120, 18, pc),
            mk_plat(920, 220, 80,  18, pc, moving=True, mx=0, my=1, mrange=60, mspeed=2.0),
            mk_plat(720, 150, 140, 18, pc),
            mk_plat(480, 100, 200, 18, pc),
            mk_plat(240, 130, 140, 18, pc),
            mk_plat(50,  80,  200, 18, pc),
            mk_plat(350, 570, 100, 18, dc, deadly=True),
            mk_plat(650, 570, 100, 18, dc, deadly=True),
        ]
        enemies = [
            mk_enemy(420, 400, "patrol", (230,100,40), 420, 560, speed=4.0),
            mk_enemy(740, 260, "orbit",  (200,50,50),  orbit_cx=820, orbit_cy=290, orbit_r=80, orbit_speed=0.05),
            mk_enemy(480, 70,  "patrol", (160,60,230), 480, 680, speed=3.5),
        ]
        start = (50, 530); goal = (100, 50)

    # ─── WORLD 5 ─────────────────────────────────────────────────
    elif idx == 4:
        platforms = floor() + [
            mk_plat(80,  560, 100, 18, pc),
            mk_plat(240, 490, 80,  18, pc, moving=True, mx=1, mrange=120, mspeed=2.5),
            mk_plat(500, 430, 80,  18, pc, phase=True, phase_time=55),
            mk_plat(700, 370, 100, 18, pc),
            mk_plat(880, 290, 80,  18, pc, moving=True, mx=0, my=1, mrange=80, mspeed=3.0),
            mk_plat(700, 200, 80,  18, pc, phase=True, phase_time=50),
            mk_plat(500, 140, 100, 18, pc),
            mk_plat(280, 90,  120, 18, pc),
            mk_plat(80,  90,  180, 18, pc),
            mk_plat(350, 570, 80,  18, dc, deadly=True),
            mk_plat(600, 570, 80,  18, dc, deadly=True),
            mk_plat(850, 570, 80,  18, dc, deadly=True),
        ]
        enemies = [
            mk_enemy(240, 460, "patrol",  (230,80,50),  240, 360, speed=4.0),
            mk_enemy(700, 340, "orbit",   (200,50,200), orbit_cx=740, orbit_cy=370, orbit_r=70, orbit_speed=0.06),
            mk_enemy(500, 110, "patrol",  (50,200,200), 500, 620, speed=4.5),
            mk_enemy(600, 300, "sine",    (200,150,50), patrol_x1=200, patrol_x2=900, orbit_cy=300, orbit_r=60, speed=3.0),
        ]
        start = (50, 530); goal = (130, 50)

    # ─── WORLDS 6–19: programmatically generated with escalating difficulty ──
    else:
        diff = (idx - 5) / 14.0  # 0..1
        # Build a grid-like path with increasing hazards
        steps = 7 + idx // 3
        xs    = [80] + [random.randint(100, W-200) for _ in range(steps-2)] + [W-200]
        ys    = [H-80]
        for i in range(1, steps):
            prev = ys[-1]
            ys.append(max(80, prev - random.randint(40, 90)))
        
        platforms = floor()
        # Main path
        for i, (x, y) in enumerate(zip(xs, ys)):
            w = max(60, 180 - idx*5)
            is_deadly  = random.random() < diff * 0.4
            is_moving  = random.random() < diff * 0.6
            is_phasing = random.random() < diff * 0.4
            c = dc if is_deadly else pc
            p = mk_plat(x, y, w, 18, c,
                        deadly=is_deadly,
                        moving=(is_moving and not is_deadly),
                        mx=random.choice([-1,0,1]),
                        my=random.choice([-1,0,1]),
                        mrange=50+idx*5,
                        mspeed=1.0+diff*3,
                        phase=(is_phasing and not is_deadly and not is_moving),
                        phase_time=max(25, 80-idx*3))
            platforms.append(p)

        # Extra deadly spikes on floor
        for i in range(idx // 2):
            sx = random.randint(100, W-200)
            platforms.append(mk_plat(sx, H-30, 60, 30, dc, deadly=True))

        # Enemy count & types scale with level
        enemy_count = 2 + idx // 2
        for i in range(enemy_count):
            etype = random.choice(["patrol", "orbit", "chase", "sine"])
            spd   = 2.5 + diff * 4.5
            ec    = hsv(random.random(), 0.8, 1.0)
            if etype == "patrol":
                ex = random.randint(150, W-150)
                ey = random.randint(200, H-100)
                enemies.append(mk_enemy(ex, ey, "patrol", ec,
                    patrol_x1=ex-120, patrol_x2=ex+120, speed=spd))
            elif etype == "orbit":
                cx, cy = random.randint(300, W-300), random.randint(200, H-200)
                enemies.append(mk_enemy(cx, cy, "orbit", ec,
                    orbit_cx=cx, orbit_cy=cy, orbit_r=60+idx*4,
                    orbit_speed=0.02+diff*0.06))
            elif etype == "chase":
                ex = random.randint(200, W-200)
                ey = random.randint(100, H-200)
                enemies.append(mk_enemy(ex, ey, "chase", ec, speed=spd*0.6))
            else:
                ey = random.randint(200, H-200)
                enemies.append(mk_enemy(200, ey, "sine", ec,
                    patrol_x1=100, patrol_x2=W-100,
                    orbit_cy=ey, orbit_r=60+idx*3, speed=spd*0.7))
            
            # Add shooters at high levels
            if idx >= 10 and random.random() < 0.4:
                cx = random.randint(300, W-300)
                cy = random.randint(200, H-300)
                enemies.append(mk_enemy(cx, cy, "orbit", (255,200,50),
                    orbit_cx=cx, orbit_cy=cy, orbit_r=40,
                    orbit_speed=0.03, shoot_interval=max(40, 100-idx*3)))

        start = (50, H-80)
        goal  = (W-100, 80)

    return platforms, enemies, start, goal

# ──────────────────────────────────────────────────────────────────
#  JOYSTICK UI WIDGET
# ──────────────────────────────────────────────────────────────────
class Joystick:
    def __init__(self, x, y, radius=55):
        self.base = (x, y)
        self.r    = radius
        self.stick = [float(x), float(y)]
        self.drag  = False
        self.dx = self.dy = 0.0

    def handle(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if math.hypot(e.pos[0]-self.base[0], e.pos[1]-self.base[1]) <= self.r:
                self.drag = True
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.drag = False
            self.stick = list(self.base)
            self.dx = self.dy = 0.0
        elif e.type == pygame.MOUSEMOTION and self.drag:
            dx = e.pos[0] - self.base[0]
            dy = e.pos[1] - self.base[1]
            d  = math.hypot(dx, dy)
            if d > self.r:
                dx, dy = dx/d*self.r, dy/d*self.r
            self.stick = [self.base[0]+dx, self.base[1]+dy]
            self.dx, self.dy = dx/self.r, dy/self.r

    def draw(self, surf):
        # Outer ring
        gls = pygame.Surface((self.r*2+20, self.r*2+20), pygame.SRCALPHA)
        pygame.draw.circle(gls, (255,255,255,25), (self.r+10, self.r+10), self.r)
        pygame.draw.circle(gls, (255,255,255,60), (self.r+10, self.r+10), self.r, 2)
        surf.blit(gls, (self.base[0]-self.r-10, self.base[1]-self.r-10))
        # Stick
        sx, sy = int(self.stick[0]), int(self.stick[1])
        sr = int(self.r * 0.42)
        gs = pygame.Surface((sr*2+10, sr*2+10), pygame.SRCALPHA)
        pygame.draw.circle(gs, (255,255,255,180), (sr+5, sr+5), sr)
        surf.blit(gs, (sx-sr-5, sy-sr-5))

joystick = Joystick(90, H-90)

# ──────────────────────────────────────────────────────────────────
#  PLAYER
# ──────────────────────────────────────────────────────────────────
class Player:
    W, H_SIZE = 22, 22
    GRAVITY   = 0.55
    JUMP_VEL  = -12.5
    SPEED     = 5.5

    def __init__(self):
        self.rect = pygame.Rect(0, 0, self.W, self.H_SIZE)
        self.vx   = 0.0
        self.vy   = 0.0
        self.on_ground = False
        self.trail = []
        self.t     = 0

    def spawn(self, x, y):
        self.rect.x, self.rect.y = x, y
        self.vx = self.vy = 0.0
        self.trail.clear()

    def update(self, platforms, dx, dy, jump):
        self.t += 1

        # Horizontal
        self.vx = dx * self.SPEED

        # Jump — check BEFORE applying gravity so on_ground is still True
        # from the previous frame's collision resolution
        if jump and self.on_ground:
            self.vy = self.JUMP_VEL
            play(SND_JUMP)
            ps.emit(self.rect.centerx, self.rect.bottom,
                    count=10, life=25, color=(180,220,255), size=4, spread=3, grav=-0.1)

        # Vertical physics
        self.vy += self.GRAVITY
        self.vy = clamp(self.vy, -20, 20)

        self.rect.x += int(self.vx)
        self.rect.x = clamp(self.rect.x, 20, W-40)
        self._resolve_x(platforms)

        self.rect.y += int(self.vy)
        self.on_ground = False
        self._resolve_y(platforms)

        # Trail
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 18: self.trail.pop(0)

    def _resolve_x(self, platforms):
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vx > 0: self.rect.right = p.rect.left
                elif self.vx < 0: self.rect.left = p.rect.right

    def _resolve_y(self, platforms):
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vy > 0:
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = p.rect.bottom
                    self.vy = 0

    def check_deadly(self, platforms):
        for p in platforms:
            if p.deadly and p.visible and self.rect.colliderect(p.rect):
                return True
        return False

    def draw(self, surf):
        # Trail
        for i, (tx, ty) in enumerate(self.trail):
            t = i / len(self.trail)
            c = hsv(self.t * 0.005 + t * 0.15, 0.9, 1.0)
            alpha = int(120 * t)
            s = max(2, int(6 * t))
            gs = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*c, alpha), (s, s), s)
            surf.blit(gs, (tx - s, ty - s))

        # Body glow
        c = hsv(self.t * 0.005, 0.7, 1.0)
        gls = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(gls, (*c, 50), (30, 30), 28)
        surf.blit(gls, (self.rect.centerx-30, self.rect.centery-30))

        # Body
        pygame.draw.rect(surf, c, self.rect, border_radius=6)
        # Highlight
        pygame.draw.rect(surf, (255,255,255), 
                         pygame.Rect(self.rect.x+3, self.rect.y+3, self.rect.w-6, 4),
                         border_radius=3)
        # Eyes
        ey = self.rect.y + 6
        for ex_off in [5, 13]:
            circle_aa(surf, (255,255,255), (self.rect.x + ex_off, ey), 3)
            circle_aa(surf, (0,0,0),       (self.rect.x + ex_off + 1, ey), 2)

player = Player()

# ──────────────────────────────────────────────────────────────────
#  BACKGROUND RENDERER
# ──────────────────────────────────────────────────────────────────
class Background:
    def __init__(self):
        self.stars = [(random.randint(0,W), random.randint(0,H),
                       random.uniform(0.5, 2.5)) for _ in range(180)]
        self.t = 0

    def draw(self, surf, idx):
        self.t += 1
        c1, c2 = PALETTES[idx % len(PALETTES)]
        # Gradient sky
        for y in range(0, H, 3):
            t = y / H
            c = lerpC(c1, c2, t)
            pygame.draw.rect(surf, c, (0, y, W, 3))
        
        # Stars / particles
        for sx, sy, s in self.stars:
            twinkle = (math.sin(self.t * 0.04 + sx) + 1) / 2
            brightness = int(100 + 155 * twinkle)
            c = (brightness, brightness, min(255, brightness + 40))
            pygame.draw.circle(surf, c, (sx, sy), max(1, int(s * twinkle)))

        # Scanlines (subtle)
        sl_surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 4):
            pygame.draw.line(sl_surf, (0,0,0,12), (0,y), (W,y))
        surf.blit(sl_surf, (0,0))

bg = Background()

# ──────────────────────────────────────────────────────────────────
#  HUD
# ──────────────────────────────────────────────────────────────────
def draw_hud(surf, level_idx, lives, tick):
    # Lives
    for i in range(5):
        filled = i < lives
        c = (255, 80, 80) if filled else (60, 60, 80)
        hx = W - 160 + i * 28
        hy = 20
        # Heart shape (simple)
        heart_pts = []
        for a in range(30):
            ang = a / 30 * math.tau
            r   = 10 if filled else 8
            hx2 = hx + r * math.sin(ang) * (1 + 0.3*math.cos(4*ang))
            hy2 = hy - r * math.cos(ang) * (1 - 0.3*abs(math.sin(ang)))
            heart_pts.append((hx2, hy2))
        if len(heart_pts) >= 3:
            pygame.draw.polygon(surf, c, heart_pts)

    # Level name & number
    name = LEVEL_MSGS[level_idx] if level_idx < len(LEVEL_MSGS) else "???"
    draw_text(surf, f"WORLD {level_idx+1:02d}/20", (W//2, 18),
              color=(255,255,200), font=FONT_MD, center=True, shadow=True)
    draw_text(surf, name, (W//2, 46),
              color=(200,200,255), font=FONT_TINY, center=True, shadow=True)

    # Controls hint
    draw_text(surf, "WASD/Arrows: Move  |  Space/Up: Jump  |  ESC: Pause",
              (W//2, H-18), color=(120,120,180), font=FONT_TINY, center=True)

    # Best world
    draw_text(surf, f"BEST: W{save_data['best']+1}",
              (20, 20), color=(180,180,255), font=FONT_TINY)

    # Deaths counter
    draw_text(surf, f"DEATHS: {save_data['deaths']}",
              (20, 40), color=(200,100,100), font=FONT_TINY)

# ──────────────────────────────────────────────────────────────────
#  SCREENS
# ──────────────────────────────────────────────────────────────────
def screen_menu(level_idx):
    surf = pygame.Surface((W, H))
    t    = pygame.time.get_ticks() / 1000.0
    
    # BG
    for y in range(0, H, 2):
        p = y / H
        c = lerpC((5,0,15), (20,5,50), p)
        pygame.draw.rect(surf, c, (0, y, W, 2))

    # Animated title glow
    for ring in range(5, 0, -1):
        alpha = 15 * ring
        gls   = pygame.Surface((W, 200), pygame.SRCALPHA)
        c     = (*hsv(t*0.05, 0.8, 1.0), alpha)
        pygame.draw.ellipse(gls, c, (100, 10, W-200, 160))
        surf.blit(gls, (0, 80))

    # Title
    title1 = FONT_TITLE.render("EMOTION", True, hsv(t*0.05, 0.9, 1.0))
    title2 = FONT_TITLE.render("ARCHITECT", True, hsv(t*0.05+0.15, 0.9, 1.0))
    sub    = FONT_LG.render("U L T I M A T E   H A R D C O R E", True, (220, 220, 255))
    
    surf.blit(title1, (W//2 - title1.get_width()//2, 80))
    surf.blit(title2, (W//2 - title2.get_width()//2, 175))
    surf.blit(sub,    (W//2 - sub.get_width()//2, 280))

    # Stats
    draw_text(surf, f"Current World: {level_idx+1} / 20", (W//2, 340),
              (200,255,200), FONT_MD, center=True, shadow=True)
    draw_text(surf, f"Best Reached: World {save_data['best']+1}", (W//2, 375),
              (180,180,255), FONT_SM, center=True)
    draw_text(surf, f"Total Deaths: {save_data['deaths']}   Runs: {save_data['runs']}", (W//2, 400),
              (180,120,120), FONT_SM, center=True)

    # Buttons
    btn_play = pygame.Rect(W//2-120, 450, 240, 55)
    btn_rst  = pygame.Rect(W//2-120, 520, 240, 45)
    
    # Play button glow
    for r in range(4, 0, -1):
        bc = (*hsv(t*0.1, 0.8, 1.0), 30)
        gs = pygame.Surface((btn_play.w+r*10, btn_play.h+r*10), pygame.SRCALPHA)
        pygame.draw.rect(gs, bc, (0,0,btn_play.w+r*10, btn_play.h+r*10), border_radius=14)
        surf.blit(gs, (btn_play.x-r*5, btn_play.y-r*5))
    
    pygame.draw.rect(surf, hsv(t*0.1, 0.7, 0.9), btn_play, border_radius=12)
    pygame.draw.rect(surf, (255,255,255), btn_play, 2, border_radius=12)
    draw_text(surf, "► ENTER THE VOID", (btn_play.centerx, btn_play.centery),
              (0,0,0), FONT_MD, center=True)

    pygame.draw.rect(surf, (60,30,30), btn_rst, border_radius=10)
    pygame.draw.rect(surf, (150,50,50), btn_rst, 2, border_radius=10)
    draw_text(surf, "RESET ALL PROGRESS", (btn_rst.centerx, btn_rst.centery),
              (200,100,100), FONT_SM, center=True)

    draw_text(surf, "20 WORLDS OF SUFFERING  |  NO MERCY  |  NO CHECKPOINTS",
              (W//2, H-30), (120,80,80), FONT_TINY, center=True)

    # Floating particles
    for _ in range(2):
        ps.emit(random.randint(100, W-100), H-10,
                count=1, vy=-1.5, life=120, spread=1.5,
                color=hsv(t*0.1 + random.random()*0.2, 0.7, 1.0), size=3, grav=-0.01)

    ps.update_draw(surf)
    return surf, btn_play, btn_rst

def screen_gameover():
    surf = pygame.Surface((W, H))
    t    = pygame.time.get_ticks() / 1000.0
    
    for y in range(0, H, 2):
        p = y / H
        c = lerpC((30,0,0), (80,10,10), p)
        pygame.draw.rect(surf, c, (0, y, W, 2))

    txt = FONT_TITLE.render("GAME OVER", True, (255,40,40))
    surf.blit(txt, (W//2 - txt.get_width()//2, 150))

    draw_text(surf, "The void has consumed your soul.", (W//2, 290),
              (220,150,150), FONT_MD, center=True, shadow=True)
    draw_text(surf, "All progress has been erased.", (W//2, 330),
              (180,100,100), FONT_SM, center=True)
    draw_text(surf, f"You made it to World {save_data['best']+1}.", (W//2, 370),
              (200,150,100), FONT_SM, center=True)

    btn = pygame.Rect(W//2-140, 440, 280, 60)
    pygame.draw.rect(surf, (140,20,20), btn, border_radius=12)
    pygame.draw.rect(surf, (255,60,60), btn, 2, border_radius=12)
    draw_text(surf, "TRY AGAIN (FROM SCRATCH)", (btn.centerx, btn.centery),
              (255,200,200), FONT_SM, center=True)

    ps.update_draw(surf)
    return surf, btn

def screen_win():
    surf = pygame.Surface((W, H))
    t    = pygame.time.get_ticks() / 1000.0

    for y in range(0, H, 2):
        c = lerpC((5,5,20), (20,10,60), y/H)
        pygame.draw.rect(surf, c, (0, y, W, 2))

    txt = FONT_TITLE.render("YOU WIN", True, hsv(t*0.1, 0.8, 1.0))
    surf.blit(txt, (W//2 - txt.get_width()//2, 120))
    draw_text(surf, "You are the Emotion Architect.", (W//2, 270),
              (220,220,255), FONT_MD, center=True, shadow=True)
    draw_text(surf, "All 20 worlds conquered. You are inhuman.", (W//2, 310),
              (180,255,180), FONT_SM, center=True)

    for _ in range(8):
        ps.emit(random.randint(0,W), random.randint(0,H),
                count=3, life=80, spread=4,
                color=hsv(random.random(), 0.9, 1.0), size=6, grav=-0.02)
    
    btn = pygame.Rect(W//2-120, 420, 240, 55)
    pygame.draw.rect(surf, (30,80,30), btn, border_radius=12)
    pygame.draw.rect(surf, (100,255,100), btn, 2, border_radius=12)
    draw_text(surf, "PLAY AGAIN", (btn.centerx, btn.centery),
              (200,255,200), FONT_MD, center=True)

    ps.update_draw(surf)
    return surf, btn

# ──────────────────────────────────────────────────────────────────
#  MAIN GAME CLASS
# ──────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.state     = "MENU"
        self.lives     = 5
        self.level_idx = save_data["level"]
        self.tick      = 0
        self.platforms = []
        self.enemies   = []
        self.portal    = None
        self.start_pos = (80, 560)
        self.flash_alpha = 0
        self.flash_color = (255,255,255)
        self.death_anim  = 0
        self.load_level(self.level_idx)

    def load_level(self, idx):
        random.seed(idx * 7 + 13)  # deterministic per level
        self.level_idx   = idx
        self.platforms, self.enemies, self.start_pos, goal = build_level(idx)
        self.portal      = Portal(*goal)
        player.spawn(*self.start_pos)
        save_data["best"] = max(save_data.get("best", 0), idx)
        write_save(save_data)

    def flash(self, color=(255,255,255), strength=200):
        self.flash_alpha = strength
        self.flash_color = color

    def die(self):
        cam.hit(20)
        play(SND_DIE)
        ps.emit(player.rect.centerx, player.rect.centery,
                count=30, life=60, spread=7, color=(255,80,80), size=6, grav=0.1)
        self.flash((255,50,50), 220)
        save_data["deaths"] += 1
        write_save(save_data)
        self.lives -= 1
        if self.lives <= 0:
            self.state = "GAME_OVER"
            save_data["level"] = 0
            save_data["best"]  = 0
            write_save(save_data)
        else:
            player.spawn(*self.start_pos)

    def next_level(self):
        play(SND_WIN)
        cam.hit(8)
        self.flash((100,255,200), 180)
        ps.emit(player.rect.centerx, player.rect.centery,
                count=50, life=90, spread=8,
                color=(100,255,200), size=5, grav=-0.05)
        nxt = self.level_idx + 1
        if nxt >= 20:
            self.state = "WIN"
        else:
            save_data["level"] = nxt
            write_save(save_data)
            self.load_level(nxt)
            self.state = "PLAY"

    def run(self):
        while True:
            self.tick += 1
            
            # ── MENU ─────────────────────────────────────────────
            if self.state == "MENU":
                surf, btn_play, btn_rst = screen_menu(self.level_idx)
                screen.blit(surf, (0,0))
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        if btn_play.collidepoint(e.pos):
                            save_data["runs"] += 1
                            write_save(save_data)
                            self.state = "PLAY"
                        if btn_rst.collidepoint(e.pos):
                            save_data.update({"level":0,"best":0,"deaths":0,"runs":0})
                            write_save(save_data)
                            self.level_idx = 0
                            self.lives     = 5
                            self.load_level(0)
                    if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "PLAY"

            # ── GAME OVER ─────────────────────────────────────────
            elif self.state == "GAME_OVER":
                surf, btn = screen_gameover()
                screen.blit(surf, (0,0))
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        if btn.collidepoint(e.pos):
                            save_data.update({"level":0,"best":0,"deaths":0})
                            write_save(save_data)
                            self.lives     = 5
                            self.level_idx = 0
                            self.load_level(0)
                            self.state = "MENU"

            # ── WIN ───────────────────────────────────────────────
            elif self.state == "WIN":
                surf, btn = screen_win()
                screen.blit(surf, (0,0))
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        if btn.collidepoint(e.pos):
                            save_data.update({"level":0,"best":0,"deaths":0,"runs":0})
                            write_save(save_data)
                            self.lives     = 5
                            self.level_idx = 0
                            self.load_level(0)
                            self.state = "MENU"

            # ── PLAY ──────────────────────────────────────────────
            elif self.state == "PLAY":
                # Events
                jump = False
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: sys.exit()
                    joystick.handle(e)
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:
                            self.state = "MENU"
                        if e.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                            jump = True
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        # Tap top half = jump
                        if e.pos[1] < H // 2:
                            jump = True

                # Input
                keys = pygame.key.get_pressed()
                dx   = 0.0
                if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
                dx += joystick.dx

                # Update platforms
                for p in self.platforms:
                    p.update()

                # Update player
                player.update(self.platforms, dx, 0, jump)

                # Update enemies
                for en in self.enemies:
                    en.update(player.rect.centerx, player.rect.centery)

                # Check death: fell off screen
                if player.rect.top > H:
                    self.die()

                # Check death: deadly platforms
                if player.check_deadly(self.platforms):
                    self.die()

                # Check death: enemy collision
                for en in self.enemies:
                    if en.alive and player.rect.colliderect(en.get_rect()):
                        self.die()
                        break
                    for b in en.bullets:
                        br = pygame.Rect(int(b["x"])-6, int(b["y"])-6, 12, 12)
                        if player.rect.colliderect(br):
                            self.die()
                            en.bullets.remove(b)
                            break

                # Portal
                self.portal.update()
                pr = pygame.Rect(self.portal.x - self.portal.r, self.portal.y - self.portal.r,
                                 self.portal.r*2, self.portal.r*2)
                if player.rect.colliderect(pr):
                    play(SND_PORTAL)
                    self.next_level()

                # Ambient particles
                if self.tick % 8 == 0:
                    ps.emit(random.randint(0, W), H,
                            count=1, vy=-0.8, life=200, spread=0.5,
                            color=PALETTES[self.level_idx % len(PALETTES)][1],
                            size=2, grav=-0.005, fade=True)

                # ── DRAW ─────────────────────────────────────────
                bg.draw(screen, self.level_idx)
                
                for p in self.platforms:
                    p.draw(screen, self.tick)

                for en in self.enemies:
                    en.draw(screen, self.tick)

                self.portal.draw(screen)
                player.draw(screen)
                ps.update_draw(screen)

                # Flash overlay
                if self.flash_alpha > 0:
                    fl = pygame.Surface((W, H), pygame.SRCALPHA)
                    fl.fill((*self.flash_color, int(self.flash_alpha)))
                    screen.blit(fl, (0,0))
                    self.flash_alpha = max(0, self.flash_alpha - 12)

                # HUD
                draw_hud(screen, self.level_idx, self.lives, self.tick)
                
                # Joystick
                joystick.draw(screen)

                # Camera shake
                cam.update()
                cam.apply(screen)

            pygame.display.flip()
            clock.tick(FPS)

# ──────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()
