"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  EMOTION ARCHITECT  ◆  ULTIMATE EDITION  ◆                                ║
║  20 Worlds · 3D Phong Balls · Weather · Combos · Parallax · World Cards    ║
║  Pause Menu · Edge Danger · Squish/Stretch · Speed Lines · Coin Magnet     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import math, random, sys, os, json, colorsys, time as _time
import pygame
from pygame import gfxdraw
from src.sprite_animator import SpriteAnimator
from src.levels.level_manager import LevelManager
from src.settings.settings_manager import SettingsManager
from src.story.emotion_system import EmotionSystem
from src.emotion.emotion_profiles import get_emotion_profile
from src.skills.skill_tree import SkillTree
from src.world.world_events import WorldEventSystem

pygame.init()
MIXER_OK = True
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)
except Exception:
    MIXER_OK = False

W, H   = 1280, 720
FPS    = 60
APP_NAME = "EmotionArchitect"
SAVE_BASENAME = "save_data.json"

# When frozen by PyInstaller --onefile, data files live in sys._MEIPASS.
# When running from source they live next to run.py.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resource_path(*parts):
    """Return absolute path to a bundled resource (works frozen & from source)."""
    return os.path.join(BASE_DIR, *parts)

def get_user_data_dir():
    """Persistent per-user folder for save data and settings (never temp)."""
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d

LEVEL_MANAGER = LevelManager()
TOTAL_LEVELS = LEVEL_MANAGER.total_levels
SETTINGS = SettingsManager(os.path.join(get_user_data_dir(), "settings.json"))

def get_save_path():
    return os.path.join(get_user_data_dir(), SAVE_BASENAME)

SAVE = get_save_path()
LEGACY_SAVE = os.path.join(os.getcwd(), "ea_v5.json")

# Canvas and Display Initialization
screen = pygame.Surface((W, H))
window = None

def apply_resolution_settings(*args):
    global window
    res_str = SETTINGS.get("resolution", "1280x720")
    try: w_disp, h_disp = map(int, res_str.split('x'))
    except Exception: w_disp, h_disp = 1280, 720
    flags = pygame.FULLSCREEN if SETTINGS.get("fullscreen") else 0
    window = pygame.display.set_mode((w_disp, h_disp), flags)

apply_resolution_settings()
SETTINGS.add_listener("resolution_changed", apply_resolution_settings)
SETTINGS.add_listener("fullscreen_changed", apply_resolution_settings)

pygame.display.set_caption("EMOTION ARCHITECT: ULTIMATE")
_icon_path = resource_path("assets", "icon.ico")
if os.path.exists(_icon_path):
    try:
        _icon = pygame.image.load(_icon_path)
        pygame.display.set_icon(_icon)
    except Exception:
        pass
clock  = pygame.time.Clock()

# ═══════════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════════
def mkf(names, size, bold=False):
    for n in names:
        try:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f: return f
        except: pass
    return pygame.font.SysFont("arial", size, bold=bold)

F_XS    = mkf(["Bahnschrift","Calibri","Segoe UI"], 11)
F_TINY  = mkf(["Bahnschrift","Calibri","Segoe UI"], 13)
F_SM    = mkf(["Bahnschrift","Calibri","Segoe UI"], 17)
F_MD    = mkf(["Bahnschrift","Calibri","Segoe UI"], 22, bold=True)
F_LG    = mkf(["Bahnschrift","Calibri","Segoe UI"], 36, bold=True)
F_XL    = mkf(["Bahnschrift","Impact","Arial Black"], 64, bold=True)
F_TITLE = mkf(["Bahnschrift","Impact","Arial Black"], 108, bold=True)
F_GIANT = mkf(["Bahnschrift","Impact","Arial Black"], 130, bold=True)
F_SUB   = mkf(["Bahnschrift","Calibri","Segoe UI"], 19)
F_TAG   = mkf(["Consolas","Lucida Console","Courier New"], 12)

# ═══════════════════════════════════════════════════════════════
#  CORE SETTINGS WRAPPERS (Audio / Display)
# ═══════════════════════════════════════════════════════════════
def get_scaled_mouse_pos(pos=None):
    if pos is None:
        mx, my = pygame.mouse.get_pos()
    else:
        mx, my = pos
    win_w, win_h = window.get_size()
    return int(mx * W / max(1, win_w)), int(my * H / max(1, win_h))

def get_events():
    for e in pygame.event.get():
        if hasattr(e, 'pos'):
            e.pos = get_scaled_mouse_pos(e.pos)
        yield e

def flip_display():
    brightness = SETTINGS.get("brightness", 100)
    if brightness < 100:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        alpha = int(255 * (100 - brightness) / 100.0)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
        
    win_w, win_h = window.get_size()
    if SETTINGS.get("pixel_art_mode", True):
        pygame.transform.scale(screen, (win_w, win_h), window)
    else:
        pygame.transform.smoothscale(screen, (win_w, win_h), window)
        
    if SETTINGS.get("fps_display", False):
        fps_surf = F_SM.render(f"FPS: {int(clock.get_fps())}", True, (0, 255, 0))
        window.blit(fps_surf, (10, 10))

    pygame.display.flip()

if MIXER_OK:
    pygame.mixer.set_num_channels(32)
    CHANNEL_MUSIC = pygame.mixer.Channel(0)
    CHANNEL_SFX = pygame.mixer.Channel(1)
    CHANNEL_ENV = pygame.mixer.Channel(2)
    CHANNEL_EMOTION = pygame.mixer.Channel(3)
    
    def sync_audio_volumes(*args):
        if SETTINGS.get("mute_all", False):
            CHANNEL_MUSIC.set_volume(0)
            CHANNEL_SFX.set_volume(0)
            CHANNEL_ENV.set_volume(0)
            CHANNEL_EMOTION.set_volume(0)
        else:
            master = SETTINGS.get("master_volume", 80) / 100.0
            CHANNEL_MUSIC.set_volume((SETTINGS.get("music_volume", 70) / 100.0) * master)
            CHANNEL_SFX.set_volume((SETTINGS.get("sfx_volume", 80) / 100.0) * master)
            CHANNEL_ENV.set_volume((SETTINGS.get("ambient_volume", 70) / 100.0) * master)
            CHANNEL_EMOTION.set_volume((SETTINGS.get("music_volume", 70) / 100.0) * master)

    sync_audio_volumes()
    SETTINGS.add_listener("master_volume_changed", sync_audio_volumes)
    SETTINGS.add_listener("music_volume_changed", sync_audio_volumes)
    SETTINGS.add_listener("sfx_volume_changed", sync_audio_volumes)
    SETTINGS.add_listener("ambient_volume_changed", sync_audio_volumes)
    SETTINGS.add_listener("mute_all_changed", sync_audio_volumes)

# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def clamp(x,a,b): return max(a,min(b,x))
def lerp(a,b,t):  return a+(b-a)*t
def lerpC(c1,c2,t): return tuple(int(lerp(c1[i],c2[i],t)) for i in range(3))

def hsv(h,s,v):
    r,g,b = colorsys.hsv_to_rgb(h%1.0,s,v)
    return (int(r*255),int(g*255),int(b*255))

# ═══════════════════════════════════════════════════════════════
#  SAVE / STATS
# ═══════════════════════════════════════════════════════════════
def load_save():
    if not os.path.exists(SAVE) and os.path.exists(LEGACY_SAVE):
        try:
            with open(LEGACY_SAVE, encoding="utf-8") as f:
                data = json.load(f)
            with open(SAVE, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return data
        except Exception:
            pass
    if os.path.exists(SAVE):
        try:
            with open(SAVE, encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"level":0,"best":0,"deaths":0,"runs":0,"coins":0,
            "cleared":[False]*TOTAL_LEVELS,"best_times":[0]*TOTAL_LEVELS,
            "completed_levels":[],"stars":0,"emotions":[],
            "level_stars":[0]*TOTAL_LEVELS}

def save_game(d):
    with open(SAVE, "w", encoding="utf-8") as f: json.dump(d,f)

SD = load_save()
if "cleared" not in SD: SD["cleared"] = []
if "best_times" not in SD: SD["best_times"] = []
SD["cleared"] = (SD["cleared"] + [False]*TOTAL_LEVELS)[:TOTAL_LEVELS]
SD["best_times"] = (SD["best_times"] + [0]*TOTAL_LEVELS)[:TOTAL_LEVELS]
if "level_stars" not in SD: SD["level_stars"] = [0]*TOTAL_LEVELS
SD["level_stars"] = (SD["level_stars"] + [0]*TOTAL_LEVELS)[:TOTAL_LEVELS]
SD["level"] = clamp(SD.get("level", 0), 0, TOTAL_LEVELS-1)
EMOTIONS = EmotionSystem(SD)

def draw_text(surf,txt,pos,color=(255,255,255),font=None,center=False,shadow=True,alpha=255):
    f = font or F_SM
    if shadow:
        sr = f.render(txt,True,(0,0,0))
        ox = pos[0]-(sr.get_width()//2 if center else 0)
        surf.blit(sr,(ox+2,pos[1]+2))
    r = f.render(txt,True,color)
    if alpha<255: r.set_alpha(alpha)
    x = pos[0]-r.get_width()//2 if center else pos[0]
    surf.blit(r,(x,pos[1]))

def outlined(text, font, color, oc=(0,0,0), th=3):
    base = font.render(text, True, color)
    w,h  = base.get_size()
    out  = pygame.Surface((w+th*2,h+th*2), pygame.SRCALPHA)
    for ox in range(-th,th+1):
        for oy in range(-th,th+1):
            if ox==0 and oy==0: continue
            if abs(ox)+abs(oy)>th+1: continue
            out.blit(font.render(text,True,oc),(ox+th,oy+th))
    out.blit(base,(th,th))
    return out

def grad_text(text, font, ct, cb):
    base = font.render(text, True, ct)
    w,h  = base.get_size()
    g    = pygame.Surface((w,h), pygame.SRCALPHA)
    for y in range(h):
        c = lerpC(ct,cb,y/max(1,h))
        pygame.draw.line(g,(*c,255),(0,y),(w,y))
    g.blit(base,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    return g

def circ(surf, color, pos, radius, alpha=255):
    x,y,r = int(pos[0]),int(pos[1]),int(radius)
    if r<=0: return
    if alpha<255:
        s = pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*color[:3],alpha),(r,r),r)
        surf.blit(s,(x-r,y-r))
    else:
        try: gfxdraw.aacircle(surf,x,y,r,color); gfxdraw.filled_circle(surf,x,y,r,color)
        except: pygame.draw.circle(surf,color,(x,y),r)

# ═══════════════════════════════════════════════════════════════
#  WORLD THEMES  (100 worlds, first 20 handcrafted then metadata-extended)
#  WORLD THEMES  (20 worlds, each fully unique)
# ═══════════════════════════════════════════════════════════════
#  bg_top, bg_bot, plat_col, accent, enemy_col, fx_col, name,
#  weather, fog_col, platform_style
WT = [
    # 0  VOID
    ((3,1,10),(14,6,40),(60,45,120),(130,80,255),(180,60,210),(110,60,255),
     "VOID","none",(20,10,40),"normal"),
    # 1  VERDANT FOREST
    ((2,10,2),(8,42,10),(38,100,45),(70,210,70),(160,210,50),(60,230,60),
     "VERDANT FOREST","leaves",(4,12,4),"mossy"),
    # 2  HELLFIRE
    ((18,3,1),(75,14,4),(150,45,20),(255,100,20),(255,60,20),(255,130,30),
     "HELLFIRE","embers",(25,5,2),"scorched"),
    # 3  DEEP OCEAN
    ((1,12,22),(4,55,105),(30,88,150),(60,185,255),(30,140,220),(80,200,255),
     "DEEP OCEAN","bubbles",(2,18,32),"coral"),
    # 4  SUNKEN DESERT
    ((20,14,2),(85,65,8),(150,118,35),(255,195,50),(220,150,30),(255,210,60),
     "SUNKEN DESERT","sand",(18,12,2),"sandstone"),
    # 5  GLACIAL ABYSS
    ((2,14,20),(6,52,78),(35,130,155),(90,225,255),(50,185,220),(80,240,255),
     "GLACIAL ABYSS","snow",(2,16,24),"ice"),
    # 6  NEON GRID
    ((8,0,16),(28,0,60),(145,20,175),(220,60,255),(190,40,230),(210,80,255),
     "NEON GRID","sparks",(10,0,20),"neon"),
    # 7  MAGMA CORE
    ((20,5,0),(90,28,0),(175,68,12),(255,130,15),(255,90,15),(255,155,30),
     "MAGMA CORE","embers",(22,6,0),"lava"),
    # 8  DEAD SPACE
    ((0,0,14),(0,0,75),(22,22,155),(70,100,255),(50,80,220),(90,130,255),
     "DEAD SPACE","none",(0,0,18),"metal"),
    # 9  GLITCH MATRIX
    ((8,8,10),(40,42,48),(88,92,100),(175,185,200),(145,155,175),(190,200,220),
     "GLITCH MATRIX","glitch",(10,10,12),"glitch"),
    # 10 DREAMSCAPE
    ((10,2,20),(42,5,95),(88,35,158),(165,75,255),(138,52,220),(178,95,255),
     "DREAMSCAPE","sparkle",(12,2,24),"crystal"),
    # 11 TOXIC WASTES
    ((0,14,2),(0,70,12),(22,148,40),(48,255,88),(32,220,65),(60,255,100),
     "TOXIC WASTES","acid",(0,16,4),"corroded"),
    # 12 BLOOD MOON
    ((18,0,6),(85,0,30),(152,22,58),(255,48,108),(215,30,85),(255,70,120),
     "BLOOD MOON","blood",(20,0,8),"gore"),
    # 13 CRYSTAL CAVERN
    ((3,3,20),(14,14,92),(42,42,182),(90,138,255),(68,108,225),(110,155,255),
     "CRYSTAL CAVERN","crystal",(4,4,24),"crystal"),
    # 14 VOLCANIC CRUST
    ((22,3,0),(98,16,0),(188,72,14),(255,132,28),(255,95,18),(255,158,38),
     "VOLCANIC CRUST","ash",(24,4,0),"volcanic"),
    # 15 CYBER NEXUS
    ((0,14,16),(0,80,90),(22,168,182),(40,245,255),(28,210,228),(55,255,255),
     "CYBER NEXUS","sparks",(0,16,18),"neon"),
    # 16 ANCIENT RUINS
    ((10,8,2),(52,46,8),(132,112,35),(215,192,72),(178,158,52),(228,205,82),
     "ANCIENT RUINS","dust",(12,10,2),"stone"),
    # 17 NIGHTMARE REALM
    ((14,0,5),(72,0,24),(148,24,50),(255,44,96),(215,28,72),(255,68,112),
     "NIGHTMARE REALM","blood",(16,0,6),"gore"),
    # 18 THE ABYSS
    ((0,3,16),(0,16,72),(22,42,162),(50,105,255),(35,85,225),(65,120,255),
     "THE ABYSS","none",(0,4,20),"metal"),
    # 19 TRANSCENDENCE
    ((10,10,16),(38,38,72),(195,195,215),(255,255,255),(225,225,245),(255,255,255),
     "TRANSCENDENCE","divine",(12,12,18),"divine"),
]

def _extend_world_themes():
    weather_map = {
        "rain": "rain", "snow": "snow", "fire_particles": "embers",
        "glowing_particles": "sparkle", "glitch": "glitch", "sand": "sand",
        "bubbles": "bubbles", "petals": "leaves",
    }
    while len(WT) < TOTAL_LEVELS:
        idx = len(WT)
        meta = LEVEL_MANAGER.get_level(idx)
        hue = (idx * 0.071 + len(meta["world"]) * 0.013) % 1.0
        top = hsv(hue, 0.84, 0.16 + (idx % 5) * 0.025)
        bot = hsv((hue + 0.08) % 1.0, 0.78, 0.34 + (idx % 7) * 0.025)
        plat = hsv((hue + 0.15) % 1.0, 0.58, 0.68)
        accent = hsv((hue + 0.28) % 1.0, 0.72, 1.0)
        enemy = hsv((hue + 0.45) % 1.0, 0.75, 0.9)
        fx = hsv((hue + 0.22) % 1.0, 0.58, 1.0)
        weather = "sparkle"
        for effect in meta.get("visual_effects", []):
            if effect in weather_map:
                weather = weather_map[effect]
                break
        fog = hsv(hue, 0.7, 0.12)
        WT.append((top, bot, plat, accent, enemy, fx, meta["world"].upper(),
                   weather, fog, meta.get("platform_style", "normal")))

_extend_world_themes()

def WTHEME(idx):
    return WT[int(idx) % len(WT)]

def level_meta(idx):
    return LEVEL_MANAGER.get_level(max(0, min(int(idx), TOTAL_LEVELS-1)))

MSGS = [
    "Welcome. Hope is the first thing you lose here.",
    "The forest breathes. It waits. It remembers.",
    "Everything burns. Especially your progress.",
    "The ocean floor claims all who fall.",
    "The desert buries the weak in silence.",
    "One crack. That's all the ice needs.",
    "The neon grid has no exit. Only loops.",
    "Magma is patient. You are not.",
    "In dead space, only your screams echo.",
    "Reality has been corrupted. Restart unavailable.",
    "Dreamscapes collapse without warning.",
    "The toxins are evolving. So are the enemies.",
    "The blood moon empowers everything but you.",
    "Crystal formations are beautiful. And razor-sharp.",
    "The volcano erupts on a timer. Learn the timer.",
    "Cyber demons adapt to your movement patterns.",
    "Ancient traps never decay. They remember you.",
    "This nightmare was personally designed for you.",
    "The Abyss has 47 different ways to kill you.",
    "FINAL WORLD. Perfection or eternal failure.",
]

# ═══════════════════════════════════════════════════════════════
#  SOUND  (procedural synthesis)
# ═══════════════════════════════════════════════════════════════
def gen_sound(freq=440,dur=0.1,vol=0.35,wave="sine",sweep=0,env_exp=0.15):
    rate=44100; n=int(rate*dur); buf=bytearray(n*2)
    for i in range(n):
        t=i/rate; env=min(1.0,(n-i)/max(1,n*env_exp)); f=freq*(1+sweep*t)
        if   wave=="sine":   s=math.sin(math.tau*f*t)
        elif wave=="square": s=1.0 if math.sin(math.tau*f*t)>0 else -1.0
        elif wave=="saw":    s=2*(f*t%1)-1
        elif wave=="tri":    s=abs(4*(f*t%1)-2)-1
        elif wave=="noise":  s=random.uniform(-1,1)
        else:                s=math.sin(math.tau*f*t)
        v=clamp(int(s*env*vol*32767),-32768,32767)
        buf[i*2]=v&0xFF; buf[i*2+1]=(v>>8)&0xFF
    snd=pygame.mixer.Sound(buffer=bytes(buf)); snd.set_volume(vol); return snd

def gen_ambient_pad(base_freq, dur=2.0, vol=0.15, harmonics=None):
    """Generate a seamlessly looping ambient drone pad (mono 16-bit PCM)."""
    rate=44100; n=int(rate*dur); buf=bytearray(n*2)
    if harmonics is None:
        harmonics=[(1.0,0.5),(2.0,0.22),(3.0,0.10),(0.5,0.18)]
    fade=int(rate*0.14)
    for i in range(n):
        t=i/rate
        env=(i/fade if i<fade else (n-i)/fade if i>n-fade else 1.0)
        lfo=1.0+0.04*math.sin(t*0.7)
        s=sum(a*math.sin(math.tau*base_freq*m*t) for m,a in harmonics)
        v=clamp(int(s*env*lfo*vol*32767),-32768,32767)
        buf[i*2]=v&0xFF; buf[i*2+1]=(v>>8)&0xFF
    snd=pygame.mixer.Sound(buffer=bytes(buf)); snd.set_volume(vol); return snd

try:
    SND_JUMP = SND_DJUMP = SND_LAND = SND_DIE = None
    SND_WIN = SND_COIN = SND_PORTAL = SND_DASH = None
    SND_BOOST = SND_COMBO = SND_PAUSE = None
    SOUND_OK = False
    if MIXER_OK:
        SND_JUMP    = gen_sound(560, 0.07, 0.26,"sine",  sweep=0.6)
        SND_DJUMP   = gen_sound(720, 0.09, 0.28,"sine",  sweep=0.8)
        SND_LAND    = gen_sound(170, 0.07, 0.18,"sine",  sweep=-0.4)
        SND_DIE     = gen_sound(100, 0.60, 0.42,"square",sweep=-0.9)
        SND_WIN     = gen_sound(820, 0.38, 0.36,"sine",  sweep=0.35)
        SND_COIN    = gen_sound(900, 0.09, 0.23,"sine",  sweep=0.25)
        SND_PORTAL  = gen_sound(460, 0.25, 0.30,"saw",   sweep=0.45)
        SND_DASH    = gen_sound(320, 0.05, 0.18,"saw",   sweep=1.2)
        SND_BOOST   = gen_sound(680, 0.14, 0.28,"sine",  sweep=0.9)
        SND_COMBO   = gen_sound(1100,0.12, 0.32,"tri",   sweep=0.2)
        SND_PAUSE   = gen_sound(280, 0.08, 0.20,"sine",  sweep=-0.2)
        SOUND_OK    = True
except Exception:
    SOUND_OK = False

# Ambient music pads (one per emotion mood)
_MOOD_PADS = {
    "nervous":   (110, [(1.0,0.50),(1.414,0.28),(2.0,0.14),(0.5,0.12)]),
    "intense":   (110, [(1.0,0.55),(1.5,0.30),(2.0,0.18),(3.0,0.08)]),
    "heavy":     (82,  [(1.0,0.60),(2.0,0.25),(3.0,0.10),(0.5,0.22)]),
    "bright":    (440, [(1.0,0.45),(1.25,0.28),(1.5,0.15),(2.0,0.10)]),
    "brave":     (220, [(1.0,0.50),(1.5,0.30),(2.0,0.14),(3.0,0.06)]),
    "peaceful":  (261, [(1.0,0.48),(1.334,0.26),(1.5,0.14),(2.0,0.10)]),
    "calm":      (196, [(1.0,0.50),(2.0,0.22),(3.0,0.10),(4.0,0.06)]),
    "energetic": (330, [(1.0,0.45),(1.25,0.30),(1.5,0.18),(2.0,0.12)]),
    "balanced":  (220, [(1.0,0.48),(2.0,0.20),(3.0,0.10),(0.5,0.15)]),
}
AMBIENT_PADS = {}
if MIXER_OK:
    for _mood, (_freq, _harm) in _MOOD_PADS.items():
        try:
            AMBIENT_PADS[_mood] = gen_ambient_pad(_freq, harmonics=_harm)
        except Exception:
            pass
_last_music_mood = None

def play(snd, channel=None):
    if SOUND_OK and snd is not None:
        try:
            if channel:
                channel.play(snd)
            elif MIXER_OK and 'CHANNEL_SFX' in globals():
                CHANNEL_SFX.play(snd)
            else:
                snd.play()
        except: pass

# ═══════════════════════════════════════════════════════════════
#  PARTICLES  (expanded shapes + world-aware)
# ═══════════════════════════════════════════════════════════════
class Particle:
    __slots__=["x","y","vx","vy","life","ml","r","g","b","size",
               "grav","fade","rot","rspd","shape","bounce"]
    def __init__(self,x,y,vx,vy,life,color,size=3,grav=0.0,fade=True,
                 shape="circle",bounce=False):
        self.x,self.y   = float(x),float(y)
        self.vx,self.vy = float(vx),float(vy)
        self.life=self.ml=int(life)
        self.r,self.g,self.b = clamp(int(color[0]),0,255),clamp(int(color[1]),0,255),clamp(int(color[2]),0,255)
        self.size=size; self.grav=grav; self.fade=fade
        self.rot=random.uniform(0,6.28); self.rspd=random.uniform(-0.18,0.18)
        self.shape=shape; self.bounce=bounce

    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=self.grav; self.vx*=0.97
        self.rot+=self.rspd; self.life-=1
        if self.bounce and self.y>H-30 and self.vy>0:
            self.vy*=-0.55; self.vx*=0.8
        return self.life>0

    def draw(self, surf):
        t   = self.life/self.ml
        alp = int(255*t) if self.fade else 255
        s   = max(1,int(self.size*t))
        c   = (self.r, self.g, self.b)
        ix,iy = int(self.x),int(self.y)
        if self.shape=="spark":
            ex=int(self.x-self.vx*2.5); ey=int(self.y-self.vy*2.5)
            if abs(ex-ix)>1 or abs(ey-iy)>1:
                ss=pygame.Surface((abs(ex-ix)+s*2+2,abs(ey-iy)+s*2+2),pygame.SRCALPHA)
                dx,dy=min(ix,ex),min(iy,ey)
                pygame.draw.line(ss,(*c,alp),(ix-dx+1,iy-dy+1),(ex-dx+1,ey-dy+1),max(1,s//2))
                surf.blit(ss,(dx-1,dy-1))
        elif self.shape=="square":
            sq=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
            pygame.draw.rect(sq,(*c,alp),(0,0,s*2,s*2),border_radius=max(1,s//3))
            surf.blit(sq,(ix-s,iy-s))
        elif self.shape=="diamond":
            if s>=2:
                ds=pygame.Surface((s*3,s*3),pygame.SRCALPHA)
                pts=[(s+1,1),(s*2+1,s+1),(s+1,s*2+1),(1,s+1)]
                pygame.draw.polygon(ds,(*c,alp),pts)
                surf.blit(ds,(ix-s-1,iy-s-1))
        elif self.shape=="ring":
            rs=pygame.Surface((s*3,s*3),pygame.SRCALPHA)
            pygame.draw.circle(rs,(*c,alp),(s+1,s+1),s+1,max(1,s//3+1))
            surf.blit(rs,(ix-s-1,iy-s-1))
        elif self.shape=="leaf":
            if s>=2:
                ls=pygame.Surface((s*2,s*3),pygame.SRCALPHA)
                pts=[(s,0),(s*2-1,s),(s,s*3-1),(1,s)]
                pygame.draw.polygon(ls,(*c,alp),pts)
                surf.blit(ls,(ix-s,iy-s))
        else:  # circle
            try: gfxdraw.filled_circle(surf,ix,iy,s,(*c,alp))
            except: pygame.draw.circle(surf,c,(ix,iy),s)

class PS:
    def __init__(self, mx=5000): self.pool=[]; self.mx=mx

    def emit(self,x,y,vx=0,vy=0,spread=3,count=5,life=40,
             color=(255,200,100),size=4,grav=0.05,fade=True,shape="circle",bounce=False):
        for _ in range(count):
            a=random.uniform(0,math.tau); sp=random.uniform(0,spread)
            self.pool.append(Particle(
                x+random.uniform(-2,2), y+random.uniform(-2,2),
                vx+math.cos(a)*sp, vy+math.sin(a)*sp,
                life+random.randint(-life//5,life//5),
                color,size,grav,fade,shape,bounce))
        if len(self.pool)>self.mx: self.pool=self.pool[-self.mx:]

    def burst(self,x,y,count=24,color=(255,200,50),size=5,world=0):
        wt=WTHEME(world)
        self.emit(x,y,spread=8,count=count,life=55,color=color,size=size,grav=0.14,shape="circle")
        self.emit(x,y,spread=6,count=count//2,life=42,color=wt[5],size=size//2,grav=0.07,shape="spark")
        self.emit(x,y,spread=4,count=count//3,life=36,color=(255,255,255),size=2,grav=0.04,shape="ring")
        self.emit(x,y,spread=5,count=count//4,life=48,color=color,size=size-1,grav=0.1,shape="diamond",bounce=True)

    def draw(self, surf):
        self.pool=[p for p in self.pool if p.update()]
        for p in self.pool: p.draw(surf)

ps = PS()

# ═══════════════════════════════════════════════════════════════
#  WEATHER SYSTEM
# ═══════════════════════════════════════════════════════════════
class Weather:
    EFFECTS = {
        "leaves": {
            "freq": 5, "y": -10.0, "vy_range": (1.2, 2.8), "vx_range": (-1, 1),
            "life_range": (160, 280), "size_range": (4, 8), "rot_range": (-0.05, 0.05),
            "colors": [(80, 160, 40), (60, 140, 30), (100, 180, 50), (120, 200, 60)]
        },
        "embers": {
            "freq": 3, "y_range": ("H-150", "H"), "vy_range": (-2.5, -0.8), "vx_range": (-0.8, 0.8),
            "life_range": (60, 120), "size_range": (2, 4),
            "colors": [(255, 120, 20), (255, 80, 10), (255, 160, 30), (255, 200, 50)]
        },
        "snow": {
            "freq": 4, "y": -8.0, "vy_range": (0.8, 1.8), "vx_range": (-0.6, 0.6),
            "life_range": (200, 320), "size_range": (2, 5), "rot_range": (0.02, 0.02),
            "colors": [(210, 230, 255)]
        },
        "bubbles": {
            "freq": 6, "y": "H+10", "vy_range": (-1.4, -0.7), "vx_range": (-0.4, 0.4),
            "life_range": (120, 200), "size_range": (3, 8),
            "colors": [(60, 180, 255), (80, 200, 255), (100, 220, 255)]
        },
        "sand": {
            "freq": 2, "x_range": (0, "W"), "y_range": (100, "H-50"), "vy_range": (-0.3, 0.3),
            "vx_factory": lambda x: random.uniform(2.5, 4.5) * (-1 if x > 0 else 1),
            "life_range": (40, 90), "size_range": (1, 3),
            "colors": [(200, 170, 80), (220, 190, 100), (180, 150, 60)]
        },
        "sparks": {
            "freq": 4, "y_range": ("H//2", "H"), "vy_range": (-3, -0.5), "vx_range": (-3, 3),
            "life_range": (20, 45), "size_range": (1, 3), "color_from_world": 5
        },
        "acid": {
            "freq": 5, "y": -8.0, "vy_range": (1.8, 3.2), "vx_range": (-0.5, 0.5),
            "life_range": (80, 140), "size_range": (2, 4), "colors": [(60, 220, 80)]
        },
        "blood": {
            "freq": 7, "y": -8.0, "vy_range": (2.0, 3.5), "vx_range": (-0.5, 0.5),
            "life_range": (80, 150), "size_range": (2, 4), "colors": [(180, 10, 30)]
        },
        "crystal": {
            "freq": 8, "y_range": (0, "H"), "vy_range": (-1, 1), "vx_range": (-1, 1),
            "life_range": (30, 60), "size_range": (3, 7), "rot_range": (0.1, 0.1),
            "color_from_world": 5
        },
        "ash": {
            "freq": 3, "y": -8.0, "vy_range": (0.5, 1.5), "vx_range": (-1.2, 1.2),
            "life_range": (140, 240), "size_range": (2, 5), "rot_range": (0.01, 0.01),
            "colors": [(160, 140, 130)]
        },
        "dust": {
            "freq": 4, "y_range": ("H//2", "H"), "vy_range": (-1, 0.5), "vx_range": (-2, 2),
            "life_range": (60, 120), "size_range": (1, 3), "colors": [(210, 190, 140)]
        },
        "glitch": {
            "freq": 6, "y_range": (0, "H"), "vy_range": (-2, 2), "vx_range": (-5, 5),
            "life_range": (8, 18), "size_range": (1, 3), "color_from_world": 5
        },
        "sparkle": {
            "freq": 3, "y_range": (0, "H"), "vy_range": (-1.2, -0.2), "vx_range": (-0.5, 0.5),
            "life_range": (25, 55), "size_range": (2, 5), "rot_range": (0.15, 0.15),
            "color_factory": lambda: hsv(random.random(), 0.7, 1.0)
        },
        "divine": {
            "freq": 4, "y_range": (0, "H"), "vy_range": (-0.5, 0.5), "vx_range": (0, 0),
            "life_range": (40, 80), "size_range": (3, 8), "rot_range": (0.08, 0.08),
            "colors": [(255, 255, 255)]
        }
    }

    def __init__(self):
        self.drops=[]
        self.t=0

    def update_emit(self, world_idx):
        wtype=WTHEME(world_idx)[7]
        self.t+=1
        if wtype=="none": return
        if wtype=="leaves" and self.t%5==0:
            x=random.randint(0,W); vy=random.uniform(1.2,2.8)
            c=random.choice([(80,160,40),(60,140,30),(100,180,50),(120,200,60)])
            self.drops.append({"x":float(x),"y":-10.,"vx":random.uniform(-1,1),"vy":vy,
                               "life":random.randint(160,280),"ml":280,"type":wtype,
                               "c":c,"rot":random.uniform(0,6.28),"rspd":random.uniform(-0.05,0.05),"s":random.randint(4,8)})
        elif wtype=="embers" and self.t%3==0:
            x=random.randint(0,W); y=random.randint(H-150,H)
            c=random.choice([(255,120,20),(255,80,10),(255,160,30),(255,200,50)])
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-0.8,0.8),
                               "vy":random.uniform(-2.5,-0.8),"life":random.randint(60,120),"ml":120,
                               "type":wtype,"c":c,"s":random.randint(2,4),"rot":0,"rspd":0})
        elif wtype=="snow" and self.t%4==0:
            x=random.randint(0,W)
            c=(210,230,255)
            self.drops.append({"x":float(x),"y":-8.,"vx":random.uniform(-0.6,0.6),
                               "vy":random.uniform(0.8,1.8),"life":random.randint(200,320),"ml":320,
                               "type":wtype,"c":c,"s":random.randint(2,5),"rot":0,"rspd":0.02})
        elif wtype=="bubbles" and self.t%6==0:
            x=random.randint(0,W); y=H+10
            c=random.choice([(60,180,255),(80,200,255),(100,220,255)])
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-0.4,0.4),
                               "vy":random.uniform(-1.4,-0.7),"life":random.randint(120,200),"ml":200,
                               "type":wtype,"c":c,"s":random.randint(3,8),"rot":0,"rspd":0})
        elif wtype=="sand" and self.t%2==0:
            x=0 if random.random()<0.5 else W
            y=random.randint(100,H-50)
            vx=random.uniform(2.5,4.5) * (1 if x==0 else -1)
            c=random.choice([(200,170,80),(220,190,100),(180,150,60)])
            self.drops.append({"x":float(x),"y":float(y),"vx":vx,"vy":random.uniform(-0.3,0.3),
                               "life":random.randint(40,90),"ml":90,"type":wtype,"c":c,"s":random.randint(1,3),"rot":0,"rspd":0})
        elif wtype=="sparks" and self.t%4==0:
            x=random.randint(0,W); y=random.randint(H//2,H)
            c=WTHEME(world_idx)[5]
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-3,3),
                               "vy":random.uniform(-3,-0.5),"life":random.randint(20,45),"ml":45,
                               "type":wtype,"c":c,"s":random.randint(1,3),"rot":0,"rspd":0})
        elif wtype=="acid" and self.t%5==0:
            x=random.randint(0,W)
            c=(60,220,80)
            self.drops.append({"x":float(x),"y":-8.,"vx":random.uniform(-0.5,0.5),
                               "vy":random.uniform(1.8,3.2),"life":random.randint(80,140),"ml":140,
                               "type":wtype,"c":c,"s":random.randint(2,4),"rot":0,"rspd":0})
        elif wtype=="blood" and self.t%7==0:
            x=random.randint(0,W)
            c=(180,10,30)
            self.drops.append({"x":float(x),"y":-8.,"vx":random.uniform(-0.5,0.5),
                               "vy":random.uniform(2.0,3.5),"life":random.randint(80,150),"ml":150,
                               "type":wtype,"c":c,"s":random.randint(2,4),"rot":0,"rspd":0})
        elif wtype=="crystal" and self.t%8==0:
            x=random.randint(0,W); y=random.randint(0,H)
            c=WTHEME(world_idx)[5]
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-1,1),
                               "vy":random.uniform(-1,1),"life":random.randint(30,60),"ml":60,
                               "type":wtype,"c":c,"s":random.randint(3,7),"rot":random.uniform(0,6.28),"rspd":0.1})
        elif wtype=="ash" and self.t%3==0:
            x=random.randint(0,W)
            c=(160,140,130)
            self.drops.append({"x":float(x),"y":-8.,"vx":random.uniform(-1.2,1.2),
                               "vy":random.uniform(0.5,1.5),"life":random.randint(140,240),"ml":240,
                               "type":wtype,"c":c,"s":random.randint(2,5),"rot":0,"rspd":0.01})
        elif wtype=="dust" and self.t%4==0:
            x=random.randint(0,W); y=random.randint(H//2,H)
            c=(210,190,140)
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-2,2),
                               "vy":random.uniform(-1,0.5),"life":random.randint(60,120),"ml":120,
                               "type":wtype,"c":c,"s":random.randint(1,3),"rot":0,"rspd":0})
        elif wtype=="glitch" and self.t%6==0:
            x=random.randint(0,W); y=random.randint(0,H)
            c=WTHEME(world_idx)[5]
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-5,5),
                               "vy":random.uniform(-2,2),"life":random.randint(8,18),"ml":18,
                               "type":wtype,"c":c,"s":random.randint(1,3),"rot":0,"rspd":0})
        elif wtype=="sparkle" and self.t%3==0:
            x=random.randint(0,W); y=random.randint(0,H)
            c=hsv(random.random(),0.7,1.0)
            self.drops.append({"x":float(x),"y":float(y),"vx":random.uniform(-0.5,0.5),
                               "vy":random.uniform(-1.2,-0.2),"life":random.randint(25,55),"ml":55,
                               "type":wtype,"c":c,"s":random.randint(2,5),"rot":random.uniform(0,6.28),"rspd":0.15})
        elif wtype=="divine" and self.t%4==0:
            x=random.randint(0,W); y=random.randint(0,H)
            c=(255,255,255)
            self.drops.append({"x":float(x),"y":float(y),"vx":0,"vy":random.uniform(-0.5,0.5),
                               "life":random.randint(40,80),"ml":80,
                               "type":wtype,"c":c,"s":random.randint(3,8),"rot":random.uniform(0,6.28),"rspd":0.08})
        wtype = WT[world_idx % 20][7]
        if wtype == "none" or wtype not in self.EFFECTS:
            return

        effect = self.EFFECTS[wtype]
        if self.t % effect["freq"] != 0:
            return

        def _eval_pos(val):
            if isinstance(val, str): return eval(val)
            return val

        x = random.randint(0, W)
        if "x_range" in effect:
            x = random.choice([_eval_pos(p) for p in effect["x_range"]])

        y = effect.get("y", -10.0)
        if "y_range" in effect:
            y_min, y_max = [_eval_pos(p) for p in effect["y_range"]]
            y = random.randint(y_min, y_max)

        vx = random.uniform(*effect.get("vx_range", (-1, 1)))
        if "vx_factory" in effect:
            vx = effect["vx_factory"](x)

        vy = random.uniform(*effect.get("vy_range", (1, 2)))
        life = random.randint(*effect["life_range"])
        size = random.randint(*effect.get("size_range", (2, 4)))
        rspd = random.uniform(*effect.get("rot_range", (0, 0)))

        if "color_factory" in effect:
            color = effect["color_factory"]()
        elif "color_from_world" in effect:
            color = WT[world_idx % 20][effect["color_from_world"]]
        else:
            color = random.choice(effect["colors"])

        self.drops.append({
            "x": float(x), "y": float(y), "vx": vx, "vy": vy,
            "life": life, "ml": effect["life_range"][1], "type": wtype,
            "c": color, "rot": random.uniform(0, 6.28), "rspd": rspd, "s": size
        })

        # Trim
        if len(self.drops)>400: self.drops=self.drops[-400:]

    def draw(self, surf):
        alive=[]
        for d in self.drops:
            d["x"]+=d["vx"]; d["y"]+=d["vy"]; d["life"]-=1
            d["rot"]+=d["rspd"]
            if d["life"]<=0: continue
            
            t=d["life"]/d["ml"]; a=int(200*t); s=d["s"]; c=d["c"]
            tp=d["type"]
            if tp=="leaves":
                pts=[]
                for k in range(4):
                    ang=d["rot"]+k*math.tau/4
                    pts.append((d["x"]+math.cos(ang)*s,d["y"]+math.sin(ang)*s*0.5))
                if len(pts)>=3:
                    ls=pygame.Surface((s*4,s*4),pygame.SRCALPHA)
                    adj=[(p[0]-d["x"]+s*2,p[1]-d["y"]+s*2) for p in pts]
                    pygame.draw.polygon(ls,(*c,a),adj)
                    surf.blit(ls,(int(d["x"])-s*2,int(d["y"])-s*2))
            elif tp in ("embers","sparks","glitch"):
                try: gfxdraw.filled_circle(surf,int(d["x"]),int(d["y"]),max(1,s),(*c,a))
                except: pygame.draw.circle(surf,c,(int(d["x"]),int(d["y"])),max(1,s))
            elif tp in ("snow","ash","dust"):
                try: gfxdraw.filled_circle(surf,int(d["x"]),int(d["y"]),max(1,s),(*c,a))
                except: pygame.draw.circle(surf,c,(int(d["x"]),int(d["y"])),max(1,s))
            elif tp in ("bubbles",):
                bs=pygame.Surface((s*2+4,s*2+4),pygame.SRCALPHA)
                pygame.draw.circle(bs,(*c,a//2),(s+2,s+2),s+2,1)
                surf.blit(bs,(int(d["x"])-s-2,int(d["y"])-s-2))
            elif tp in ("sand","blood","acid"):
                ew=max(2,s*3); eh=max(1,s)
                ds=pygame.Surface((ew,eh),pygame.SRCALPHA)
                ds.fill((*c,a))
                surf.blit(ds,(int(d["x"])-ew//2,int(d["y"])-eh//2))
            elif tp in ("crystal","sparkle","divine"):
                cs=pygame.Surface((s*4,s*4),pygame.SRCALPHA)
                for k in range(4):
                    ang=d["rot"]+k*math.tau/4
                    ex2=s*2+int(math.cos(ang)*s*1.5); ey2=s*2+int(math.sin(ang)*s*1.5)
                    pygame.draw.line(cs,(*c,a),(s*2,s*2),(ex2,ey2),max(1,s//3))
                surf.blit(cs,(int(d["x"])-s*2,int(d["y"])-s*2))
            
            alive.append(d)
        self.drops=alive

weather = Weather()

# ═══════════════════════════════════════════════════════════════
#  3D SPHERE RENDERER  (Phong shading: diffuse, specular, rim, AO)
# ═══════════════════════════════════════════════════════════════
# Pre-cache sphere surfaces for perf
_sphere_cache = {}

def draw_sphere(surf, cx, cy, radius, base_color, tick=0,
                emissive=False, emissive_color=None, shadow=True,
                pulse_t=0.0, squish_x=1.0, squish_y=1.0):
    r = max(3, int(radius))
    bx,by = int(cx), int(cy)
    rw = max(3, int(r*squish_x))
    rh = max(3, int(r*squish_y))

    # Ground shadow
    if shadow:
        sw=int(rw*1.7); sh2=max(2,int(rh*0.3))
        shad=pygame.Surface((sw*2,sh2*2),pygame.SRCALPHA)
        pygame.draw.ellipse(shad,(0,0,0,50),(0,0,sw*2,sh2*2))
        surf.blit(shad,(bx-sw,by+rh-2))

    # Outer glow
    gr=int(rw*1.8+pulse_t*rw*0.35)
    if emissive and emissive_color:
        gc=(*emissive_color,int(28+pulse_t*22))
    else:
        gc=(*lerpC(base_color,(255,255,255),0.2),16)
    gs=pygame.Surface((gr*2,int(gr*1.3)),pygame.SRCALPHA)
    pygame.draw.ellipse(gs,gc,(0,0,gr*2,int(gr*1.3)))
    surf.blit(gs,(bx-gr,by-int(gr*0.65)))

    # Build sphere on a small surface (scaled for squish)
    diam_w=rw*2+2; diam_h=rh*2+2
    sphere=pygame.Surface((diam_w,diam_h),pygame.SRCALPHA)
    dark=lerpC(base_color,(0,0,0),0.48)
    mid=base_color
    bright=lerpC(base_color,(255,255,255),0.28)

    # Diffuse shading: draw concentric ellipses from edge to center
    for i in range(max(rw,rh),0,-1):
        t=1.0-(i/max(rw,rh))
        # Light from upper-left: shift center
        lox=int(-rw*0.22); loy=int(-rh*0.25)
        c=lerpC(dark,bright,t**0.55)
        ew=max(1,int(i*squish_x*2*(rw/max(rw,rh))))
        eh=max(1,int(i*squish_y*2*(rh/max(rw,rh))))
        try:
            pygame.draw.ellipse(sphere,c,
                (rw+lox-ew//2, rh+loy-eh//2, ew, eh))
        except: pass

    # Specular highlight
    sr2=max(2,int(rw*0.28))
    sx=int(rw*0.65); sy=int(rh*0.38)  # upper-left quadrant
    for i in range(sr2,0,-1):
        tt=1-(i/sr2)
        a=int(210*tt**1.8)
        ss2=pygame.Surface((i*2,i*2),pygame.SRCALPHA)
        pygame.draw.circle(ss2,(255,255,255,a),(i,i),i)
        sphere.blit(ss2,(sx-i,sy-i))
    # Micro specular
    ms=max(1,int(rw*0.1))
    try: gfxdraw.filled_circle(sphere,int(rw*0.58),int(rh*0.3),ms,(255,255,255,235))
    except: pass

    # Rim light (lower-right, blue tint)
    rim_c=lerpC(base_color,(40,60,140),0.72)
    for i in range(max(rw,rh),max(rw,rh)-4,-1):
        if i<=0: break
        rim_s=pygame.Surface((rw*2+2,rh*2+2),pygame.SRCALPHA)
        a2=int(55*(max(rw,rh)-i+1)/4)
        pygame.draw.ellipse(rim_s,(*rim_c,a2),(rw-i+1,rh-i+1,i*2,i*2),2)
        sphere.blit(rim_s,(0,0))

    # Emissive inner pulse
    if emissive and emissive_color:
        pr=max(1,int(rw*0.52))
        ph=max(1,int(rh*0.52))
        ec=(*emissive_color,int(72+pulse_t*55))
        es=pygame.Surface((pr*2,ph*2),pygame.SRCALPHA)
        pygame.draw.ellipse(es,ec,(0,0,pr*2,ph*2))
        sphere.blit(es,(rw-pr,rh-ph),special_flags=pygame.BLEND_RGBA_ADD)

    # AO ring at bottom
    ao_h=max(1,int(rh*0.4))
    ao=pygame.Surface((rw*2,ao_h*2),pygame.SRCALPHA)
    pygame.draw.ellipse(ao,(0,0,0,45),(0,0,rw*2,ao_h*2))
    sphere.blit(ao,(0,rh+int(rh*0.62)),special_flags=pygame.BLEND_RGBA_MULT)

    surf.blit(sphere,(bx-rw-1,by-rh-1))

# ═══════════════════════════════════════════════════════════════
#  CAMERA (shake + chromatic aberration)
# ═══════════════════════════════════════════════════════════════
class Camera:
    def __init__(self):
        self.shake=0.0; self.ox=self.oy=0.0; self.chromatic=0.0

    def hit(self,s=14,ch=0):
        self.shake=max(self.shake,s); self.chromatic=max(self.chromatic,ch)

    def update(self):
        if self.shake>0.1:
            self.ox=random.gauss(0,self.shake*0.5)
            self.oy=random.gauss(0,self.shake*0.5)
            self.shake*=0.73
        else: self.shake=self.ox=self.oy=0
        if self.chromatic>0.1: self.chromatic*=0.76
        else: self.chromatic=0

    def apply(self, surf):
        if self.shake>0.5:
            dst=pygame.Surface((W,H)); dst.fill((0,0,0))
            dst.blit(surf,(int(self.ox),int(self.oy)))
            surf.blit(dst,(0,0))
        if self.chromatic>1:
            ch=int(self.chromatic)
            for col,offset in [((255,0,0,25),(-ch,0)),((0,0,255,25),(ch,0))]:
                cs=pygame.Surface((W,H),pygame.SRCALPHA)
                cs.blit(surf,(0,0))
                cs.fill(col,special_flags=pygame.BLEND_RGBA_MULT)
                surf.blit(cs,offset,special_flags=pygame.BLEND_RGBA_ADD)

cam = Camera()

# ═══════════════════════════════════════════════════════════════
#  COIN  (3D spinning disc with magnet effect)
# ═══════════════════════════════════════════════════════════════
class Coin:
    MAGNET_DIST = 90
    MAGNET_SPD  = 7.0

    def __init__(self,x,y):
        self.x,self.y   = float(x),float(y)
        self.t          = random.uniform(0,6.28)
        self.collected  = False
        self.r          = 9
        self.spin       = random.uniform(0,6.28)
        self.bob_off    = random.uniform(0,6.28)
        self.magnetized = False

    def update(self, px, py, magnet=False):
        self.t    += 0.055
        self.spin += 0.10
        if self.collected: return
        if magnet:
            dx=px-self.x; dy=py-self.y
            d=math.hypot(dx,dy)
            if d<self.MAGNET_DIST:
                self.magnetized=True
                spd=self.MAGNET_SPD*(1-(d/self.MAGNET_DIST)*0.6)
                if d>1:
                    self.x+=dx/d*spd; self.y+=dy/d*spd
            else:
                self.magnetized=False
        else:
            self.magnetized=False

    def draw(self, surf):
        if self.collected: return
        bob=math.sin(self.t+self.bob_off)*5
        squish=max(0.08, abs(math.cos(self.spin)))
        c=hsv(self.t*0.035%1,0.95,1.0)
        w=max(2,int(self.r*2*squish))
        h=self.r*2
        cx=int(self.x); cy=int(self.y+bob)

        # Magnet glow
        if self.magnetized:
            mg_r=int(self.r*2.5)
            ms=pygame.Surface((mg_r*2,mg_r*2),pygame.SRCALPHA)
            pygame.draw.circle(ms,(*c,30),(mg_r,mg_r),mg_r)
            surf.blit(ms,(cx-mg_r,cy-mg_r))

        # Ground shadow
        sh=pygame.Surface((self.r*2,6),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,30),(0,0,self.r*2,6))
        surf.blit(sh,(cx-self.r,cy+self.r+2))

        # Coin body
        coin_s=pygame.Surface((w+6,h+6),pygame.SRCALPHA)
        dark_c=lerpC(c,(0,0,0),0.35)
        pygame.draw.ellipse(coin_s,(*dark_c,255),(0,0,w+6,h+6))
        pygame.draw.ellipse(coin_s,(*c,255),(2,2,w+2,h+2))
        # Highlight ellipse
        hw=max(1,(w+2)//3); hh=max(1,(h+2)//3)
        pygame.draw.ellipse(coin_s,(255,255,210,190),(3,3,hw,hh))
        # Edge rim
        pygame.draw.ellipse(coin_s,(*lerpC(c,(255,255,255),0.5),120),(2,2,w+2,h+2),1)
        surf.blit(coin_s,(cx-w//2-3,cy-h//2-3))

        # Outer glow
        gls=pygame.Surface((self.r*4,self.r*4),pygame.SRCALPHA)
        pygame.draw.circle(gls,(*c,28),(self.r*2,self.r*2),self.r*2)
        surf.blit(gls,(cx-self.r*2,cy-self.r*2))

    def check(self, prect):
        if self.collected: return False
        if pygame.Rect(self.x-self.r,self.y-self.r,self.r*2,self.r*2).colliderect(prect):
            self.collected=True; return True
        return False

# ═══════════════════════════════════════════════════════════════
#  PLATFORM  (world-themed visual styles)
# ═══════════════════════════════════════════════════════════════
class Platform:
    def __init__(self,x,y,w,h,color=(60,80,120),deadly=False,
                 moving=False,mx=0,my=0,mrange=100,mspeed=1.5,
                 phase=False,phase_time=90,crumble=False,boost=False,
                 world_idx=0):
        self.rect=pygame.Rect(x,y,w,h)
        self.ox,self.oy=x,y
        self.color=color; self.deadly=deadly
        self.moving=moving; self.mx=mx; self.my=my
        self.mrange=mrange; self.mspeed=mspeed
        self.phase=phase; self.phase_time=phase_time
        self.phase_timer=random.randint(0,phase_time)
        self.visible=True; self.t=0.0
        self.crumble=crumble; self.crumble_timer=0; self.crumbling=False
        self.boost=boost
        self.prev_rect=pygame.Rect(x,y,w,h)
        self.world_idx=world_idx
        self.style=WTHEME(world_idx)[9]
        self.style=WT[world_idx%20][9]
        self.crack_pts=[(random.randint(8,max(9,w-8)),random.randint(2,max(3,h-2))) for _ in range(5)]
        # Moving path trail points
        self.path_pts=[]
        self.path_t=0

    def update(self):
        self.prev_rect=self.rect.copy(); self.t+=0.02
        if self.moving:
            s=math.sin(self.t*self.mspeed)
            self.rect.x=int(self.ox+self.mx*s*self.mrange)
            self.rect.y=int(self.oy+self.my*s*self.mrange)
            # Record trail for moving platform path indicator
            self.path_t=(self.path_t+1)%4
            if self.path_t==0:
                self.path_pts.append((self.rect.centerx,self.rect.centery))
                if len(self.path_pts)>20: self.path_pts.pop(0)
        if self.phase:
            self.phase_timer=(self.phase_timer+1)%(self.phase_time*2)
            self.visible=self.phase_timer<self.phase_time
        if self.crumbling:
            self.crumble_timer+=1
            if self.crumble_timer>40: self.visible=False

    def draw(self, surf, tick):
        wt=WTHEME(self.world_idx)
        accent=wt[3]

        if not self.visible:
            if self.phase and (self.phase_time*2-self.phase_timer)<24:
                t=(self.phase_time*2-self.phase_timer)/24
                a=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
                a.fill((*self.color,int(55*t))); surf.blit(a,self.rect.topleft)
            return

        pulse=(math.sin(tick*0.1)+1)/2
        c=self.color
        if self.deadly:
            c=lerpC((215,15,15),(255,85,30),pulse)
        elif self.boost:
            c=lerpC((15,195,15),(90,255,90),pulse)
        elif self.moving:
            c=lerpC(self.color,accent,0.38)
        elif self.crumbling:
            c=lerpC(self.color,(175,75,10),self.crumble_timer/40)

        # Drop shadow
        sh=pygame.Surface((self.rect.w+6,12),pygame.SRCALPHA)
        sh.fill((0,0,0,30)); surf.blit(sh,(self.rect.x-3,self.rect.bottom+1))

        # World-specific platform styles
        if self.style=="ice":
            # Ice: bright sheen, blue tint top edge
            for row in range(self.rect.h):
                t=row/max(1,self.rect.h)
                rc=lerpC(lerpC(c,(200,240,255),0.3),lerpC(c,(0,0,0),0.35),t)
                pygame.draw.rect(surf,rc,(self.rect.x,self.rect.y+row,self.rect.w,1))
            pygame.draw.rect(surf,(220,250,255),(self.rect.x+1,self.rect.y,self.rect.w-2,3))
        elif self.style=="lava":
            # Lava: dark body with orange glow edges
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.4),self.rect,border_radius=3)
            glow_c=(*lerpC((255,100,0),(255,180,0),pulse),80)
            gs=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
            pygame.draw.rect(gs,glow_c,(0,0,self.rect.w,self.rect.h),3,border_radius=3)
            surf.blit(gs,self.rect.topleft)
            # Drip drops
            if not self.deadly and self.t%0.4<0.02:
                for i in range(0,self.rect.w,16):
                    if math.sin(self.t*3+i)>0.8:
                        drip_y=self.rect.bottom+int(math.sin(self.t*2+i)*4)+2
                        pygame.draw.circle(surf,(255,80,10),(self.rect.x+i,drip_y),2)
        elif self.style=="neon":
            # Neon: dark body with bright neon edge glow
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.55),self.rect,border_radius=4)
            ne=(*lerpC(c,accent,0.6+pulse*0.3),int(140+pulse*80))
            ns=pygame.Surface((self.rect.w+4,self.rect.h+4),pygame.SRCALPHA)
            pygame.draw.rect(ns,ne,(0,0,self.rect.w+4,self.rect.h+4),2,border_radius=6)
            surf.blit(ns,(self.rect.x-2,self.rect.y-2))
        elif self.style=="crystal":
            # Crystal: faceted look
            pygame.draw.rect(surf,lerpC(c,(255,255,255),0.15),self.rect,border_radius=2)
            mid=self.rect.centerx; top=self.rect.y; bot=self.rect.bottom
            pygame.draw.line(surf,(*lerpC(c,(255,255,255),0.55),150),(mid,top),(mid,bot),1)
            pygame.draw.rect(surf,(*lerpC(c,(255,255,255),0.5),120),(self.rect.x,self.rect.y,self.rect.w,3))
        elif self.style=="stone":
            # Ancient stone: rough, textured edges
            pygame.draw.rect(surf,c,self.rect,border_radius=2)
            pygame.draw.rect(surf,lerpC(c,(255,255,255),0.25),(self.rect.x+1,self.rect.y,self.rect.w-2,4))
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.4),(self.rect.x,self.rect.y+4,3,self.rect.h-4))
            # Stone texture lines
            for i in range(0,self.rect.w,14):
                pygame.draw.line(surf,lerpC(c,(0,0,0),0.2),
                    (self.rect.x+i,self.rect.y+3),(self.rect.x+i+4,self.rect.y+3),1)
        elif self.style=="glitch":
            # Glitch: offset RGB channels look
            for offset,col in [(-2,(255,0,0,60)),(0,(0,255,255,120)),(2,(255,0,255,60))]:
                gs=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
                gs.fill(col); surf.blit(gs,(self.rect.x+offset,self.rect.y))
            pygame.draw.rect(surf,c,self.rect,1)
        elif self.style=="coral":
            # Ocean coral: rounded with texture
            pygame.draw.rect(surf,c,self.rect,border_radius=6)
            for i in range(2,self.rect.w-2,12):
                h2=random.choice([4,6,8])
                pygame.draw.circle(surf,lerpC(c,(255,255,255),0.3),
                    (self.rect.x+i,self.rect.y-h2//2),h2//3)
        elif self.style=="mossy":
            # Forest mossy: green top layer
            pygame.draw.rect(surf,c,self.rect,border_radius=4)
            pygame.draw.rect(surf,lerpC(c,(60,200,60),0.45),(self.rect.x,self.rect.y,self.rect.w,5),border_radius=4)
        elif self.style=="metal":
            # Space metal: dark with bright stripe
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.3),self.rect,border_radius=2)
            pygame.draw.rect(surf,lerpC(c,(255,255,255),0.35),(self.rect.x+2,self.rect.y+1,self.rect.w-4,2))
        elif self.style=="divine":
            # Transcendence: white glowing
            pygame.draw.rect(surf,c,self.rect,border_radius=5)
            glow_surf=pygame.Surface((self.rect.w+8,self.rect.h+8),pygame.SRCALPHA)
            pygame.draw.rect(glow_surf,(255,255,255,int(40+pulse*40)),(0,0,self.rect.w+8,self.rect.h+8),3,border_radius=8)
            surf.blit(glow_surf,(self.rect.x-4,self.rect.y-4))
        elif self.style=="scorched":
            # Fire scorched
            pygame.draw.rect(surf,c,self.rect,border_radius=3)
            pygame.draw.rect(surf,lerpC(c,(255,120,0),0.3),(self.rect.x,self.rect.y,self.rect.w,4),border_radius=3)
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.5),(self.rect.x,self.rect.y+4,3,self.rect.h-4))
        elif self.style=="sandstone":
            # Desert sandstone: layered look
            for row in range(self.rect.h):
                t=row/max(1,self.rect.h)
                rc=lerpC(lerpC(c,(255,255,200),0.2),lerpC(c,(80,60,0),0.4),t)
                pygame.draw.rect(surf,rc,(self.rect.x,self.rect.y+row,self.rect.w,1))
            for i in range(0,self.rect.h,5):
                pygame.draw.line(surf,(*lerpC(c,(0,0,0),0.15),80),(self.rect.x+2,self.rect.y+i),(self.rect.right-2,self.rect.y+i),1)
        elif self.style=="volcanic":
            # Volcanic: hot glowing edges
            pygame.draw.rect(surf,c,self.rect,border_radius=3)
            ve=(*lerpC((255,60,0),(255,150,0),pulse),int(80+pulse*60))
            vs=pygame.Surface((self.rect.w+4,self.rect.h+4),pygame.SRCALPHA)
            pygame.draw.rect(vs,ve,(0,0,self.rect.w+4,self.rect.h+4),2,border_radius=5)
            surf.blit(vs,(self.rect.x-2,self.rect.y-2))
        elif self.style=="corroded":
            # Toxic corroded
            pygame.draw.rect(surf,c,self.rect,border_radius=3)
            pygame.draw.rect(surf,lerpC(c,(60,255,80),0.4),(self.rect.x,self.rect.y,self.rect.w,4),border_radius=3)
        elif self.style=="gore":
            # Blood moon
            pygame.draw.rect(surf,c,self.rect,border_radius=3)
            pygame.draw.rect(surf,lerpC(c,(255,40,40),0.5),(self.rect.x,self.rect.y,self.rect.w,4),border_radius=3)
        else:  # normal
            for row in range(self.rect.h):
                t=row/max(1,self.rect.h)
                rc=lerpC(lerpC(c,(255,255,255),0.18),lerpC(c,(0,0,0),0.32),t)
                pygame.draw.rect(surf,rc,(self.rect.x,self.rect.y+row,self.rect.w,1))
            pygame.draw.rect(surf,lerpC(c,(255,255,255),0.45),(self.rect.x+2,self.rect.y,self.rect.w-4,3))
            pygame.draw.rect(surf,lerpC(c,(0,0,0),0.38),(self.rect.x,self.rect.y+3,2,self.rect.h-3))

        # Deadly spikes on top
        if self.deadly:
            ns=max(2,self.rect.w//14)
            sw2=self.rect.w/ns
            sc=lerpC((255,40,0),(255,180,0),pulse)
            for i in range(ns):
                sx2=int(self.rect.x+i*sw2+sw2//2); sy2=self.rect.y
                pygame.draw.polygon(surf,sc,[(sx2-4,sy2),(sx2,sy2-11),(sx2+4,sy2)])
                pygame.draw.polygon(surf,lerpC(sc,(255,255,255),0.4),[(sx2-2,sy2-1),(sx2,sy2-9),(sx2+2,sy2-1)])
            # Red pulse glow
            dg=pygame.Surface((self.rect.w,24),pygame.SRCALPHA)
            dg.fill((255,30,0,int(30+pulse*30)))
            surf.blit(dg,(self.rect.x,self.rect.y-24))

        # Boost arrow (animated)
        if self.boost:
            for oi in range(3):
                ao=int(140-oi*40)
                ay=self.rect.y-10-oi*7+int(pulse*4)
                ax=self.rect.centerx
                pts=[(ax,ay-10),(ax-7,ay+1),(ax,ay-4),(ax+7,ay+1)]
                bs=pygame.Surface((20,18),pygame.SRCALPHA)
                adj=[(p[0]-ax+10,p[1]-ay+10) for p in pts]
                pygame.draw.polygon(bs,(*lerpC((100,255,100),(200,255,200),pulse),ao),adj)
                surf.blit(bs,(ax-10,ay-10))

        # Crumble cracks
        if self.crumbling and self.crumble_timer>8:
            t=self.crumble_timer/40
            for cpx,cpy in self.crack_pts:
                if cpx<self.rect.w and cpy<self.rect.h:
                    x1=self.rect.x+cpx; y1=self.rect.y+cpy
                    pygame.draw.line(surf,(0,0,0),(x1,y1),
                        (x1+random.randint(-8,8),y1+random.randint(-4,4)),1)
            if t>0.5:
                cs=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
                cs.fill((0,0,0,int(80*(t-0.5)*2))); surf.blit(cs,self.rect.topleft)

        # Moving platform trail
        if self.moving and len(self.path_pts)>1:
            for i in range(1,len(self.path_pts)):
                t=i/len(self.path_pts)
                a=int(25*t)
                pygame.draw.line(surf,(*accent,a),
                    self.path_pts[i-1],self.path_pts[i],1)

# ═══════════════════════════════════════════════════════════════
#  ENEMY  (3D sphere + death animation + world-themed)
# ═══════════════════════════════════════════════════════════════
class Enemy:
    def __init__(self,x,y,etype="patrol",color=(200,50,50),
                 px1=0,px2=0,speed=2.0,size=20,
                 ocx=0,ocy=0,orb_r=80,orb_spd=0.02,
                 shoot_iv=0,hp=1,world_idx=0):
        self.x,self.y=float(x),float(y)
        self.etype=etype; self.color=color
        self.speed=speed; self.size=size
        self.px1,self.px2=float(px1),float(px2); self.dir=1
        self.ocx,self.ocy=float(ocx),float(ocy)
        self.orb_r=orb_r; self.orb_spd=orb_spd
        self.angle=random.uniform(0,math.tau)
        self.shoot_iv=shoot_iv; self.shoot_t=0
        self.bullets=[]; self.alive=True; self.t=0.0
        self.hp=hp; self.max_hp=hp; self.hurt_t=0
        self.warn_ring=0.0; self.world_idx=world_idx
        # Squish/stretch juice
        self.sq_x=1.0; self.sq_y=1.0
        self.bounce_vy=-(2+random.uniform(1,3)); self.bounce_on=False
        self.emissive=(etype in ["chase","teleport","spiral","bouncer"])
        # Death animation state
        self.dying=False; self.die_t=0
        # Per-type extras
        self.spiral_r=0

    def squish(self,sx,sy):
        self.sq_x=sx; self.sq_y=sy

    def update(self, px=0, py=0):
        self.t+=1
        if self.hurt_t>0: self.hurt_t-=1
        # Restore squish
        self.sq_x=lerp(self.sq_x,1.0,0.18); self.sq_y=lerp(self.sq_y,1.0,0.18)

        if not self.alive: return

        if self.etype=="patrol":
            self.x+=self.speed*self.dir
            if self.x<self.px1: self.dir=1; self.squish(0.7,1.3)
            if self.x>self.px2: self.dir=-1; self.squish(0.7,1.3)
        elif self.etype=="orbit":
            self.angle+=self.orb_spd
            self.x=self.ocx+math.cos(self.angle)*self.orb_r
            self.y=self.ocy+math.sin(self.angle)*self.orb_r
        elif self.etype=="chase":
            dx2=px-self.x; dy2=py-self.y; d=math.hypot(dx2,dy2)
            if d>2:
                self.x+=(dx2/d)*self.speed; self.y+=(dy2/d)*self.speed
                self.sq_x=lerp(self.sq_x,1.25,0.1); self.sq_y=lerp(self.sq_y,0.8,0.1)
        elif self.etype=="sine":
            self.x+=self.speed
            self.y=self.ocy+math.sin(self.t*0.05)*self.orb_r
            if self.x>self.px2: self.x=self.px1
        elif self.etype=="zigzag":
            self.x+=self.speed*self.dir
            if self.t%28==0: self.dir*=-1; self.squish(1.3,0.7)
            self.y=self.ocy+math.sin(self.t*0.09)*self.orb_r
        elif self.etype=="teleport":
            if self.t%95==0:
                self.x=random.uniform(120,W-120); self.y=random.uniform(80,H-200)
                ps.emit(self.x,self.y,count=20,life=30,color=self.color,spread=7,shape="ring")
                self.squish(1.5,0.5)
        elif self.etype=="spiral":
            self.angle+=self.orb_spd
            self.spiral_r=min(self.orb_r,self.t*0.35)
            self.x=self.ocx+math.cos(self.angle)*self.spiral_r
            self.y=self.ocy+math.sin(self.angle)*self.spiral_r
            if self.spiral_r>=self.orb_r:
                self.ocx=random.uniform(200,W-200); self.ocy=random.uniform(100,H-200); self.t=0
        elif self.etype=="bouncer":
            self.x+=self.speed*self.dir
            self.y+=self.bounce_vy; self.bounce_vy+=0.45
            if self.y>H-80: self.bounce_vy=-abs(self.bounce_vy)*0.82; self.y=H-80; self.squish(1.4,0.6)
            if self.x<80 or self.x>W-80: self.dir*=-1; self.squish(0.6,1.4)

        # Shooting
        if self.shoot_iv>0:
            self.shoot_t+=1
            self.warn_ring=max(0,(self.shoot_t-(self.shoot_iv-22))/22)
            if self.shoot_t>=self.shoot_iv:
                self.shoot_t=0; self.warn_ring=0
                dx2=px-self.x; dy2=py-self.y; d=math.hypot(dx2,dy2)
                if d>0:
                    spd=5.2
                    self.bullets.append({"x":self.x,"y":self.y,
                        "vx":(dx2/d)*spd,"vy":(dy2/d)*spd,"life":210,"t":0})
                    if self.max_hp>=3:
                        for ao in [-0.22,0.22]:
                            a=math.atan2(dy2,dx2)+ao
                            self.bullets.append({"x":self.x,"y":self.y,
                                "vx":math.cos(a)*spd,"vy":math.sin(a)*spd,"life":210,"t":0})
                self.squish(0.6,1.4)

        for b in self.bullets:
            b["x"]+=b["vx"]; b["y"]+=b["vy"]; b["life"]-=1; b["t"]+=1
        self.bullets=[b for b in self.bullets if b["life"]>0 and 0<b["x"]<W and 0<b["y"]<H]

    def take_hit(self):
        self.hp-=1; self.hurt_t=8; self.squish(0.5,1.5)
        ps.emit(self.x,self.y,count=8,life=18,color=(255,255,255),spread=4,size=3,shape="spark")
        if self.hp<=0:
            self.alive=False
            return True
        return False

    def get_rect(self):
        s=self.size
        return pygame.Rect(int(self.x-s//2),int(self.y-s//2),s,s)

    def draw(self, surf, tick):
        if not self.alive: return
        pulse=(math.sin(tick*0.1)+1)/2
        wt=WTHEME(self.world_idx)
        hurt_f=self.hurt_t/8

        # Warning ring for shooter
        if self.warn_ring>0:
            wr=int(self.size*1.8+self.warn_ring*26)
            ws=pygame.Surface((wr*2+4,wr*2+4),pygame.SRCALPHA)
            pygame.draw.circle(ws,(*hsv(0.0,1.0,1.0),int(155*self.warn_ring)),(wr+2,wr+2),wr,3)
            surf.blit(ws,(int(self.x)-wr-2,int(self.y)-wr-2))

        base_c=lerpC(self.color,(255,255,255),hurt_f*0.75)
        em_c=wt[3] if self.emissive else None

        draw_sphere(surf, self.x, self.y, self.size//2, base_c, tick,
                    emissive=self.emissive, emissive_color=em_c,
                    shadow=True, pulse_t=pulse*0.28,
                    squish_x=self.sq_x, squish_y=self.sq_y)

        # HP bar
        if self.max_hp>1:
            bw=self.size+14; bh=5
            bx=int(self.x-bw//2); by=int(self.y-self.size//2-16)
            pygame.draw.rect(surf,(35,12,12),(bx,by,bw,bh),border_radius=2)
            fw=int(bw*(self.hp/self.max_hp))
            hpc=lerpC((255,50,50),(255,210,50),self.hp/self.max_hp)
            pygame.draw.rect(surf,hpc,(bx,by,fw,bh),border_radius=2)
            pygame.draw.rect(surf,(255,255,255,40),(bx,by,bw,bh),1,border_radius=2)

        # Bullets as mini 3D spheres
        for b in self.bullets:
            bt=(b["t"]%20)/20
            bc=lerpC(self.color,(255,240,50),0.5+0.5*bt)
            draw_sphere(surf,b["x"],b["y"],5,bc,tick,shadow=False,pulse_t=bt)

# ═══════════════════════════════════════════════════════════════
#  PORTAL  (world-tinted wormhole)
# ═══════════════════════════════════════════════════════════════
class Portal:
    def __init__(self,x,y,world_idx=0):
        self.x,self.y=float(x),float(y)
        self.r=34; self.t=0.0; self.world_idx=world_idx

    def update(self):
        self.t+=0.05
        wt=WTHEME(self.world_idx)
        for i in range(3):
            a=self.t+i*math.tau/3
            ppx=self.x+math.cos(a)*(self.r+10)
            ppy=self.y+math.sin(a)*(self.r+10)
            ps.emit(ppx,ppy,count=1,life=30,color=wt[5],size=4,spread=1.2,grav=-0.025)

    def draw(self, surf):
        pulse=(math.sin(self.t*2)+1)/2
        wt=WTHEME(self.world_idx)
        # Multi-layer corona
        for ring in range(7,0,-1):
            a=max(0,48-ring*6)
            c=(*hsv((self.t*0.07+ring*0.10)%1,0.9,1.0),a)
            rs=self.r+ring*8+int(pulse*5)
            gs=pygame.Surface((rs*2+8,rs*2+8),pygame.SRCALPHA)
            pygame.draw.circle(gs,c,(rs+4,rs+4),rs,3)
            surf.blit(gs,(int(self.x)-rs-4,int(self.y)-rs-4))
        pc=hsv(self.t*0.07%1,0.85,1.0)
        draw_sphere(surf,self.x,self.y,self.r,pc,int(self.t*60),
                    emissive=True,emissive_color=wt[3],shadow=False,pulse_t=pulse)
        draw_text(surf,"EXIT",(int(self.x),int(self.y)-self.r-24),
                  (255,255,180),F_TINY,center=True)

# ═══════════════════════════════════════════════════════════════
#  PLAYER  (sprite character, squish/stretch, speed lines, double-jump)
# ═══════════════════════════════════════════════════════════════
PLAYER_SPRITE_PATH = resource_path("assets", "sprites", "player", "character_sheet.png")
PLAYER_FRAME_W = 96
PLAYER_FRAME_H = 80
PLAYER_VISUAL_SCALE = 0.7
SPIKE_HAZARDS_ENABLED = False

def sprite_row(row, count):
    return [(i * PLAYER_FRAME_W, row * PLAYER_FRAME_H, PLAYER_FRAME_W, PLAYER_FRAME_H)
            for i in range(count)]

PLAYER_ANIMATIONS = {
    "idle": sprite_row(0, 4),
    "walk": sprite_row(1, 8),
    "dash": sprite_row(2, 6),
    "jump": sprite_row(3, 6),
    "fall": sprite_row(4, 1),
    "land": sprite_row(5, 2),
    "hit": sprite_row(6, 3),
}

class Player:
    SIZE    = 22
    GRAVITY = 0.52
    JUMP    = -13.2
    JUMP2   = -11.5   # double jump
    SPEED   = 5.8
    DASH_V  = 15.0
    DASH_DUR= 9
    COYOTE  = 9
    JBUFFER = 8

    def __init__(self):
        self.rect=pygame.Rect(0,0,self.SIZE,self.SIZE)
        self.vx=self.vy=0.0
        self.on_ground=False
        self.coyote_t=0; self.jbuffer_t=0
        self.trail=[]; self.t=0
        self.dash_t=0; self.dashing=False; self.dash_dir=1; self.dashing_t=0
        self.invincible=0; self.world_idx=0
        self.facing=1
        self.anim_state="idle"
        self.land_anim_t=0
        self.hit_anim_t=0
        self.sprite=SpriteAnimator(PLAYER_SPRITE_PATH, PLAYER_ANIMATIONS,
                                   frame_duration=5, scale=1)
        # Squish/stretch
        self.sq_x=1.0; self.sq_y=1.0
        # Double jump
        self.jumps_left=2
        # Speed lines
        self.speed_lines=[]  # [(x,y,len,alpha)]
        self.shield_active=False
        self.ghost_active=False
        self.rage_active=False

    def spawn(self,x,y,hit=False):
        self.rect.x,self.rect.y=x,y
        self.vx=self.vy=0.0; self.on_ground=False
        self.coyote_t=0; self.jbuffer_t=0
        self.dash_t=0; self.dashing=False
        self.invincible=60; self.trail.clear()
        self.sq_x=1.0; self.sq_y=1.0; self.jumps_left=2
        self.anim_state="hit" if hit else "idle"
        self.land_anim_t=0
        self.hit_anim_t=18 if hit else 0

    def _squish(self,sx,sy):
        self.sq_x=sx; self.sq_y=sy

    def hit(self):
        self.hit_anim_t=18
        self.anim_state="hit"

    def _choose_animation(self):
        if self.hit_anim_t>0:
            return "hit"
        if self.land_anim_t>0:
            return "land"
        if self.dashing:
            return "dash"
        if not self.on_ground and self.vy < -1.2:
            return "jump"
        if not self.on_ground and self.vy > 1.2:
            return "fall"
        if abs(self.vx)>0.2:
            return "walk"
        return "idle"

    def update(self, platforms, dx, jump, dash, emotion_profile=None, skills=None):
        emotion_profile = emotion_profile or {}
        skills = skills or SkillTree()

        self.t+=1
        if self.invincible>0: self.invincible-=1
        if self.dash_t>0: self.dash_t-=1
        if self.land_anim_t>0: self.land_anim_t-=1
        if self.hit_anim_t>0: self.hit_anim_t-=1

        # Restore squish
        self.sq_x=lerp(self.sq_x,1.0,0.20)
        self.sq_y=lerp(self.sq_y,1.0,0.20)

        if dx>0.05: self.facing=1
        elif dx<-0.05: self.facing=-1

        wt=WTHEME(self.world_idx)

        # ── DASH ───────────────────────────────────────────────
        if dash and self.dash_t==0 and not self.dashing:
            self.dashing=True; self.dash_dir=1 if dx>=0 else -1
            self.dashing_t=self.DASH_DUR
            self.dash_t=28 if skills.has("power_dash") else 35
            self.vy*=0.3
            play(SND_DASH)
            self._squish(1.6,0.5)
            ps.emit(self.rect.centerx,self.rect.centery,
                    count=16,life=20,color=(166,88,255),size=5,spread=3,grav=0,shape="spark")

        if self.dashing:
            self.dashing_t-=1
            dash_power=emotion_profile.get("dash_power",1.0) * (1.18 if skills.has("power_dash") else 1.0)
            self.vx=self.dash_dir*self.DASH_V*dash_power
            self.facing=self.dash_dir
            if self.t%2==0:
                ps.emit(self.rect.centerx-self.dash_dir*9,self.rect.centery+2,
                        vx=-self.dash_dir*1.8,vy=0,count=3,life=18,
                        color=(166,88,255),size=4,spread=1.5,grav=0,shape="spark")
            if self.dashing_t<=0: self.dashing=False

        if not self.dashing:
            self.vx=dx*self.SPEED*emotion_profile.get("movement",1.0)

        # ── COYOTE / JUMP BUFFER ───────────────────────────────
        was_grounded=self.on_ground
        if was_grounded:
            self.coyote_t=self.COYOTE
            self.jumps_left=2 + emotion_profile.get("extra_jumps",0)
        elif self.coyote_t>0: self.coyote_t-=1

        if jump: self.jbuffer_t=self.JBUFFER
        elif self.jbuffer_t>0: self.jbuffer_t-=1

        # ── JUMP (with double-jump) ────────────────────────────
        if self.jbuffer_t>0:
            if self.coyote_t>0:  # ground/coyote jump
                self.vy=self.JUMP*emotion_profile.get("jump",1.0); self.coyote_t=0; self.jbuffer_t=0
                self.jumps_left=max(0,self.jumps_left-1)
                play(SND_JUMP)
                self._squish(0.7,1.4)
                ps.emit(self.rect.centerx,self.rect.bottom,
                        count=14,life=24,color=wt[5],size=4,spread=4,grav=-0.05)
            elif self.jumps_left>0 and not was_grounded and skills.has("double_jump"):  # double jump
                self.vy=self.JUMP2*emotion_profile.get("jump",1.0); self.jbuffer_t=0
                self.jumps_left-=1
                play(SND_DJUMP)
                self._squish(1.3,0.65)
                # Double jump ring burst
                for a in range(0,360,45):
                    ang=math.radians(a)
                    ps.emit(self.rect.centerx,self.rect.centery,
                            vx=math.cos(ang)*3,vy=math.sin(ang)*3,
                            count=1,life=22,color=wt[5],size=3,spread=1,grav=0,shape="ring")

        # ── GRAVITY ───────────────────────────────────────────
        if not self.dashing: self.vy+=self.GRAVITY*emotion_profile.get("gravity",1.0)
        self.vy=clamp(self.vy,-20,18)

        # ── COLLIDE ───────────────────────────────────────────
        self.rect.x+=int(self.vx)
        self.rect.x=clamp(self.rect.x,20,W-40)
        self._res_x(platforms)
        self.rect.y+=int(self.vy)
        if self.rect.y < 0:
            self.rect.y = 0
            if self.vy < 0: self.vy = 0
        self.on_ground=False
        landed=self._res_y(platforms)

        if landed and not was_grounded and abs(self.vy)>3:
            play(SND_LAND)
            self.land_anim_t=10
            self._squish(1.35,0.6)
            ps.emit(self.rect.centerx,self.rect.bottom,
                    count=10,life=18,color=wt[5],size=3,spread=3,grav=0.07)

        # Sprite afterimages during high-speed movement.
        if self.dashing:
            self.trail.append((self.rect.centerx,self.rect.bottom+4,self.facing,self.sq_x,self.sq_y))
            if len(self.trail)>8: self.trail.pop(0)
        elif self.trail:
            self.trail=self.trail[-6:]
            self.trail.pop(0)

        # Speed lines (when moving fast)
        spd=abs(self.vx)
        if spd>8 or self.dashing:
            for _ in range(3):
                lx=self.rect.centerx+random.randint(-12,12)
                ly=self.rect.centery+random.randint(-8,8)
                ln=int(spd*2.5+random.randint(5,15))
                self.speed_lines.append([lx,ly,ln,200])
        self.speed_lines=[[l[0],l[1],l[2],max(0,l[3]-18)] for l in self.speed_lines if l[3]>0]
        self.anim_state=self._choose_animation()
        self.sprite.update(self.anim_state)

    def _res_x(self, platforms):
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vx>0: self.rect.right=p.rect.left
                elif self.vx<0: self.rect.left=p.rect.right

    def _res_y(self, platforms):
        landed=False
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vy>0:
                    self.rect.bottom=p.rect.top; self.vy=0
                    self.on_ground=True; landed=True
                    if p.crumble and not p.crumbling: p.crumbling=True
                    if p.boost:
                        self.vy=-20; play(SND_BOOST)
                        wt=WTHEME(self.world_idx)
                        ps.burst(self.rect.centerx,self.rect.bottom,
                                 count=20,color=(100,255,100),world=self.world_idx)
                        self._squish(0.5,1.6)
                elif self.vy<0:
                    self.rect.top=p.rect.bottom; self.vy=0

        return landed

    def check_deadly(self, platforms):
        if self.invincible>0: return False
        for p in platforms:
            if p.deadly and p.visible and self.rect.colliderect(p.rect): return True
        return False

    def draw(self, surf):
        wt=WTHEME(self.world_idx)
        profile=get_emotion_profile(level_meta(self.world_idx)["emotion"])

        # Speed lines behind player
        face=-self.dash_dir if self.dashing else (-1 if self.vx<-2 else 1)
        for sl in self.speed_lines:
            a=sl[3]
            lx2=sl[0]+face*sl[2]
            pygame.draw.line(surf,(*wt[5],a),(sl[0],sl[1]),(lx2,sl[1]),1)

        # Sprite afterimage trail, replacing the old mini-ball trail.
        for i,(tx,ty,tf,tsx,tsy) in enumerate(self.trail):
            t=(i+1)/max(1,len(self.trail))
            self.sprite.draw(surf,(tx,ty),facing=tf,
                             squash=(lerp(1.0,tsx,t*0.2)*PLAYER_VISUAL_SCALE,
                                      lerp(1.0,tsy,t*0.2)*PLAYER_VISUAL_SCALE),
                             alpha=int(30+60*t))

        if self.invincible>0 and (self.invincible//4)%2==1: return

        cx=self.rect.centerx; cy=self.rect.centery
        r=self.SIZE//2

        # Double jump indicator ring
        if self.jumps_left>=1 and not self.on_ground:
            jr=r+6+int(math.sin(self.t*0.15)*2)
            js=pygame.Surface((jr*2+4,jr*2+4),pygame.SRCALPHA)
            jc=(*wt[3],int(80+(self.jumps_left==2)*40))
            pygame.draw.circle(js,jc,(jr+2,jr+2),jr,2)
            surf.blit(js,(cx-jr-2,cy-jr-2))

        # Ground shadow under the character.
        sh=pygame.Surface((32,9),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,72),(0,0,32,9))
        surf.blit(sh,(cx-16,self.rect.bottom-1))

        mood=profile.get("mood","balanced")
        breathe=1.0
        if self.anim_state=="idle":
            breathe=1.0+math.sin(self.t*0.08)*0.035
            if self.t%180==0:
                ps.emit(cx+self.facing*8,self.rect.y+4,count=2,life=35,color=wt[5],size=2,spread=0.4,grav=-0.01)
        if mood=="nervous" and self.t%28==0:
            ps.emit(cx,self.rect.y+8,count=1,life=22,color=(130,90,210),size=2,spread=0.8,grav=-0.02)
        elif mood=="energetic" and self.t%16==0:
            ps.emit(cx,self.rect.bottom-8,count=1,life=24,color=wt[3],size=2,spread=0.8,grav=-0.01,shape="spark")

        aura_r=18+int(math.sin(self.t*0.05)*2)
        pygame.draw.circle(surf,(*wt[3],32),(cx,self.rect.centery),aura_r,1)

        # Active shield: pulsing hexagon bubble
        if self.shield_active:
            pulse_s=(math.sin(self.t*0.25)+1)/2
            sr=28+int(pulse_s*5)
            sc=(int(80+175*pulse_s),int(200+55*pulse_s),255,int(140+80*pulse_s))
            hex_pts=[(cx+int(sr*math.cos(math.pi/2+i*math.pi/3)),
                      self.rect.centery+int(sr*math.sin(math.pi/2+i*math.pi/3)))
                     for i in range(6)]
            hs=pygame.Surface((sr*2+16,sr*2+16),pygame.SRCALPHA)
            pygame.draw.polygon(hs,(*sc[:3],int(sc[3]*0.18)),
                [(x-cx+sr+8,y-self.rect.centery+sr+8) for x,y in hex_pts])
            pygame.draw.polygon(hs,sc[:3]+[sc[3]],
                [(x-cx+sr+8,y-self.rect.centery+sr+8) for x,y in hex_pts],3)
            surf.blit(hs,(cx-sr-8,self.rect.centery-sr-8))
            if int(self.t)%4==0:
                ai=random.randint(0,5)
                px2=cx+int(sr*math.cos(math.pi/2+ai*math.pi/3))
                py2=self.rect.centery+int(sr*math.sin(math.pi/2+ai*math.pi/3))
                ps.emit(px2,py2,count=1,life=18,color=(120,220,255),size=3,spread=0.6,grav=0)

        # Rage Mode: fire aura + intense red-orange glow
        if self.rage_active:
            pulse_r=(math.sin(self.t*0.18)+1)/2
            for ring_r,ring_a in [(26,60),(36,30),(46,14)]:
                rr=ring_r+int(pulse_r*4)
                ra_surf=pygame.Surface((rr*2+4,rr*2+4),pygame.SRCALPHA)
                pygame.draw.circle(ra_surf,(255,int(80+pulse_r*60),20,ring_a),(rr+2,rr+2),rr,3)
                surf.blit(ra_surf,(cx-rr-2,self.rect.centery-rr-2))
            # fire particles from feet
            if int(self.t)%3==0:
                ps.emit(cx+random.randint(-8,8),self.rect.bottom-4,
                        count=2,life=22,color=(255,random.randint(60,160),20),
                        size=random.randint(2,4),spread=0.9,grav=-0.12)

        # Ghost Step: semi-transparent ghostly overlay + echo copies
        if self.ghost_active:
            pulse_g=(math.sin(self.t*0.22)+1)/2
            # Ghostly echo ring
            gr=22+int(pulse_g*6)
            gs=pygame.Surface((gr*2+6,gr*2+6),pygame.SRCALPHA)
            pygame.draw.circle(gs,(160,130,255,int(50+pulse_g*50)),(gr+3,gr+3),gr,2)
            surf.blit(gs,(cx-gr-3,self.rect.centery-gr-3))
            # Draw 2 ghost copies offset behind player
            for gi in range(1,3):
                gox=cx-self.facing*gi*14
                ghost_s=pygame.Surface((self.SIZE+4,self.SIZE+12),pygame.SRCALPHA)
                self.sprite.draw(ghost_s,(self.SIZE//2+2,self.SIZE+6),
                                 facing=self.facing,
                                 squash=(self.sq_x*PLAYER_VISUAL_SCALE,
                                         self.sq_y*PLAYER_VISUAL_SCALE))
                ghost_s.set_alpha(int(55-gi*18))
                # tint purple
                tint=pygame.Surface(ghost_s.get_size(),pygame.SRCALPHA)
                tint.fill((120,80,255,30))
                ghost_s.blit(tint,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
                surf.blit(ghost_s,(gox-self.SIZE//2-2,self.rect.bottom+4-self.SIZE-12))
            # particles drifting upward
            if int(self.t)%5==0:
                ps.emit(cx+random.randint(-10,10),self.rect.centery+random.randint(-10,10),
                        count=1,life=30,color=(180,140,255),size=2,spread=0.5,grav=-0.05)

        # Draw sprite (ghost step renders it semi-transparent)
        if self.ghost_active:
            ghost_sprite_s=pygame.Surface((self.SIZE+20,self.SIZE+20),pygame.SRCALPHA)
            self.sprite.draw(ghost_sprite_s,(self.SIZE//2+10,self.SIZE+10),
                             facing=self.facing,
                             squash=(self.sq_x*PLAYER_VISUAL_SCALE,
                                      self.sq_y*PLAYER_VISUAL_SCALE*breathe))
            ghost_sprite_s.set_alpha(140)
            surf.blit(ghost_sprite_s,(cx-self.SIZE//2-10,self.rect.bottom+4-self.SIZE-10))
        else:
            self.sprite.draw(surf,(cx,self.rect.bottom+4),facing=self.facing,
                             squash=(self.sq_x*PLAYER_VISUAL_SCALE,
                                      self.sq_y*PLAYER_VISUAL_SCALE*breathe))

        # Dash ready indicator
        if self.dash_t==0:
            di=pygame.Surface((r*2+10,3),pygame.SRCALPHA)
            di.fill((*wt[3],190))
            surf.blit(di,(cx-r-5,self.rect.bottom+3))

player = Player()

# ═══════════════════════════════════════════════════════════════
#  PARALLAX BACKGROUND  (3 layers per world)
# ═══════════════════════════════════════════════════════════════
class Background:
    def __init__(self):
        self.stars=[(random.randint(0,W),random.randint(0,H),
                     random.uniform(0.3,2.2),random.uniform(0,6.28)) for _ in range(220)]
        self.t=0
        self.scanlines=pygame.Surface((W,H),pygame.SRCALPHA)
        for y in range(0,H,4):
            pygame.draw.line(self.scanlines,(0,0,0,7),(0,y),(W,y))
        # Parallax layer objects (generated per world change)
        self.parallax=[]; self.last_world=-1
        # Fog gradient surface cache
        self._fog_cache={}

    def _gen_parallax(self, world_idx):
        wt=WTHEME(world_idx)
        self.parallax=[]
        # Layer 1: far (slowest scroll)
        for _ in range(14):
            x=random.randint(0,W); y=random.randint(50,H-100)
            s=random.uniform(20,55)
            self.parallax.append({"x":float(x),"y":float(y),"s":s,
                                  "layer":0,"c":wt[1],"t":random.uniform(0,6.28)})
        # Layer 2: mid
        for _ in range(10):
            x=random.randint(0,W); y=random.randint(60,H-80)
            s=random.uniform(10,30)
            self.parallax.append({"x":float(x),"y":float(y),"s":s,
                                  "layer":1,"c":wt[2],"t":random.uniform(0,6.28)})

    def draw(self, surf, idx):
        self.t+=1
        if self.last_world!=idx:
            self._gen_parallax(idx); self.last_world=idx
        wt=WTHEME(idx)
        meta=level_meta(idx)
        profile=get_emotion_profile(meta["emotion"])
        events=WorldEventSystem(meta)
        c1,c2=wt[0],wt[1]

        # Gradient sky
        for y in range(0,H,2):
            c=lerpC(c1,c2,y/H)
            pygame.draw.rect(surf,c,(0,y,W,2))

        # Parallax layer 0 (far bg shapes)
        for p in self.parallax:
            if p["layer"]!=0: continue
            p["t"]+=0.008
            ox=int(math.sin(p["t"]*0.6)*8)
            oy=int(math.sin(p["t"]*0.4)*4)
            s=int(p["s"])
            c=lerpC(c2,c1,0.35)
            ac=(*c,int(20+10*math.sin(p["t"])))
            gs=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,ac,(s,s),s)
            surf.blit(gs,(p["x"]+ox-s,p["y"]+oy-s))

        # World-specific bg art
        self._draw_world_art(surf, idx)

        # Parallax layer 1 (mid shapes, slightly transparent)
        for p in self.parallax:
            if p["layer"]!=1: continue
            p["t"]+=0.018
            ox=int(math.sin(p["t"]*0.9)*5)
            s=int(p["s"])
            c=lerpC(c2,c1,0.18)
            ac=(*c,int(14+8*math.sin(p["t"])))
            gs=pygame.Surface((s*2,s),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,ac,(0,0,s*2,s))
            surf.blit(gs,(p["x"]+ox-s,p["y"]-s//2))

        # Stars
        for sx,sy,ss,sp in self.stars:
            tw=(math.sin(self.t*0.032+sp)+1)/2
            br=int(65+155*tw)
            col=(br,br,min(255,br+44))
            r=max(1,int(ss*tw))
            pygame.draw.circle(surf,col,(sx,sy),r)

        # Fog layer (world-colored bottom fog)
        fog_c=wt[8]
        if idx not in self._fog_cache:
            fc=pygame.Surface((W,80),pygame.SRCALPHA)
            for fy in range(80):
                a=int(80*(1-fy/80))
                fc.fill((*fog_c,a),(0,fy,W,1))
            self._fog_cache[idx]=fc
        surf.blit(self._fog_cache[idx],(0,H-80))

        # Scanlines
        surf.blit(self.scanlines,(0,0))

        if profile.get("visibility",1.0) < 0.9:
            darkness=int((1.0-profile["visibility"])*150)
            shade=pygame.Surface((W,H),pygame.SRCALPHA)
            shade.fill((0,0,0,darkness))
            pygame.draw.circle(shade,(0,0,0,0),(W//2,H//2),260)
            surf.blit(shade,(0,0))

        if events.event_flags().get("fog"):
            fog=pygame.Surface((W,H),pygame.SRCALPHA)
            for i in range(7):
                fy=int((self.t*0.25+i*95)%H)
                pygame.draw.ellipse(fog,(*wt[8],34),(-120+i*210,fy,360,70))
            surf.blit(fog,(0,0))

        if events.has_major_challenge:
            pulse=(math.sin(self.t*0.045)+1)/2
            ring=pygame.Surface((W,H),pygame.SRCALPHA)
            pygame.draw.rect(ring,(*wt[3],int(25+pulse*32)),(0,0,W,H),8)
            surf.blit(ring,(0,0))

    def _draw_world_art(self, surf, idx):
        t=self.t
        wt=WTHEME(idx)
        if idx==1:  # Forest — tree silhouettes
            for i in range(13):
                tx=i*(W//13)+30; h=int(80+20*math.sin(i*1.3))
                c=lerpC((6,28,6),(12,50,12),i/12)
                pygame.draw.polygon(surf,c,[(tx,H-28),(tx-22,H-28-h),(tx+22,H-28-h)])
                pygame.draw.rect(surf,lerpC((30,18,6),(50,28,10),i/12),(tx-4,H-28,8,40))
        elif idx==2:  # Inferno — fire pillars
            for i in range(8):
                fx=i*(W//8)+55
                fh=int(70+math.sin(t*0.07+i)*38)
                fc=(*lerpC((160,40,0),(255,120,0),(math.sin(t*0.09+i)+1)/2),55)
                fs=pygame.Surface((24,fh),pygame.SRCALPHA)
                for fy in range(fh):
                    a=int(55*(1-fy/fh)); cc=lerpC((255,55,0),(255,200,0),fy/fh)
                    fs.fill((*cc,a),(0,fy,24,1))
                surf.blit(fs,(fx-12,H-28-fh))
        elif idx==3:  # Ocean — caustics/ripples
            for i in range(6):
                rx=i*(W//6)+40; ry=H-60-int(math.sin(t*0.04+i)*20)
                rr=int(30+15*math.sin(t*0.06+i*0.8))
                rs=pygame.Surface((rr*2,rr),pygame.SRCALPHA)
                pygame.draw.ellipse(rs,(60,180,255,20),(0,0,rr*2,rr))
                surf.blit(rs,(rx-rr,ry))
        elif idx==5:  # Glacier — ice chunks bg
            for i in range(8):
                ix=i*(W//8)+random.choice([20,40]); iy=H-50-i*15
                iw=random.choice([40,55,35])
                ic=(*lerpC((80,180,210),(140,220,255),i/8),35)
                is2=pygame.Surface((iw,30),pygame.SRCALPHA)
                pts=[(0,30),(iw//4,0),(iw*3//4,0),(iw,30)]
                pygame.draw.polygon(is2,ic,pts)
                surf.blit(is2,(ix,iy))
        elif idx==7:  # Magma — lava flow floor
            for i in range(0,W,3):
                wy=H-38+int(math.sin(i*0.025+t*0.05)*9)
                c=lerpC((180,40,0),(255,120,0),(math.sin(i*0.02+t*0.04)+1)/2)
                pygame.draw.line(surf,c,(i,wy),(i+3,wy),3)
        elif idx==8:  # Space — distant galaxies
            for p in self.parallax[:8]:
                s=int(p["s"]*0.7)
                gc=(*wt[5],int(15+8*math.sin(p["t"])))
                gs=pygame.Surface((s*3,s),pygame.SRCALPHA)
                pygame.draw.ellipse(gs,gc,(0,0,s*3,s))
                angle=math.radians(p["t"]*20)
                surf.blit(gs,(int(p["x"])-s,int(p["y"])-s//2))
        elif idx==14:  # Volcanic — eruption
            for i in range(5):
                vx=i*(W//5)+80
                vh=int(30+math.sin(t*0.08+i*1.2)*20)
                for j in range(vh):
                    jt=j/vh
                    vc=(*lerpC((255,50,0),(255,200,50),jt),int(60*(1-jt)))
                    pygame.draw.circle(surf,vc,(vx+random.randint(-3,3),H-28-j-30),2)
        elif idx==19:  # Transcendence — divine rays
            for i in range(10):
                ra=i*(math.tau/10)+t*0.008
                rx=W//2+math.cos(ra)*700; ry=H//2+math.sin(ra)*600
                rc=(*hsv((t*0.004+i*0.10)%1,0.35,0.9),7)
                rs=pygame.Surface((W,H),pygame.SRCALPHA)
                pygame.draw.line(rs,rc,(W//2,H//2),(int(rx),int(ry)),4)
                surf.blit(rs,(0,0))

bg = Background()

# ═══════════════════════════════════════════════════════════════
#  LEVEL BUILDER  (20 fully unique, handcrafted + procedural)
# ═══════════════════════════════════════════════════════════════
def mk_P(x,y,w,h,wi,deadly=False,moving=False,mx=0,my=0,
         mrange=100,mspeed=1.5,phase=False,phase_time=90,crumble=False,boost=False):
    wt=WTHEME(wi)
    if deadly and not SPIKE_HAZARDS_ENABLED:
        p=Platform(x,y,w,h,wt[2],False,moving,mx,my,mrange,mspeed,
                   phase,phase_time,crumble,boost,wi)
        p.visible=False
        return p
    c=(195,22,22) if deadly else wt[2]
    return Platform(x,y,w,h,c,deadly,moving,mx,my,mrange,mspeed,
                    phase,phase_time,crumble,boost,wi)

def mk_E(x,y,etype,speed,wi,**kw):
    wt=WTHEME(wi)
    return Enemy(x,y,etype,wt[4],speed=speed,world_idx=wi,**kw)

def build_level(idx):
    wi=idx
    def walls():
        return [mk_P(0,H-28,W,28,wi),mk_P(0,0,18,H,wi),mk_P(W-18,0,18,H,wi)]

    platforms=[]; enemies=[]; coins=[]; start=(60,H-80); goal=(W-110,80)

    # WORLD 0: VOID — Clean tutorial staircase
    if idx==0:
        platforms=walls()+[
            mk_P(100,558,220,18,wi), mk_P(370,488,200,18,wi),
            mk_P(620,418,200,18,wi), mk_P(880,348,200,18,wi),
            mk_P(620,258,200,18,wi), mk_P(370,168,200,18,wi),
            mk_P(100,98,240,18,wi),
        ]
        enemies=[mk_E(370,458,"patrol",2.4,wi,px1=370,px2=558),
                 mk_E(620,388,"patrol",3.0,wi,px1=620,px2=808)]
        coins=[Coin(310,448),Coin(560,383),Coin(810,313),Coin(560,223),Coin(280,58)]
        start=(60,518); goal=(200,58)

    # WORLD 1: FOREST — Moving platforms + leaf hazards
    elif idx==1:
        platforms=walls()+[
            mk_P(80,558,160,18,wi),
            mk_P(295,498,120,18,wi,moving=True,mx=1,mrange=88,mspeed=1.3),
            mk_P(528,438,110,18,wi),
            mk_P(708,373,100,18,wi,moving=True,mx=1,mrange=68,mspeed=2.0),
            mk_P(878,308,170,18,wi),
            mk_P(708,223,110,18,wi),
            mk_P(462,160,190,18,wi),
            mk_P(208,100,175,18,wi),
            mk_P(408,548,54,18,wi,deadly=True),
            mk_P(762,393,54,18,wi,deadly=True),
        ]
        enemies=[mk_E(528,408,"patrol",3.2,wi,px1=528,px2=648),
                 mk_E(878,278,"patrol",2.9,wi,px1=878,px2=1058)]
        coins=[Coin(462,473),Coin(658,343),Coin(402,128)]
        start=(50,528); goal=(262,60)

    # WORLD 2: HELLFIRE — Orbit enemies, deadly floor spikes
    elif idx==2:
        platforms=walls()+[
            mk_P(80,558,138,18,wi),
            mk_P(292,488,104,18,wi,moving=True,mx=1,mrange=104,mspeed=2.2),
            mk_P(492,430,98,18,wi,deadly=True),
            mk_P(652,378,138,18,wi),
            mk_P(858,306,78,18,wi,moving=True,mx=1,mrange=86,mspeed=2.8),
            mk_P(663,236,118,18,wi),mk_P(443,178,98,18,wi),
            mk_P(223,128,158,18,wi),mk_P(52,78,202,18,wi),
            mk_P(512,568,74,18,wi,deadly=True),mk_P(763,568,74,18,wi,deadly=True),
        ]
        enemies=[mk_E(652,348,"patrol",3.7,wi,px1=652,px2=788),
                 mk_E(443,148,"orbit",2.0,wi,ocx=443,ocy=178,orb_r=64,orb_spd=0.048)]
        coins=[Coin(398,458),Coin(698,296),Coin(378,98)]
        start=(50,528); goal=(110,44)

    # WORLD 3: DEEP OCEAN — Phasing + zigzag + shooter
    elif idx==3:
        platforms=walls()+[
            mk_P(80,556,118,18,wi),
            mk_P(266,488,78,18,wi,phase=True,phase_time=68),
            mk_P(430,428,98,18,wi),
            mk_P(596,358,78,18,wi,phase=True,phase_time=58),
            mk_P(756,288,118,18,wi),
            mk_P(938,218,78,18,wi,moving=True,mx=0,my=1,mrange=62,mspeed=2.2),
            mk_P(738,148,138,18,wi),mk_P(490,98,198,18,wi),
            mk_P(246,128,138,18,wi),mk_P(52,78,198,18,wi),
            mk_P(356,576,98,18,wi,deadly=True),mk_P(662,576,98,18,wi,deadly=True),
        ]
        enemies=[mk_E(430,398,"patrol",4.2,wi,px1=430,px2=566),
                 mk_E(756,258,"orbit",2.0,wi,ocx=836,ocy=288,orb_r=84,orb_spd=0.055),
                 mk_E(490,68,"zigzag",3.7,wi,ocy=98,orb_r=48)]
        coins=[Coin(596,328),Coin(736,118),Coin(246,98)]
        start=(50,526); goal=(110,46)

    # WORLD 4: DESERT — Crumble + boost + shooter intro
    elif idx==4:
        platforms=walls()+[
            mk_P(80,556,98,18,wi),
            mk_P(250,490,80,18,wi,crumble=True),
            mk_P(422,430,80,18,wi,phase=True,phase_time=52),
            mk_P(592,368,80,18,wi,boost=True),
            mk_P(762,308,94,18,wi,moving=True,mx=0,my=1,mrange=76,mspeed=3.1),
            mk_P(592,228,80,18,wi,phase=True,phase_time=48),
            mk_P(422,168,80,18,wi,crumble=True),
            mk_P(250,108,90,18,wi),mk_P(80,88,180,18,wi),
            mk_P(360,576,78,18,wi,deadly=True),mk_P(616,576,78,18,wi,deadly=True),
            mk_P(872,576,78,18,wi,deadly=True),
        ]
        enemies=[mk_E(250,458,"patrol",4.2,wi,px1=250,px2=372),
                 mk_E(592,338,"orbit",2.0,wi,ocx=642,ocy=368,orb_r=72,orb_spd=0.068),
                 mk_E(422,138,"patrol",4.7,wi,px1=422,px2=542,shoot_iv=90),
                 mk_E(700,280,"sine",3.2,wi,px1=200,px2=900,ocy=280,orb_r=62)]
        coins=[Coin(592,340),Coin(422,140),Coin(250,80)]
        start=(50,526); goal=(140,48)

    # WORLD 5: GLACIER — narrow fast + crumble everywhere
    elif idx==5:
        platforms=walls()+[
            mk_P(80,556,88,18,wi),
            mk_P(238,490,72,18,wi,moving=True,mx=1,mrange=118,mspeed=2.9),
            mk_P(458,430,68,18,wi,phase=True,phase_time=48),
            mk_P(648,366,72,18,wi),
            mk_P(858,296,70,18,wi,moving=True,mx=0,my=1,mrange=88,mspeed=3.3),
            mk_P(658,216,68,18,wi,phase=True,phase_time=44),
            mk_P(458,156,70,18,wi,crumble=True),
            mk_P(250,96,86,18,wi),mk_P(80,80,172,18,wi),
            mk_P(338,576,72,18,wi,deadly=True),mk_P(568,576,72,18,wi,deadly=True),
            mk_P(798,576,72,18,wi,deadly=True),mk_P(1018,576,72,18,wi,deadly=True),
        ]
        enemies=[mk_E(458,398,"patrol",4.9,wi,px1=438,px2=578),
                 mk_E(658,186,"orbit",2.0,wi,ocx=718,ocy=216,orb_r=72,orb_spd=0.072),
                 mk_E(598,298,"zigzag",4.1,wi,ocy=298,orb_r=56)]
        coins=[Coin(648,338),Coin(458,128),Coin(250,68)]
        start=(50,526); goal=(138,46)

    # WORLD 6: NEON — Spiral enemy + shooter combo
    elif idx==6:
        platforms=walls()+[
            mk_P(80,556,82,18,wi),
            mk_P(233,486,68,18,wi,phase=True,phase_time=42),
            mk_P(418,426,66,18,wi,moving=True,mx=1,mrange=112,mspeed=3.0),
            mk_P(648,363,70,18,wi,crumble=True),
            mk_P(858,293,66,18,wi,phase=True,phase_time=38),
            mk_P(678,216,68,18,wi,moving=True,mx=0,my=1,mrange=83,mspeed=3.5),
            mk_P(478,156,66,18,wi,crumble=True),
            mk_P(268,96,80,18,wi),mk_P(80,78,168,18,wi),
            mk_P(328,576,70,18,wi,deadly=True),mk_P(556,576,70,18,wi,deadly=True),
            mk_P(784,576,70,18,wi,deadly=True),mk_P(1012,576,70,18,wi,deadly=True),
        ]
        enemies=[mk_E(418,396,"patrol",5.0,wi,px1=398,px2=562),
                 mk_E(648,333,"orbit",2.0,wi,ocx=698,ocy=363,orb_r=76,orb_spd=0.076),
                 mk_E(638,298,"spiral",2.0,wi,ocx=638,ocy=298,orb_r=102,orb_spd=0.042)]
        coins=[Coin(648,336),Coin(478,128),Coin(268,68)]
        start=(50,526); goal=(138,46)

    # WORLD 7: MAGMA — Bouncer enemy + lava floor hazards
    elif idx==7:
        platforms=walls()+[
            mk_P(80,556,78,18,wi),
            mk_P(228,486,65,18,wi,crumble=True),
            mk_P(408,426,63,18,wi,phase=True,phase_time=36),
            mk_P(598,362,66,18,wi,moving=True,mx=1,mrange=108,mspeed=3.2),
            mk_P(798,292,63,18,wi,crumble=True),
            mk_P(618,212,65,18,wi,phase=True,phase_time=32),
            mk_P(438,152,63,18,wi,moving=True,mx=0,my=1,mrange=78,mspeed=3.6),
            mk_P(258,92,78,18,wi),mk_P(80,76,162,18,wi),
            mk_P(320,576,68,18,wi,deadly=True),mk_P(548,576,68,18,wi,deadly=True),
            mk_P(776,576,68,18,wi,deadly=True),mk_P(1004,576,68,18,wi,deadly=True),
            mk_P(120,H-28,80,28,wi,deadly=True),mk_P(400,H-28,80,28,wi,deadly=True),
            mk_P(700,H-28,80,28,wi,deadly=True),mk_P(950,H-28,80,28,wi,deadly=True),
        ]
        enemies=[mk_E(408,396,"patrol",5.2,wi,px1=388,px2=556),
                 mk_E(598,332,"orbit",2.0,wi,ocx=648,ocy=362,orb_r=78,orb_spd=0.080),
                 mk_E(400,H-120,"bouncer",4.0,wi),
                 mk_E(800,H-120,"bouncer",3.8,wi)]
        coins=[Coin(598,334),Coin(438,124),Coin(258,64)]
        start=(50,526); goal=(136,44)

    # WORLDS 8–19: Procedural escalating horror
    else:
        diff=(idx-7)/12.0
        random.seed(idx*11+7)
        steps=9+idx//3
        xs=[80]+[random.randint(100,W-210) for _ in range(steps-2)]+[W-200]
        ys=[H-80]
        for i in range(1,steps):
            ys.append(max(70,ys[-1]-random.randint(42,90)))

        platforms=walls()
        for i,(x,y) in enumerate(zip(xs,ys)):
            w=max(45,182-idx*7)
            is_d  =random.random()<min(0.46,diff*0.44)
            is_m  =random.random()<min(0.74,diff*0.67) and not is_d
            is_ph =random.random()<min(0.56,diff*0.50) and not is_d and not is_m
            is_cr =random.random()<min(0.36,diff*0.30) and not is_d and not is_m
            is_b  =random.random()<0.07 and not is_d
            platforms.append(mk_P(x,y,w,18,wi,
                deadly=is_d,moving=is_m,
                mx=random.choice([-1,0,1]),my=random.choice([-1,0,1]),
                mrange=56+idx*5,mspeed=1.2+diff*3.6,
                phase=is_ph,phase_time=max(16,74-idx*3),
                crumble=is_cr,boost=is_b))
            if random.random()<0.28 and not is_d:
                coins.append(Coin(x+w//2,y-22))

        for i in range(idx//2):
            sx=random.randint(88,W-186)
            platforms.append(mk_P(sx,H-28,58,28,wi,deadly=True))

        ec=max(4,3+idx//2)
        is_final=(idx==TOTAL_LEVELS-1)
        # chase weight: 0 on all levels, high on level 100 only
        chase_w=8 if is_final else 0
        etype_pool=["patrol","orbit","sine","zigzag","spiral","bouncer","teleport","chase"]
        wts_pool=[3,2,2,2,max(0,int((idx-7)*0.6)),max(0,int((idx-9)*0.4)),max(0,int((idx-11)*0.5)),chase_w]
        for i in range(ec):
            spd=3.2+diff*5.4
            hp=max(1,int(1+diff*2.8))
            etype=random.choices(etype_pool,weights=wts_pool)[0]
            if etype=="patrol":
                ex=random.randint(148,W-148); ey=random.randint(198,H-98)
                enemies.append(mk_E(ex,ey,"patrol",spd,wi,px1=ex-142,px2=ex+142,hp=hp))
            elif etype=="orbit":
                cx2=random.randint(318,W-318); cy2=random.randint(198,H-208)
                enemies.append(mk_E(cx2,cy2,"orbit",2.0,wi,ocx=cx2,ocy=cy2,
                    orb_r=66+idx*4,orb_spd=0.025+diff*0.072))
            elif etype=="sine":
                ey=random.randint(198,H-208)
                enemies.append(mk_E(220,ey,"sine",spd*0.75,wi,px1=98,px2=W-98,
                    ocy=ey,orb_r=66+idx*3))
            elif etype=="zigzag":
                ey=random.randint(148,H-208)
                enemies.append(mk_E(318,ey,"zigzag",spd*0.94,wi,ocy=ey,orb_r=50+idx*3))
            elif etype=="spiral":
                cx2=random.randint(298,W-298); cy2=random.randint(148,H-198)
                enemies.append(mk_E(cx2,cy2,"spiral",2.0,wi,ocx=cx2,ocy=cy2,
                    orb_r=78+idx*3,orb_spd=0.034+diff*0.022))
            elif etype=="bouncer":
                enemies.append(mk_E(random.randint(198,W-198),H-198,"bouncer",spd,wi))
            elif etype=="teleport":
                enemies.append(mk_E(400,298,"teleport",0,wi,hp=hp+1))
            elif etype=="chase":
                ex=random.randint(208,W-208); ey=random.randint(108,H-208)
                enemies.append(mk_E(ex,ey,"chase",spd*0.75,wi,hp=hp))

        # Guarantee at least one chase enemy on the final level
        if is_final and not any(e.etype=="chase" for e in enemies):
            enemies.append(mk_E(W//2,H//2,"chase",diff*3.0,wi,hp=3))

        start=(50,H-80); goal=(W-108,80)

    return platforms,enemies,coins,start,goal

# ═══════════════════════════════════════════════════════════════
#  HUD  (world-tinted, combo display, dash, lives as 3D spheres)
# ═══════════════════════════════════════════════════════════════
def draw_hud(surf, idx, lives, tick, coins_total, coins_got, combo, dash_t, time_elapsed,
             shield_cooldown_t=0, skill_has_shield=False,
             ghost_cooldown_t=0, ghost_active_t=0, skill_has_ghost=False,
             rage_cooldown_t=0, rage_active_t=0, skill_has_rage=False):
    wt=WTHEME(idx)
    acc=wt[3]

    # Top bar
    bar=pygame.Surface((W,68),pygame.SRCALPHA)
    bar.fill((0,0,0,128))
    surf.blit(bar,(0,0))

    # World-tinted accent line
    ls=pygame.Surface((W,2),pygame.SRCALPHA)
    for px in range(0,W,2):
        a=int(160*math.sin(px/W*math.pi))
        ls.fill((*acc,a),(px,0,2,2))
    surf.blit(ls,(0,66))

    # ── Lives: 3D mini spheres ──────────────────────────────────
    for i in range(5):
        filled=i<lives
        hx=W-162+i*30; hy=28
        if filled:
            pulse=(math.sin(tick*0.09+i)+1)/2
            lc=lerpC((255,55,55),(255,140,90),pulse)
            draw_sphere(surf,hx,hy,10,lc,tick,shadow=False,
                       emissive=True,emissive_color=(255,60,60),pulse_t=pulse*0.4)
        else:
            pygame.draw.circle(surf,(45,45,62),(hx,hy),9,1)

    # World title
    name=MSGS[idx] if idx<len(MSGS) else "???"
    tc=hsv(tick*0.004%1,0.7,1.0)
    meta=level_meta(idx)
    wname=meta["world"]
    draw_text(surf,f"WORLD {idx+1:03d}/{TOTAL_LEVELS}  ·  {wname}",(W//2,7),acc,F_MD,center=True)
    draw_text(surf,f"{meta['name']} · {meta['emotion']}",(W//2,33),(175,185,215),F_TINY,center=True)
    event=WorldEventSystem(meta)
    if event.has_major_challenge:
        draw_text(surf,event.challenge_name,(W//2,50),lerpC(acc,(255,255,255),0.35),F_TINY,center=True)

    # Stats
    draw_text(surf,f"BEST: W{SD['best']+1}",(24,7),(155,165,235),F_TINY)
    draw_text(surf,f"DEATHS: {SD['deaths']}",(24,24),(215,95,95),F_TINY)
    cc=lerpC(acc,(255,255,200),0.3)
    draw_text(surf,f"◆ {coins_got}/{coins_total}",(24,41),cc,F_TINY)
    skills=SkillTree(SD.get("emotions", [])).describe()
    draw_text(surf,f"SKILLS: {skills}",(24,58),(110,125,175),F_XS)

    # Timer
    ts=int(time_elapsed)
    tm=ts//60; tss=ts%60
    draw_text(surf,f"⏱ {tm:02d}:{tss:02d}",(24+110,41),(180,180,220),F_TINY)

    # Combo display
    if combo>=2:
        cx2=W//2
        cy2=H-55
        ca=min(1.0,(combo-1)/8.0)
        cc2=lerpC((255,200,50),(255,50,50),ca)
        pulse2=(math.sin(tick*0.2)+1)/2
        csize=int(24+combo*2+pulse2*4)
        # Background glow
        cgs=pygame.Surface((200,44),pygame.SRCALPHA)
        cgs.fill((0,0,0,80))
        pygame.draw.rect(cgs,(*cc2,int(60+pulse2*40)),(0,0,200,44),2,border_radius=8)
        surf.blit(cgs,(cx2-100,cy2-4))
        c_surf=outlined(f"✕{combo} COMBO!",F_MD,cc2,(0,0,0),2)
        surf.blit(c_surf,(cx2-c_surf.get_width()//2,cy2))

    # Dash bar
    bw=112; bx=W-bw-20; by=H-22
    if dash_t==0:
        pygame.draw.rect(surf,(*acc,210),(bx,by,bw,7),border_radius=3)
        draw_text(surf,"DASH READY",(bx+bw//2,by-16),acc,F_TINY,center=True)
    else:
        pct=1-(dash_t/35)
        pygame.draw.rect(surf,(22,22,40),(bx,by,bw,7),border_radius=3)
        fc=lerpC((60,70,90),acc,pct)
        pygame.draw.rect(surf,fc,(bx,by,int(bw*pct),7),border_radius=3)
        draw_text(surf,"DASH",(bx+bw//2,by-16),(78,92,108),F_TINY,center=True)

    # Skill cooldown bars (stacked above dash bar, right side)
    # Each bar is 20px taller than the one below it
    bar_slot=0  # counts bars added so far (grows upward)

    def _skill_bar(label, key_hint, color, cooldown, max_cd, active=False):
        nonlocal bar_slot
        bw2=112; bx2=W-bw2-20; by2=H-42-bar_slot*20
        bar_slot+=1
        if active:
            pulse=(math.sin(tick*0.18)+1)/2
            ac=lerpC(color,(255,255,255),pulse*0.35)
            pygame.draw.rect(surf,(*ac,230),(bx2,by2,bw2,6),border_radius=3)
            draw_text(surf,f"{key_hint}:ACTIVE!",(bx2+bw2//2,by2-14),ac,F_TINY,center=True)
        elif cooldown==0:
            pygame.draw.rect(surf,(*color,210),(bx2,by2,bw2,6),border_radius=3)
            draw_text(surf,f"{key_hint}:{label}",(bx2+bw2//2,by2-14),color,F_TINY,center=True)
        else:
            pct2=1-(cooldown/max_cd)
            pygame.draw.rect(surf,(22,22,40),(bx2,by2,bw2,6),border_radius=3)
            fc2=lerpC((40,50,70),color,pct2)
            pygame.draw.rect(surf,fc2,(bx2,by2,int(bw2*pct2),6),border_radius=3)
            draw_text(surf,label,(bx2+bw2//2,by2-14),(50,65,85),F_TINY,center=True)

    if skill_has_shield:
        _skill_bar("SHIELD","E",(80,200,255),shield_cooldown_t,300)
    if skill_has_ghost:
        _skill_bar("GHOST","R",(180,160,255),ghost_cooldown_t,900,active=ghost_active_t>0)
    if skill_has_rage:
        rage_c=(255,90,40) if rage_active_t>0 else (255,140,60)
        _skill_bar("RAGE","AUTO",rage_c,rage_cooldown_t,1200,active=rage_active_t>0)

    # Controls
    def _kname(k): return pygame.key.name(k).upper()
    hint=(f"{_kname(SETTINGS.get('key_left',97))}/{_kname(SETTINGS.get('key_right',100))}:Move"
          f"  {_kname(SETTINGS.get('key_jump',32))}:Jump"
          f"  {_kname(SETTINGS.get('key_dash',1073742049))}:Dash"
          f"  {_kname(SETTINGS.get('key_skill',101))}:Shield"
          f"  {_kname(SETTINGS.get('key_ghost',114))}:Ghost"
          f"  {_kname(SETTINGS.get('key_ultimate',113))}:Ultimate"
          f"  {_kname(SETTINGS.get('key_pause',27))}:Pause")
    draw_text(surf,hint,(W//2,H-14),(68,72,108),F_TINY,center=True,shadow=False)

# ═══════════════════════════════════════════════════════════════
#  WORLD INTRO CARD  (cinematic world name flash on enter)
# ═══════════════════════════════════════════════════════════════
class WorldIntroCard:
    def __init__(self):
        self.active=False; self.timer=0; self.world_idx=0

    def trigger(self, world_idx):
        self.active=True; self.timer=90; self.world_idx=world_idx

    def update(self):
        if self.active: self.timer-=1
        if self.timer<=0: self.active=False

    def draw(self, surf):
        if not self.active: return
        t=self.timer/90
        wt=WTHEME(self.world_idx)
        meta=level_meta(self.world_idx)
        # Fade in/out
        if self.timer>75: a=int(255*(90-self.timer)/15)
        elif self.timer<18: a=int(255*self.timer/18)
        else: a=255
        if a<=0: return

        # Dark overlay
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,min(180,a)))
        surf.blit(ov,(0,0))

        # Horizontal accent bars
        bar_h=4
        for by2 in [H//2-62,H//2+52]:
            bs=pygame.Surface((W,bar_h),pygame.SRCALPHA)
            for px2 in range(W):
                ba=int(a*math.sin(px2/W*math.pi))
                bs.fill((*wt[3],ba),(px2,0,1,bar_h))
            surf.blit(bs,(0,by2))

        # World number + name
        num_s=outlined(f"WORLD  {self.world_idx+1:02d}",F_LG,wt[3],(0,0,0),3)
        num_s.set_alpha(a)
        surf.blit(num_s,(W//2-num_s.get_width()//2,H//2-56))

        name_s=outlined(meta["world"].upper(),F_TITLE,
                         lerpC(wt[3],(255,255,255),0.3),(0,0,0),4)
        name_s.set_alpha(a)
        surf.blit(name_s,(W//2-name_s.get_width()//2,H//2-22))

        msg_s=F_SUB.render(meta.get("story") or (MSGS[self.world_idx] if self.world_idx<len(MSGS) else "...")
                            ,True,lerpC(wt[3],(255,255,255),0.6))
        msg_s.set_alpha(a)
        surf.blit(msg_s,(W//2-msg_s.get_width()//2,H//2+76))

intro_card = WorldIntroCard()

# ═══════════════════════════════════════════════════════════════
#  EDGE DANGER INDICATOR  (arrow when enemy is off-screen)
# ═══════════════════════════════════════════════════════════════
def draw_edge_indicators(surf, enemies, tick):
    MARGIN=60
    for en in enemies:
        if not en.alive: continue
        if 0<en.x<W and 0<en.y<H: continue  # on screen
        # Clamp to screen edge
        ex=clamp(int(en.x),MARGIN,W-MARGIN)
        ey=clamp(int(en.y),MARGIN,H-MARGIN)
        # Arrow pointing to enemy
        dx2=en.x-W//2; dy2=en.y-H//2
        angle=math.atan2(dy2,dx2)
        # Draw on the edge
        ax=int(W//2+math.cos(angle)*(min(W,H)*0.44))
        ay=int(H//2+math.sin(angle)*(min(W,H)*0.38))
        ax=clamp(ax,MARGIN,W-MARGIN); ay=clamp(ay,MARGIN,H-MARGIN)
        pulse=(math.sin(tick*0.18)+1)/2
        c=en.color
        a=int(160+pulse*60)
        # Arrow triangle
        sz=10+int(pulse*4)
        pts=[(ax+math.cos(angle)*sz, ay+math.sin(angle)*sz),
             (ax+math.cos(angle+2.4)*sz*0.55, ay+math.sin(angle+2.4)*sz*0.55),
             (ax+math.cos(angle-2.4)*sz*0.55, ay+math.sin(angle-2.4)*sz*0.55)]
        as2=pygame.Surface((sz*4,sz*4),pygame.SRCALPHA)
        adj=[(p[0]-ax+sz*2,p[1]-ay+sz*2) for p in pts]
        pygame.draw.polygon(as2,(*c,a),adj)
        surf.blit(as2,(ax-sz*2,ay-sz*2))
        # Mini enemy dot
        draw_sphere(surf,ax,ay,5,c,tick,shadow=False,pulse_t=pulse*0.3)

# ═══════════════════════════════════════════════════════════════
#  PAUSE MENU
# ═══════════════════════════════════════════════════════════════
def draw_pause(surf, world_idx):
    t=pygame.time.get_ticks()/1000.0
    wt=WTHEME(world_idx)
    ov=pygame.Surface((W,H),pygame.SRCALPHA)
    ov.fill((0,0,0,175))
    surf.blit(ov,(0,0))

    # Vignette
    for ring in range(5,0,-1):
        vc=(*wt[3],int(8*ring))
        vs=pygame.Surface((W,H),pygame.SRCALPHA)
        brd=ring*30
        for r2 in [(0,0,W,brd),(0,H-brd,W,brd),(0,0,brd,H),(W-brd,0,brd,H)]:
            pygame.draw.rect(vs,vc,r2)
        surf.blit(vs,(0,0))

    # Panel
    pw=520; ph=380; ppx=W//2-pw//2; ppy=H//2-ph//2
    panel=pygame.Surface((pw,ph),pygame.SRCALPHA)
    panel.fill((8,8,18,220))
    pygame.draw.rect(panel,(*wt[3],100),(0,0,pw,ph),2,border_radius=18)
    surf.blit(panel,(ppx,ppy))

    # Title
    ps2=outlined("PAUSED",F_XL,wt[3],(0,0,0),3)
    surf.blit(ps2,(W//2-ps2.get_width()//2,ppy+18))

    # World info
    wis=F_MD.render(f"WORLD {world_idx+1:02d}  ·  {wt[6]}",True,
                    lerpC(wt[3],(255,255,255),0.4))
    surf.blit(wis,(W//2-wis.get_width()//2,ppy+92))

    # Buttons
    btns=[]
    btn_data=[
        ("▶  RESUME",    wt[3],          (0,0,0)),
        ("⚙  SETTINGS",  (120,170,255),  (0,0,0)),
        ("↺  RESTART",   (220,100,100),  (0,0,0)),
        ("⌂  MAIN MENU", (150,150,180),  (0,0,0)),
    ]
    for i,(label,fc,tc2) in enumerate(btn_data):
        bw=300; bh=50
        bx2=W//2-bw//2; by2=ppy+134+i*58
        btn_r=pygame.Rect(bx2,by2,bw,bh)
        # Glow
        for ring in range(3,0,-1):
            gs=pygame.Surface((bw+ring*8,bh+ring*6),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*fc,15),(0,0,bw+ring*8,bh+ring*6),border_radius=12)
            surf.blit(gs,(bx2-ring*4,by2-ring*3))
        pygame.draw.rect(surf,lerpC(fc,(0,0,0),0.45),btn_r,border_radius=10)
        pygame.draw.rect(surf,(*fc,150),btn_r,1,border_radius=10)
        hi=pygame.Surface((bw-8,10),pygame.SRCALPHA)
        hi.fill((255,255,255,28))
        surf.blit(hi,(bx2+4,by2+4))
        ls2=outlined(label,F_MD,fc,tc2,2)
        surf.blit(ls2,(W//2-ls2.get_width()//2,by2+bh//2-ls2.get_height()//2))
        btns.append(btn_r)

    # Stats line
    st=F_TAG.render(f"Deaths: {SD['deaths']}  ·  Coins: {SD['coins']}  ·  Runs: {SD['runs']}",
                     True,(120,130,160))
    surf.blit(st,(W//2-st.get_width()//2,ppy+ph-30))

    return btns  # [resume, settings, restart, menu]

# ═══════════════════════════════════════════════════════════════
#  SETTINGS SCREEN  (fully interactive, premium UI)
# ═══════════════════════════════════════════════════════════════
class SettingsScreen:
    TABS = ["GAMEPLAY", "GRAPHICS", "AUDIO", "CONTROLS", "YOUR JOURNEY", "ACCESSIBILITY", "DATA"]

    ROWS = {
        "GAMEPLAY": [
            ("difficulty",      "Difficulty",       "cycle",  ["relaxed","normal","challenge"]),
            ("assist_mode",     "Assist Mode",      "toggle", None),
            ("auto_dash",       "Auto Dash",        "toggle", None),
            ("screen_shake",    "Screen Shake",     "toggle", None),
            ("game_speed",      "Game Speed",       "slider", (50,150)),
            ("checkpoint_assist","Checkpoint Assist","toggle", None),
        ],
        "GRAPHICS": [
            ("fullscreen",      "Fullscreen",       "toggle", None),
            ("resolution",      "Resolution",       "cycle",  ["1280x720", "1600x900", "1920x1080"]),
            ("pixel_art_mode",  "Pixel Art Mode",   "toggle", None),
            ("particle_quality","Particle Quality", "cycle",  ["low","medium","high"]),
            ("lighting_effects","Lighting Effects", "toggle", None),
            ("brightness",      "Brightness",       "slider", (0,100)),
            ("screen_effects",  "Screen Effects",   "toggle", None),
            ("fps_display",     "FPS Display",      "toggle", None),
        ],
        "AUDIO": [
            ("mute_all",        "Mute All",         "toggle", None),
            ("master_volume",   "Master Volume",    "slider", (0,100)),
            ("music_volume",    "Music Volume",     "slider", (0,100)),
            ("sfx_volume",      "Sound Effects",    "slider", (0,100)),
            ("ambient_volume",  "Environment Vol",  "slider", (0,100)),
            ("emotion_music",   "Emotion Music",    "toggle", None),
            ("environment_sounds","Environment Sounds","toggle",None),
        ],
        "CONTROLS": [
            ("key_left",        "Move Left",        "keybind",None),
            ("key_right",       "Move Right",       "keybind",None),
            ("key_jump",        "Jump",             "keybind",None),
            ("key_dash",        "Dash",             "keybind",None),
            ("key_skill",       "Shield",           "keybind",None),
            ("key_ghost",       "Ghost Step",       "keybind",None),
            ("key_ultimate",    "Ultimate",         "keybind",None),
            ("key_pause",       "Pause",            "keybind",None),
            ("key_interact",    "Interact",         "keybind",None),
            ("controller_support","Controller Support","toggle",None),
            ("controller_vibration","Controller Vibrate","toggle",None),
            ("mouse_sensitivity","Mouse Sensitivity","slider",(0,100)),
        ],
        "YOUR JOURNEY": [
            ("emotion_intensity","Emotion Intensity","cycle",["low","medium","high"]),
            ("aura",            "Character Aura",   "cycle",  ["purple_dream","blue_calm","red_courage","green_hope","gold_balance"]),
            ("dash_effect",     "Dash Trail",       "cycle",  ["shadow_trail","star_trail","heart_energy","lightning_trail"]),
            ("focus_mode",      "Focus Mode",       "toggle", None),
            ("dream_mode",      "Dream Mode",       "toggle", None),
            ("color_theme",     "Color Theme",      "cycle",  ["dream_theme","dark_theme","bright_theme","emotional_core"]),
        ],
        "ACCESSIBILITY": [
            ("reduce_motion",   "Reduce Motion",    "toggle", None),
            ("color_blind_mode","Color Blind Mode", "toggle", None),
            ("high_contrast",   "High Contrast",    "toggle", None),
            ("text_size",       "Text Size",        "cycle",  ["small","medium","large"]),
        ],
        "DATA": [
            ("__save_hdr",      "Progress",         "header", None),
            ("__save_progress", "Save Progress",    "button", (100,200,100)),
            ("__load_progress", "Load Progress",    "button", (100,100,250)),
            ("__restore_defaults","Restore Default Settings","button",(180,140,60)),
            ("__save_hdr2",     "Danger Zone",      "header", None),
            ("__reset_progress","Reset All Progress","button",(200,40,40)),
        ],
    }

    AURA_COLS = {
        "purple_dream":  (166,88,255),
        "blue_calm":     (60,160,255),
        "red_courage":   (255,60,60),
        "green_hope":    (50,220,100),
        "gold_balance":  (255,200,50),
    }

    def __init__(self):
        self.selected_tab  = 0
        self.hover_key     = None
        self.capture_key   = None   # key currently being rebound
        self.confirm_reset = False  # show danger confirmation?
        self.reset_hold_time = 0.0
        self.confirm_defaults=False
        self._tick         = 0
        self.scroll        = 0.0
        self.tab_anim      = [0.0]*len(self.TABS)
        self.save_flash    = 0      # frames to show "SAVED" message
        self._drag_key     = None   # slider being dragged
        self._drag_start   = 0
        self._drag_val0    = 0
        # ambient particles for settings bg
        self._particles    = []
        self._spawn_particles()

    # ── helpers ──────────────────────────────────────────────────
    def _spawn_particles(self):
        self._particles=[]
        for _ in range(60):
            self._particles.append({
                "x": random.uniform(0,W),
                "y": random.uniform(0,H),
                "vx": random.uniform(-0.4,0.4),
                "vy": random.uniform(-0.55,-0.08),
                "r":  random.uniform(1.2,4.0),
                "life": random.uniform(0,1),
            })

    def _get_accent(self):
        aura=SETTINGS.get("aura","purple_dream")
        return self.AURA_COLS.get(aura,(166,88,255))

    def _fmt_key(self, raw):
        """Convert pygame key constant to display name."""
        if isinstance(raw,int):
            name=pygame.key.name(raw)
            return name.upper().replace(" ","_")
        return str(raw).upper()

    def _get_val(self,key):
        return SETTINGS.get(key)

    def _set_val(self,key,val):
        SETTINGS.set(key,val)
        self.save_flash=90

    def _cycle(self,key,opts):
        cur=self._get_val(key)
        try: idx=opts.index(cur)
        except ValueError: idx=0
        self._set_val(key, opts[(idx+1)%len(opts)])

    def _cycle_back(self,key,opts):
        cur=self._get_val(key)
        try: idx=opts.index(cur)
        except ValueError: idx=0
        self._set_val(key, opts[(idx-1)%len(opts)])

    def _tab_rows(self):
        return self.ROWS[self.TABS[self.selected_tab]]

    # ── row geometry ─────────────────────────────────────────────
    ROW_H    = 54
    PANEL_X  = 90
    PANEL_W  = W-180
    PANEL_Y  = 158   # top of scrollable area
    PANEL_VH = H-220 # visible height

    def _row_rect(self, i):
        """Rect for row i (in screen coords, accounting for scroll)."""
        y = self.PANEL_Y + int(i*self.ROW_H - self.scroll)
        return pygame.Rect(self.PANEL_X, y, self.PANEL_W, self.ROW_H-4)

    def _widget_rect(self, row_rect):
        """Right-hand widget area inside a row rect."""
        return pygame.Rect(row_rect.right-370, row_rect.y+6, 360, row_rect.height-12)

    # ── slider hit geometry ───────────────────────────────────────
    SLIDER_TRK_W = 260
    def _slider_rect(self, wr):
        return pygame.Rect(wr.x+4, wr.y+wr.height//2-6, self.SLIDER_TRK_W, 12)

    # ── input ────────────────────────────────────────────────────
    def handle_event(self, e):
        """Return True if the event was consumed (don't pass to game)."""
        t=pygame.time.get_ticks()/1000.0
        mx,my=get_scaled_mouse_pos()

        # ── key-capture mode ──
        if self.capture_key is not None:
            if e.type==pygame.KEYDOWN:
                if e.key!=pygame.K_ESCAPE:
                    self._set_val(self.capture_key, e.key)
                self.capture_key=None
            return True

        # ── confirm dialogs ──
        if self.confirm_reset:
            # We don't use this anymore, we use hold_reset_time instead
            self.confirm_reset=False
            return True

        if self.confirm_defaults:
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                cancel_r=pygame.Rect(W//2-160,H//2+50,140,44)
                do_r    =pygame.Rect(W//2+20, H//2+50,140,44)
                if do_r.collidepoint(mx,my):
                    self._do_restore_defaults()
                self.confirm_defaults=False
            return True

        # ── tab clicks ──
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            tab_rects=self._tab_rects()
            for i,tr in enumerate(tab_rects):
                if tr.collidepoint(mx,my):
                    self.selected_tab=i
                    self.scroll=0
                    return True

        # ── slider drag start ──
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            rows=self._tab_rows()
            for i,(key,label,rtype,opts) in enumerate(rows):
                rr=self._row_rect(i)
                if not rr.colliderect((0,self.PANEL_Y,W,self.PANEL_VH)): continue
                wr=self._widget_rect(rr)
                if rtype=="slider" and wr.collidepoint(mx,my):
                    sr=self._slider_rect(wr)
                    self._drag_key=key
                    self._drag_opts=opts
                    self._drag_x0=sr.x
                    self._drag_w=sr.width
                    self._update_slider_from_mouse(mx,sr,opts)
                    return True

        # ── slider drag end ──
        if e.type==pygame.MOUSEBUTTONUP and e.button==1:
            self._drag_key=None
            self.reset_hold_time = 0.0

        # ── slider drag motion ──
        if e.type==pygame.MOUSEMOTION and self._drag_key:
            rows=self._tab_rows()
            for i,(key,label,rtype,opts) in enumerate(rows):
                if key!=self._drag_key: continue
                rr=self._row_rect(i)
                wr=self._widget_rect(rr)
                sr=self._slider_rect(wr)
                self._update_slider_from_mouse(mx,sr,opts)
                return True

        # ── scroll ──
        if e.type==pygame.MOUSEWHEEL:
            self.scroll=max(0.0, self.scroll - e.y*30)
            return True

        # ── row clicks ──
        if e.type==pygame.MOUSEBUTTONDOWN and e.button in (1,3):
            rows=self._tab_rows()
            for i,(key,label,rtype,opts) in enumerate(rows):
                rr=self._row_rect(i)
                if not (self.PANEL_Y<=rr.y<=self.PANEL_Y+self.PANEL_VH): continue
                if not rr.collidepoint(mx,my): continue
                wr=self._widget_rect(rr)
                if rtype=="toggle":
                    cur=self._get_val(key)
                    self._set_val(key, not cur)
                    return True
                if rtype=="cycle":
                    # left arrow or right click = go back
                    cx=wr.x+wr.width//2
                    if e.button==3 or mx<cx:
                        self._cycle_back(key,opts)
                    else:
                        self._cycle(key,opts)
                    return True
                if rtype=="keybind":
                    self.capture_key=key
                    return True
                if rtype=="button":
                    if key=="__reset_progress":
                        self.reset_hold_time = 0.01 # start hold
                    elif key=="__restore_defaults":
                        self.confirm_defaults=True
                    elif key=="__save_progress":
                        save_game(SD)
                        self.save_flash=120
                    elif key=="__load_progress":
                        new_sd = load_save()
                        SD.clear()
                        SD.update(new_sd)
                        self.save_flash=120
                    return True
        return False

    def _update_slider_from_mouse(self, mx, sr, opts):
        lo,hi=opts
        frac=clamp((mx-sr.x)/max(1,sr.width),0.0,1.0)
        val=int(round(lo+(hi-lo)*frac))
        self._set_val(self._drag_key, val)

    def _do_reset(self):
        SD.update({"level":0,"best":0,"deaths":0,"runs":0,"coins":0,
                   "cleared":[False]*TOTAL_LEVELS,"best_times":[0]*TOTAL_LEVELS,
                   "completed_levels":[],"stars":0,"emotions":[],
                   "level_stars":[0]*TOTAL_LEVELS})
        save_game(SD)
        self.save_flash=120

    def _do_restore_defaults(self):
        from src.settings.settings_manager import DEFAULT_SETTINGS
        for k,v in DEFAULT_SETTINGS.items():
            if k != "settings_version":
                SETTINGS.set(k,v)
        self.save_flash=90

    # ── tab rect geometry ─────────────────────────────────────────
    def _tab_rects(self):
        n=len(self.TABS)
        tw=(W-100)//n
        rects=[]
        for i in range(n):
            rects.append(pygame.Rect(50+i*tw, 96, tw-6, 36))
        return rects

    # ── update (call every frame) ─────────────────────────────────
    def update(self):
        self._tick+=1
        
        # Reset hold logic
        if getattr(self, "reset_hold_time", 0) > 0:
            if pygame.mouse.get_pressed()[0]:
                self.reset_hold_time += 1.0/60.0
                if self.reset_hold_time >= 3.0:
                    self._do_reset()
                    self.reset_hold_time = 0.0
            else:
                self.reset_hold_time = 0.0
                
        # animate tab glow
        for i in range(len(self.TABS)):
            target=1.0 if i==self.selected_tab else 0.0
            self._tab_anim_val=getattr(self,"_tab_anim",None)
            self.tab_anim[i]=lerp(self.tab_anim[i],target,0.12)
        # drift particles
        for p in self._particles:
            p["x"]+=p["vx"]; p["y"]+=p["vy"]
            p["life"]=min(1.0,p["life"]+0.007)
            if p["y"]<-8:
                p["y"]=H+4; p["x"]=random.uniform(0,W); p["life"]=0.0
        if self.save_flash>0: self.save_flash-=1

    # ── draw ─────────────────────────────────────────────────────
    def draw(self, surf):
        self.update()
        t=self._tick*0.016
        accent=self._get_accent()
        mx,my=get_scaled_mouse_pos()

        # ── background gradient ──
        aura=SETTINGS.get("aura","purple_dream")
        bg_tops={"purple_dream":(14,4,28),"blue_calm":(4,12,28),
                 "red_courage":(22,4,4),"green_hope":(4,18,8),"gold_balance":(22,16,4)}
        bg_bots={"purple_dream":(4,2,12),"blue_calm":(2,4,14),
                 "red_courage":(10,2,2),"green_hope":(2,8,4),"gold_balance":(10,8,2)}
        top=bg_tops.get(aura,(14,4,28))
        bot=bg_bots.get(aura,(4,2,12))
        for y in range(0,H,2):
            surf.fill(lerpC(top,bot,y/H),(0,y,W,2))

        # ── ambient particles ──
        intensity=SETTINGS.get("emotion_intensity","medium")
        pc=18 if intensity=="low" else (35 if intensity=="medium" else 55)
        for p in self._particles[:pc]:
            a=int(clamp(p["life"]*180,0,180))
            circ(surf,accent,(p["x"],p["y"]),p["r"],a)

        # soft glow behind title
        for ring in range(5,0,-1):
            gs=pygame.Surface((500,80),pygame.SRCALPHA)
            pygame.draw.ellipse(gs,(*accent,ring*8),(0,0,500,80))
            surf.blit(gs,(W//2-250,22))

        # ── title ──
        title=outlined("EMOTIONAL SETTINGS",F_XL,accent,(0,0,0),3)
        surf.blit(title,(W//2-title.get_width()//2,28))

        # ── tabs ──
        tab_rects=self._tab_rects()
        for i,(tab,tr) in enumerate(zip(self.TABS,tab_rects)):
            hov=tr.collidepoint(mx,my)
            sel=i==self.selected_tab
            glow=self.tab_anim[i]
            # glow halo
            if glow>0.05:
                gs=pygame.Surface((tr.w+12,tr.h+12),pygame.SRCALPHA)
                pygame.draw.rect(gs,(*accent,int(glow*80)),(0,0,tr.w+12,tr.h+12),border_radius=10)
                surf.blit(gs,(tr.x-6,tr.y-6))
            fill=lerpC(lerpC((20,16,40),accent,glow*0.35),accent,0.2 if hov else 0)
            pygame.draw.rect(surf,fill,tr,border_radius=8)
            bord=(*lerpC(accent,(255,255,255),glow*0.5),int(80+glow*175))
            pygame.draw.rect(surf,bord,tr,1+(1 if sel else 0),border_radius=8)
            lc=lerpC((160,155,200),(255,255,255),glow*0.8+(0.2 if hov else 0))
            ts=F_SM.render(tab,True,lc)
            surf.blit(ts,(tr.x+tr.w//2-ts.get_width()//2,tr.y+tr.h//2-ts.get_height()//2))

        # ── panel bg ──
        panel=pygame.Surface((self.PANEL_W+2,self.PANEL_VH+2),pygame.SRCALPHA)
        panel.fill((5,6,18,210))
        pygame.draw.rect(panel,(*accent,70),(0,0,self.PANEL_W+2,self.PANEL_VH+2),1,border_radius=12)
        surf.blit(panel,(self.PANEL_X-1,self.PANEL_Y-1))

        # ── clip drawing to panel area ──
        clip=pygame.Rect(self.PANEL_X,self.PANEL_Y,self.PANEL_W,self.PANEL_VH)
        surf.set_clip(clip)

        rows=self._tab_rows()
        max_scroll=max(0.0,len(rows)*self.ROW_H-self.PANEL_VH+8)
        self.scroll=clamp(self.scroll,0.0,max_scroll)

        for i,(key,label,rtype,opts) in enumerate(rows):
            rr=self._row_rect(i)
            if rr.bottom<self.PANEL_Y or rr.top>self.PANEL_Y+self.PANEL_VH: continue

            hov=rr.collidepoint(mx,my) and clip.collidepoint(mx,my)
            if key==self.hover_key and not hov: self.hover_key=None
            if hov: self.hover_key=key

            # ── header row ──
            if rtype=="header":
                hy=rr.y+rr.height//2
                pygame.draw.line(surf,(*accent,55),(self.PANEL_X+12,hy),(self.PANEL_X+self.PANEL_W-12,hy),1)
                hs=F_SM.render(label.upper(),True,lerpC(accent,(255,255,255),0.5))
                surf.blit(hs,(self.PANEL_X+self.PANEL_W//2-hs.get_width()//2,rr.y+8))
                continue

            # row background
            if hov:
                rb=pygame.Surface((rr.w,rr.h),pygame.SRCALPHA)
                rb.fill((*accent,22))
                surf.blit(rb,(rr.x,rr.y))
                pygame.draw.rect(surf,(*accent,80),rr,1,border_radius=8)

            # label
            lc2=(210,215,240) if not hov else (255,255,255)
            ls=F_SM.render(label,True,lc2)
            surf.blit(ls,(rr.x+20,rr.y+rr.height//2-ls.get_height()//2))

            wr=self._widget_rect(rr)

            # ── TOGGLE ──
            if rtype=="toggle":
                val=self._get_val(key)
                on_c=accent if val else (80,80,100)
                pill_w,pill_h=76,30
                px=wr.right-pill_w; py=wr.y+wr.height//2-pill_h//2
                pill_r=pygame.Rect(px,py,pill_w,pill_h)
                # glow
                if val:
                    gs=pygame.Surface((pill_w+8,pill_h+8),pygame.SRCALPHA)
                    pygame.draw.rect(gs,(*on_c,50),(0,0,pill_w+8,pill_h+8),border_radius=pill_h)
                    surf.blit(gs,(px-4,py-4))
                pygame.draw.rect(surf,lerpC(on_c,(0,0,0),0.45),pill_r,border_radius=pill_h)
                pygame.draw.rect(surf,(*on_c,180),pill_r,2,border_radius=pill_h)
                knob_x=px+pill_w-16 if val else px+10
                pygame.draw.circle(surf,(255,255,255),(knob_x,py+pill_h//2),10)
                ts2=F_TINY.render("ON" if val else "OFF",True,(255,255,255) if val else (120,120,150))
                ox=px+12 if val else px+28
                surf.blit(ts2,(ox,py+pill_h//2-ts2.get_height()//2))

            # ── CYCLE ──
            elif rtype=="cycle":
                val=self._get_val(key)
                if val is None: val=opts[0]
                disp=str(val).replace("_"," ").upper()
                bw=240; bh=30
                bx=wr.right-bw; by=wr.y+wr.height//2-bh//2
                # left arrow
                la=F_MD.render("◀",True,lerpC((80,80,120),accent,0.7))
                surf.blit(la,(bx+4,by+bh//2-la.get_height()//2))
                # right arrow
                ra=F_MD.render("▶",True,lerpC((80,80,120),accent,0.7))
                surf.blit(ra,(bx+bw-ra.get_width()-4,by+bh//2-ra.get_height()//2))
                # value bg
                vr=pygame.Rect(bx+30,by,bw-60,bh)
                pygame.draw.rect(surf,lerpC(accent,(0,0,0),0.55),vr,border_radius=6)
                pygame.draw.rect(surf,(*accent,120),vr,1,border_radius=6)
                vs=F_SM.render(disp,True,(255,255,255))
                surf.blit(vs,(vr.x+vr.w//2-vs.get_width()//2,vr.y+vr.h//2-vs.get_height()//2))

            # ── SLIDER ──
            elif rtype=="slider":
                lo,hi=opts
                val=self._get_val(key)
                if val is None: val=lo
                val=clamp(int(val),lo,hi)
                frac=(val-lo)/max(1,hi-lo)
                sr=self._slider_rect(wr)
                # track
                pygame.draw.rect(surf,(40,38,60),sr,border_radius=6)
                # filled portion
                fw=int(sr.width*frac)
                if fw>0:
                    fr=pygame.Rect(sr.x,sr.y,fw,sr.height)
                    pygame.draw.rect(surf,lerpC(accent,(255,255,255),0.15),fr,border_radius=6)
                # knob
                kx=sr.x+fw
                pygame.draw.circle(surf,(255,255,255),(kx,sr.y+sr.height//2),10)
                pygame.draw.circle(surf,accent,(kx,sr.y+sr.height//2),8)
                # value label
                vs=F_TINY.render(str(val),True,(200,200,220))
                surf.blit(vs,(sr.right+14,sr.y+sr.height//2-vs.get_height()//2))

            # ── KEYBIND ──
            elif rtype=="keybind":
                capturing=self.capture_key==key
                val=self._get_val(key)
                disp="PRESS KEY…" if capturing else self._fmt_key(val)
                chip_c=(200,40,40) if capturing else accent
                cw=160; ch=30
                cx2=wr.right-cw; cy2=wr.y+wr.height//2-ch//2
                chip_r=pygame.Rect(cx2,cy2,cw,ch)
                if capturing:
                    pulse=(math.sin(self._tick*0.18)+1)/2
                    pc2=lerpC((200,40,40),(255,80,80),pulse)
                    pygame.draw.rect(surf,pc2,chip_r,border_radius=6)
                else:
                    pygame.draw.rect(surf,lerpC(accent,(0,0,0),0.55),chip_r,border_radius=6)
                    pygame.draw.rect(surf,(*accent,140),chip_r,1,border_radius=6)
                cs=F_SM.render(disp,True,(255,255,255))
                surf.blit(cs,(chip_r.x+chip_r.w//2-cs.get_width()//2,
                              chip_r.y+chip_r.h//2-cs.get_height()//2))

            # ── ACTION BUTTON ──
            elif rtype=="button":
                btn_c=opts if opts else accent
                bw=260; bh=34
                bx2=wr.right-bw; by2=wr.y+wr.height//2-bh//2
                br=pygame.Rect(bx2,by2,bw,bh)
                hov_btn=br.collidepoint(mx,my) and clip.collidepoint(mx,my)
                fc=lerpC(btn_c,(0,0,0),0.4 if not hov_btn else 0.2)
                pygame.draw.rect(surf,fc,br,border_radius=8)
                
                # Hold to reset progress bar
                if key=="__reset_progress" and getattr(self, "reset_hold_time", 0) > 0:
                    prog = self.reset_hold_time / 3.0
                    fill_w = int(bw * prog)
                    if fill_w > 0:
                        fill_r = pygame.Rect(br.x, br.y, fill_w, br.height)
                        pygame.draw.rect(surf, (255,100,100), fill_r, border_radius=8)
                        
                pygame.draw.rect(surf,(*btn_c,160),br,2,border_radius=8)
                
                label_disp = label
                if key=="__reset_progress" and getattr(self, "reset_hold_time", 0) > 0:
                    label_disp = "HOLD TO RESET..."
                
                bs=F_SM.render(label_disp,True,(255,255,255))
                surf.blit(bs,(br.x+br.w//2-bs.get_width()//2,br.y+br.h//2-bs.get_height()//2))

        surf.set_clip(None)
        
        # ── EMOTIONAL PREVIEW ──
        if self.TABS[self.selected_tab] in ["YOUR JOURNEY", "ACCESSIBILITY"]:
            cx, cy = W - 180, H - 180
            
            # Glow Aura
            for ring in range(3, 0, -1):
                a_surf = pygame.Surface((120+ring*30, 120+ring*30), pygame.SRCALPHA)
                pygame.draw.circle(a_surf, (*accent, 20), (60+ring*15, 60+ring*15), 60+ring*15)
                surf.blit(a_surf, (cx - 60 - ring*15, cy - 60 - ring*15))
                
            # Mock Player Square
            pr = pygame.Rect(cx-30, cy-30, 60, 60)
            pygame.draw.rect(surf, (255,255,255), pr, border_radius=12)
            pygame.draw.rect(surf, (200,200,200), pr, 2, border_radius=12)
            
            # Trail text
            trail_type = SETTINGS.get("dash_effect", "shadow_trail")
            ts = F_SM.render(trail_type.replace("_", " ").upper(), True, accent)
            surf.blit(ts, (cx - ts.get_width()//2, cy + 50))
            
            # Focus Mode text
            if SETTINGS.get("focus_mode"):
                fs = F_TINY.render("FOCUS MODE ON", True, (255,200,100))
                surf.blit(fs, (cx - fs.get_width()//2, cy + 75))

        # ── scroll indicator ──
        if max_scroll>0:
            bar_h=int(self.PANEL_VH*(self.PANEL_VH/(len(rows)*self.ROW_H+1)))
            bar_y=self.PANEL_Y+int((self.PANEL_VH-bar_h)*(self.scroll/max_scroll))
            pygame.draw.rect(surf,(*accent,90),(self.PANEL_X+self.PANEL_W+4,bar_y,4,bar_h),border_radius=2)

        # ── BACK button ──
        back=pygame.Rect(W//2-110,H-56,220,42)
        hbk=back.collidepoint(mx,my)
        pygame.draw.rect(surf,lerpC(accent,(0,0,0),0.45 if not hbk else 0.25),back,border_radius=10)
        pygame.draw.rect(surf,(*accent,180),back,2,border_radius=10)
        bks=F_MD.render("◀  BACK",True,(255,255,255))
        surf.blit(bks,(back.centerx-bks.get_width()//2,back.centery-bks.get_height()//2))

        # ── SAVED flash ──
        if self.save_flash>0:
            a=int(255*min(1.0,self.save_flash/30))
            sfs=F_SM.render("✓  SETTINGS SAVED",True,(*accent,255))
            sfs.set_alpha(a)
            surf.blit(sfs,(W-sfs.get_width()-24,H-36))

        # ── DATA tab stats ──
        if self.TABS[self.selected_tab]=="DATA":
            stats=[
                f"Levels Cleared:  {sum(1 for x in SD['cleared'] if x)} / {TOTAL_LEVELS}",
                f"Stars:           {SD.get('stars',0)} / {TOTAL_LEVELS*3}",
                f"Emotions Found:  {len(SD.get('emotions',[]))} / 10",
                f"Total Deaths:    {SD.get('deaths',0)}",
                f"Total Coins:     {SD.get('coins',0)}",
                f"Total Runs:      {SD.get('runs',0)}",
            ]
            sy=self.PANEL_Y+14
            for s in stats:
                ss=F_SM.render(s,True,(180,185,220))
                surf.blit(ss,(self.PANEL_X+20,sy))
                sy+=26

        # ── confirmation popups ──
        if self.confirm_reset:
            self._draw_confirm(surf,
                "⚠  RESET ALL PROGRESS?",
                ["You are about to permanently delete:",
                 " ✓  Completed Levels",
                 " ✓  Stars & Coins",
                 " ✓  Emotional Progress",
                 " ✓  Skill Unlocks"],
                "CANCEL","RESET",
                cancel_c=(60,60,90), do_c=(180,30,30))

        if self.confirm_defaults:
            self._draw_confirm(surf,
                "⚠  RESTORE DEFAULT SETTINGS?",
                ["Audio, Graphics, Controls and",
                 "Gameplay will be reset.",
                 "",
                 "Your save progress is NOT affected."],
                "CANCEL","RESTORE",
                cancel_c=(60,60,90), do_c=(120,90,20))

        return back

    def _draw_confirm(self, surf, title, lines, cancel_lbl, do_lbl, cancel_c, do_c):
        # dim overlay
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,160))
        surf.blit(ov,(0,0))
        # panel
        pw,ph=520,300
        px,py=W//2-pw//2,H//2-ph//2
        panel=pygame.Surface((pw,ph),pygame.SRCALPHA)
        panel.fill((10,8,24,240))
        pygame.draw.rect(panel,(200,60,60,160),(0,0,pw,ph),2,border_radius=14)
        surf.blit(panel,(px,py))
        # title
        ts=F_MD.render(title,True,(255,80,80))
        surf.blit(ts,(W//2-ts.get_width()//2,py+18))
        # lines
        for i,ln in enumerate(lines):
            ls=F_SM.render(ln,True,(200,195,230))
            surf.blit(ls,(W//2-ls.get_width()//2,py+60+i*28))
        # buttons
        cancel_r=pygame.Rect(W//2-160,py+ph-58,140,42)
        do_r    =pygame.Rect(W//2+20, py+ph-58,140,42)
        pygame.draw.rect(surf,cancel_c,cancel_r,border_radius=8)
        pygame.draw.rect(surf,do_c,    do_r,    border_radius=8)
        pygame.draw.rect(surf,(180,180,200),cancel_r,1,border_radius=8)
        pygame.draw.rect(surf,(255,80,80),  do_r,    1,border_radius=8)
        cls2=F_MD.render(cancel_lbl,True,(220,220,240))
        dos=F_MD.render(do_lbl,    True,(255,200,200))
        surf.blit(cls2,(cancel_r.centerx-cls2.get_width()//2,cancel_r.centery-cls2.get_height()//2))
        surf.blit(dos, (do_r.centerx-dos.get_width()//2,    do_r.centery-dos.get_height()//2))


# ── instantiate global settings screen ───────────────────────────
settings_screen = SettingsScreen()


def cycle_setting(key, values):
    cur=SETTINGS.get(key)
    idx=values.index(cur) if cur in values else 0
    SETTINGS.set(key, values[(idx+1)%len(values)])

# ═══════════════════════════════════════════════════════════════
#  WORLD PROGRESS RING  (shown on menu)
#  WORLD PROGRESS RING  (shown on menu, 20 segments)
# ═══════════════════════════════════════════════════════════════
def draw_progress_ring(surf, cx, cy, r_out, r_in, tick):
    n=TOTAL_LEVELS
    for i in range(n):
        a1=i*(math.tau/n)-math.tau/4
        a2=(i+0.88)*(math.tau/n)-math.tau/4
        cleared=SD["cleared"][i] if i<len(SD["cleared"]) else False
        current=i==SD["level"]
        if cleared:
            c=hsv((i/n+tick*0.003)%1,0.8,1.0)
        elif current:
            c=lerpC((255,255,255),(200,200,100),(math.sin(tick*0.12)+1)/2)
        else:
            c=(45,45,62)
        # Draw arc as polygon
        pts=[]
        steps=8
        for j in range(steps+1):
            ang=lerp(a1,a2,j/steps)
            pts.append((cx+math.cos(ang)*r_out,cy+math.sin(ang)*r_out))
        for j in range(steps,-1,-1):
            ang=lerp(a1,a2,j/steps)
            pts.append((cx+math.cos(ang)*r_in,cy+math.sin(ang)*r_in))
        if len(pts)>=3:
            try: pygame.draw.polygon(surf,c,[(int(p[0]),int(p[1])) for p in pts])
            except: pass
        # Number label at midpoint
        mid_a=(a1+a2)/2
        lx=int(cx+math.cos(mid_a)*(r_out+r_in)/2)
        ly=int(cy+math.sin(mid_a)*(r_out+r_in)/2)
        lc=(255,255,255) if (cleared or current) else (70,70,90)
        nr=F_XS.render(str(i+1),True,lc)
        surf.blit(nr,(lx-nr.get_width()//2,ly-nr.get_height()//2))

# ═══════════════════════════════════════════════════════════════
#  SCREENS — Menu / Game Over / Win
# ═══════════════════════════════════════════════════════════════
def draw_menu(surf, idx, tick):
    t=pygame.time.get_ticks()/1000.0
    # Deep space bg
    for y in range(0,H,1):
        pygame.draw.rect(surf,lerpC((2,0,8),(9,2,26),y/H),(0,y,W,1))
    # Galaxy swirls
    for i in range(5):
        a=t*0.06+i*(math.tau/5)
        gx=W//2+math.cos(a)*(258+i*42); gy=H//2+math.sin(a*0.7)*158
        gr=int(88+math.sin(t*0.18+i)*28)
        gc=(*hsv((t*0.03+i*0.2)%1,0.65,0.44),13)
        gs=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,gc,(0,0,gr*2,int(gr*0.8)*2))
        surf.blit(gs,(int(gx-gr),int(gy-gr*0.8)))
    # Shooting stars
    for i in range(3):
        sx=(t*188*(i+1)*0.7)%(W+200)-100; sy=75+i*114; slen=63+i*22
        sa2=int(175*abs(math.sin(t*0.5+i)))
        sl=pygame.Surface((slen,3),pygame.SRCALPHA)
        for px2 in range(slen): sl.fill((255,255,220,int(sa2*(1-px2/slen))),(px2,0,1,3))
        surf.blit(sl,(int(sx),int(sy)))
    # Big halo
    for ring in range(8,0,-1):
        gls=pygame.Surface((W,260),pygame.SRCALPHA)
        hc=(*hsv((t*0.035)%1,0.9,1.0),ring*7)
        pygame.draw.ellipse(gls,hc,(W//2-418,10,836,240))
        surf.blit(gls,(0,40))
    # Title
    lc=hsv((t*0.04)%1,0.8,1.0)
    e_out=outlined("EMOTION",F_GIANT,hsv((t*0.04)%1,1.0,1.0),(0,0,0),4)
    surf.blit(e_out,(W//2-e_out.get_width()//2,58))
    a_out=outlined("ARCHITECT",F_TITLE,hsv((t*0.04+0.15)%1,1.0,1.0),(0,0,0),4)
    surf.blit(a_out,(W//2-a_out.get_width()//2,188))
    # Diamond row
    for i in range(11):
        dx2=W//2-100+i*20; dy2=308; sz=5 if i==5 else 3
        dc=hsv((t*0.05+i*0.09)%1,0.9,1.0)
        pygame.draw.polygon(surf,dc,[(dx2,dy2-sz),(dx2+sz,dy2),(dx2,dy2+sz),(dx2-sz,dy2)])
    # Edition badge
    bs=pygame.Surface((580,34),pygame.SRCALPHA); bs.fill((255,255,255,7))
    pygame.draw.rect(bs,(255,255,255,36),(0,0,580,34),1,border_radius=4)
    surf.blit(bs,(W//2-290,314))
    st=F_SUB.render("✦  U L T I M A T E   E D I T I O N   v5.0  ✦",True,hsv((t*0.04+0.35)%1,0.5,1.0))
    surf.blit(st,(W//2-st.get_width()//2,318))

    # World progress ring
    draw_progress_ring(surf, W//2, H//2+88, 52, 36, tick)
    cleared=sum(1 for x in SD["cleared"] if x)
    cr=F_SM.render(f"{cleared}/{TOTAL_LEVELS} CLEARED",True,(180,180,220))
    surf.blit(cr,(W//2-cr.get_width()//2,H//2+148))

    # Stats panel
    pw2,ph2=700,82; ppx2=W//2-pw2//2; ppy2=358
    panel2=pygame.Surface((pw2,ph2),pygame.SRCALPHA); panel2.fill((255,255,255,5))
    pygame.draw.rect(panel2,(*hsv((t*0.04)%1,0.7,0.9),72),(0,0,pw2,ph2),2,border_radius=10)
    surf.blit(panel2,(ppx2,ppy2))
    stats=[(f"⬡ WORLD {idx+1:03d}/{TOTAL_LEVELS}",(140,255,180)),(f"★ BEST W{SD['best']+1}",(255,220,100)),
           (f"✦ DEATHS {SD['deaths']}",(255,110,110)),(f"◆ COINS {SD['coins']}",(255,200,60))]
    cw2=pw2//4
    for i2,(lb2,col2) in enumerate(stats):
        r2=F_TAG.render(lb2,True,col2); surf.blit(r2,(ppx2+cw2*i2+cw2//2-r2.get_width()//2,ppy2+14))
    rt2=F_TAG.render(f"RUNS:{SD['runs']}  ·  DOUBLE JUMP  ·  DASH  ·  COIN MAGNET  ·  WEATHER SYSTEM",True,(92,112,150))
    surf.blit(rt2,(W//2-rt2.get_width()//2,ppy2+54))

    # Play button
    btn=pygame.Rect(W//2-162,468,324,58)
    btn_set=pygame.Rect(W//2-122,538,244,38)
    for ring in range(6,0,-1):
        gs2=pygame.Surface((btn.w+ring*14,btn.h+ring*10),pygame.SRCALPHA)
        pygame.draw.rect(gs2,(*hsv((t*0.07)%1,0.9,1.0),18),(0,0,btn.w+ring*14,btn.h+ring*10),border_radius=18)
        surf.blit(gs2,(btn.x-ring*7,btn.y-ring*5))
    pygame.draw.rect(surf,hsv((t*0.07)%1,0.8,0.92),btn,border_radius=14)
    hi=pygame.Surface((btn.w-8,12),pygame.SRCALPHA); hi.fill((255,255,255,44))
    surf.blit(hi,(btn.x+4,btn.y+4))
    pygame.draw.rect(surf,(255,255,255),btn,2,border_radius=14)
    pl=outlined("▶   TRANSCEND NOW",F_LG,(10,10,10),(255,255,255),2)
    surf.blit(pl,(btn.centerx-pl.get_width()//2,btn.centery-pl.get_height()//2))
    pygame.draw.rect(surf,(16,26,58),btn_set,border_radius=8)
    pygame.draw.rect(surf,(78,112,185),btn_set,1,border_radius=8)
    sl=F_SUB.render("⚙  EMOTIONAL SETTINGS",True,(140,175,255))
    surf.blit(sl,(btn_set.centerx-sl.get_width()//2,btn_set.centery-sl.get_height()//2))
    # Bottom line
    ls2=pygame.Surface((W,2),pygame.SRCALPHA)
    for px2 in range(W): ls2.fill((*lc,int(200*math.sin(px2/W*math.pi))),(px2,0,1,2))
    surf.blit(ls2,(0,H-52))
    tg=F_TAG.render(f"{TOTAL_LEVELS} WORLDS · EMOTION JOURNEY · SETTINGS · WEATHER · WORLD THEMES",True,(72,50,50))
    surf.blit(tg,(W//2-tg.get_width()//2,H-24))
    return btn, btn_set

def draw_gameover(surf, death_world=0):
    t=pygame.time.get_ticks()/1000.0
    pulse=(math.sin(t*2.2)+1)/2
    wt=WTHEME(death_world)
    for y in range(0,H,1):
        pygame.draw.rect(surf,lerpC((20,0,0),(62,5,5),y/H),(0,y,W,1))
    for i in range(6):
        ex2=W//7*i+int(math.sin(t*0.8+i)*80); ey2=H-int((t*42*(i*0.4+0.6))%H)
        er2=int(3+math.sin(t+i)*2)
        gs=pygame.Surface((er2*6,er2*6),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*hsv((0.04+i*0.01)%1,0.9,1.0),115),(er2*3,er2*3),er2*3)
        surf.blit(gs,(ex2-er2*3,ey2-er2*3))
    for ring in range(5,0,-1):
        vc=(*lerpC((180,0,0),(255,40,0),pulse),int(12*ring))
        vs=pygame.Surface((W,H),pygame.SRCALPHA); brd=ring*28
        for rct in [(0,0,W,brd),(0,H-brd,W,brd),(0,0,brd,H),(W-brd,0,brd,H)]:
            pygame.draw.rect(vs,vc,rct)
        surf.blit(vs,(0,0))
    for i in range(8):
        a2=i*(math.tau/8)+t*0.04; ln=162+math.sin(t*0.5+i)*42
        c2=lerpC((100,0,0),(200,30,0),pulse)
        pygame.draw.line(surf,c2,(W//2,H//2+28),
            (int(W//2+math.cos(a2)*ln),int(H//2+28+math.sin(a2)*ln*0.6)),1)
    gt="GAME OVER"
    for ox2,oy2 in [(6,6),(4,4),(2,2)]:
        sh=F_TITLE.render(gt,True,(55,0,0)); surf.blit(sh,(W//2-sh.get_width()//2+ox2,108+oy2))
    g_top=lerpC((255,55,55),(255,125,0),pulse); g_bot=lerpC((180,0,0),(220,42,0),pulse)
    go_surf=grad_text(gt,F_TITLE,g_top,g_bot); surf.blit(go_surf,(W//2-go_surf.get_width()//2,108))
    for px2 in range(W):
        a2=int(180*math.sin(px2/W*math.pi)); dc2=lerpC((200,30,0),(255,80,0),pulse)
        pygame.draw.rect(surf,(*dc2,a2),(px2,244,1,2))
    mp=pygame.Surface((720,140),pygame.SRCALPHA); mp.fill((0,0,0,58))
    pygame.draw.rect(mp,(180,20,20,48),(0,0,720,140),1,border_radius=8); surf.blit(mp,(W//2-360,257))
    for i2,(msg2,col2,fnt2) in enumerate([
        (f"You fell in World {death_world+1} — {wt[6]}.",(238,148,148),F_MD),
        ("All lives lost. But your progress remains.",(200,188,88),F_SM),
        (f"World {death_world+1} awaits your return.",(220,155,98),F_SM),
        (f"Total deaths: {SD['deaths']}",(158,78,78),F_SUB)]):
        r2=fnt2.render(msg2,True,col2); rs2=fnt2.render(msg2,True,(0,0,0))
        surf.blit(rs2,(W//2-r2.get_width()//2+2,266+i2*28+2)); surf.blit(r2,(W//2-r2.get_width()//2,266+i2*28))
    btn=pygame.Rect(W//2-188,432,376,66)
    for ring in range(5,0,-1):
        gs2=pygame.Surface((btn.w+ring*12,btn.h+ring*10),pygame.SRCALPHA)
        pygame.draw.rect(gs2,(200,30,30,17),(0,0,btn.w+ring*12,btn.h+ring*10),border_radius=18)
        surf.blit(gs2,(btn.x-ring*6,btn.y-ring*5))
    for by2 in range(btn.h):
        pygame.draw.rect(surf,lerpC(lerpC((160,20,20),(200,42,42),pulse),lerpC((100,10,10),(140,25,25),pulse),by2/btn.h),(btn.x,btn.y+by2,btn.w,1))
    pygame.draw.rect(surf,lerpC((255,60,60),(255,120,60),pulse),btn,2,border_radius=14)
    hi2=pygame.Surface((btn.w-10,10),pygame.SRCALPHA); hi2.fill((255,100,100,33)); surf.blit(hi2,(btn.x+5,btn.y+5))
    bl2=outlined(f"↺   RETRY  WORLD  {death_world+1}",F_LG,lerpC((255,200,200),(255,240,220),pulse),(80,0,0),2)
    surf.blit(bl2,(btn.centerx-bl2.get_width()//2,btn.centery-bl2.get_height()//2))
    # Settings button
    btn_set=pygame.Rect(W//2-188,514,376,48)
    pygame.draw.rect(surf,(28,28,50),btn_set,border_radius=12)
    pygame.draw.rect(surf,(90,90,140),btn_set,2,border_radius=12)
    sl=F_MD.render("⚙  SETTINGS",True,(180,185,230))
    surf.blit(sl,(btn_set.centerx-sl.get_width()//2,btn_set.centery-sl.get_height()//2))
    wn2=F_TAG.render(f"⚠  YOUR PROGRESS IS SAFE  ·  RESPAWNING ON WORLD {death_world+1}  ⚠",True,(118,110,40))
    surf.blit(wn2,(W//2-wn2.get_width()//2,H-26))
    return btn, btn_set

def draw_level_complete(surf, level_idx, time_elapsed, stars=3):
    t=pygame.time.get_ticks()/1000.0
    meta=level_meta(level_idx)
    wt=WTHEME(level_idx)
    for y in range(H):
        surf.fill(lerpC(wt[0],wt[1],y/H),(0,y,W,1))
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,105)); surf.blit(ov,(0,0))
    for i in range(18):
        x=int((i*73+t*38)%W); y=int(90+math.sin(t+i)*220+i*17)%H
        circ(surf,wt[5],(x,y),2+i%4,120)
    title=outlined("LEVEL COMPLETE",F_XL,wt[3],(0,0,0),4)
    surf.blit(title,(W//2-title.get_width()//2,92))
    draw_text(surf,f"WORLD {level_idx+1:03d}/{TOTAL_LEVELS} · {meta['world']}",
              (W//2,178),(230,235,255),F_MD,center=True)
    draw_text(surf,f"Emotion discovered: {meta['emotion'].upper()}",
              (W//2,236),wt[3],F_LG,center=True)
    event=WorldEventSystem(meta)
    if event.has_major_challenge:
        draw_text(surf,event.challenge_name,(W//2,282),(255,180,110),F_MD,center=True)
    star_str="★"*stars + "☆"*(3-stars)
    draw_text(surf,f"Stars: {star_str}",(W//2,322),(255,220,90),F_MD,center=True)
    draw_text(surf,f"Memory unlocked: {meta['story']}",
              (W//2,376),(210,215,240),F_SUB,center=True)
    ts=int(time_elapsed); draw_text(surf,f"Time: {ts//60:02d}:{ts%60:02d}",
              (W//2,426),(170,185,220),F_SUB,center=True)
    btn=pygame.Rect(W//2-145,500,290,58)
    pygame.draw.rect(surf,lerpC(wt[3],(0,0,0),0.35),btn,border_radius=14)
    pygame.draw.rect(surf,(255,255,255),btn,2,border_radius=14)
    draw_text(surf,"CONTINUE",(btn.centerx,btn.y+15),(15,15,25),F_MD,center=True)
    return btn

def draw_win(surf):
    t=pygame.time.get_ticks()/1000.0
    pulse=(math.sin(t*1.8)+1)/2
    for y in range(0,H,1):
        pygame.draw.rect(surf,lerpC((2,2,14),(10,5,40),y/H),(0,y,W,1))
    cx2,cy2=W//2,H//2-20
    for i in range(24):
        a2=i*(math.tau/24)+t*0.08; ln2=288+math.sin(t*0.4+i*0.5)*64
        rs2=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.line(rs2,(*hsv((t*0.04+i/24)%1,0.7,0.6),17),(cx2,cy2),(int(cx2+math.cos(a2)*ln2),int(cy2+math.sin(a2)*ln2)),2)
        surf.blit(rs2,(0,0))
    for ring in range(4):
        rr2=int((t*64+ring*84)%328); ra2=max(0,int(180*(1-rr2/328)))
        rs3=pygame.Surface((rr2*2+4,rr2*2+4),pygame.SRCALPHA)
        pygame.draw.circle(rs3,(*hsv((t*0.06+ring*0.12)%1,0.9,1.0),ra2),(rr2+2,rr2+2),rr2,3)
        surf.blit(rs3,(cx2-rr2-2,cy2-rr2-2))
    for i in range(16):
        fx=(W//17*i+int(t*34*(i%3+1)))%W; fy=int(t*60*(i*0.3+0.5)+i*44)%H
        rot2=t*2+i; sz2=6+i%4; fc2=hsv((i/16+t*0.05)%1,0.9,1.0)
        pts2=[(fx+sz2*math.cos(rot2+k*math.tau/4),fy+sz2*math.sin(rot2+k*math.tau/4)) for k in range(4)]
        if len(pts2)>=3: pygame.draw.polygon(surf,fc2,pts2)
    tt2="TRANSCENDED"
    for ring in range(9,0,-1):
        gls2=pygame.Surface((W,220),pygame.SRCALPHA)
        pygame.draw.ellipse(gls2,(*hsv((t*0.05+ring*0.04)%1,0.9,1.0),ring*8),(W//2-500,5,1000,210))
        surf.blit(gls2,(0,60))
    for ox2,oy2 in [(8,8),(5,5),(3,3)]:
        sh2=F_TITLE.render(tt2,True,(18,10,58)); surf.blit(sh2,(W//2-sh2.get_width()//2+ox2,88+oy2))
    ws2=grad_text(tt2,F_TITLE,lerpC((255,220,50),(255,255,200),pulse),lerpC((200,140,0),(255,200,80),pulse))
    surf.blit(ws2,(W//2-ws2.get_width()//2,88))
    sm2=F_TITLE.render(tt2,True,(255,255,255)); sm2.set_alpha(int(28*pulse)); surf.blit(sm2,(W//2-sm2.get_width()//2,87))
    for px2 in range(W):
        a2=int(200*math.sin(px2/W*math.pi)); dc3=lerpC((200,160,0),(255,220,80),pulse)
        pygame.draw.rect(surf,(*dc3,a2),(px2,234,1,2))
    ap2=pygame.Surface((780,144),pygame.SRCALPHA); ap2.fill((255,220,50,7))
    pygame.draw.rect(ap2,(255,200,0,53),(0,0,780,144),2,border_radius=12); surf.blit(ap2,(W//2-390,260))
    for i2,(ln2,col3,fnt3) in enumerate([
        ("You have transcended the Emotion Architect.",(240,230,178),F_MD),
        ("20 worlds. All enemies. All suffering. Conquered.",(200,255,200),F_SM),
        (f"Deaths: {SD['deaths']}  ·  Coins: {SD['coins']}  ·  Runs: {SD['runs']}",(178,200,255),F_SUB),
        ("The void bows to you. You are beyond human.",(220,200,120),F_SUB)]):
        r3=fnt3.render(ln2,True,col3); rs3b=fnt3.render(ln2,True,(0,0,0))
        surf.blit(rs3b,(W//2-r3.get_width()//2+1,270+i2*30+1)); surf.blit(r3,(W//2-r3.get_width()//2,270+i2*30))
    btn2=pygame.Rect(W//2-175,432,350,64)
    for ring in range(6,0,-1):
        gs3=pygame.Surface((btn2.w+ring*14,btn2.h+ring*10),pygame.SRCALPHA)
        pygame.draw.rect(gs3,(*hsv((t*0.06)%1,0.8,1.0),19),(0,0,btn2.w+ring*14,btn2.h+ring*10),border_radius=18)
        surf.blit(gs3,(btn2.x-ring*7,btn2.y-ring*5))
    for by2b in range(btn2.h):
        pygame.draw.rect(surf,lerpC((40,120,40),(20,80,20),by2b/btn2.h),(btn2.x,btn2.y+by2b,btn2.w,1))
    pygame.draw.rect(surf,lerpC((100,255,100),(180,255,180),pulse),btn2,2,border_radius=14)
    hi3=pygame.Surface((btn2.w-10,10),pygame.SRCALPHA); hi3.fill((180,255,180,33)); surf.blit(hi3,(btn2.x+5,btn2.y+5))
    bl3=outlined("▶   PLAY AGAIN",F_LG,(200,255,200),(0,42,0),2)
    surf.blit(bl3,(btn2.centerx-bl3.get_width()//2,btn2.centery-bl3.get_height()//2))
    et2=F_TAG.render(f"EMOTION ARCHITECT: ULTIMATE  ·  v5.0  ·  ALL {TOTAL_LEVELS} WORLDS CLEARED",True,(78,70,28))
    surf.blit(et2,(W//2-et2.get_width()//2,H-24))
    return btn2




# ═══════════════════════════════════════════════════════════════
#  JOYSTICK
# ═══════════════════════════════════════════════════════════════
class Joystick:
    def __init__(self,x,y,r=52):
        self.base=(x,y); self.r=r; self.stick=[float(x),float(y)]
        self.drag=False; self.dx=self.dy=0.0
    def handle(self,e):
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if math.hypot(e.pos[0]-self.base[0],e.pos[1]-self.base[1])<=self.r: self.drag=True
        elif e.type==pygame.MOUSEBUTTONUP and e.button==1:
            self.drag=False; self.stick=list(self.base); self.dx=self.dy=0.0
        elif e.type==pygame.MOUSEMOTION and self.drag:
            dx2=e.pos[0]-self.base[0]; dy2=e.pos[1]-self.base[1]
            d=math.hypot(dx2,dy2)
            if d>self.r: dx2,dy2=dx2/d*self.r,dy2/d*self.r
            self.stick=[self.base[0]+dx2,self.base[1]+dy2]; self.dx,self.dy=dx2/self.r,dy2/self.r
    def draw(self,surf):
        gs=pygame.Surface((self.r*2+24,self.r*2+24),pygame.SRCALPHA)
        pygame.draw.circle(gs,(255,255,255,16),(self.r+12,self.r+12),self.r)
        pygame.draw.circle(gs,(255,255,255,52),(self.r+12,self.r+12),self.r,2)
        surf.blit(gs,(self.base[0]-self.r-12,self.base[1]-self.r-12))
        sx2,sy2=int(self.stick[0]),int(self.stick[1]); sr2=int(self.r*0.4)
        ss2=pygame.Surface((sr2*2+8,sr2*2+8),pygame.SRCALPHA)
        pygame.draw.circle(ss2,(255,255,255,172),(sr2+4,sr2+4),sr2)
        surf.blit(ss2,(sx2-sr2-4,sy2-sr2-4))

joy=Joystick(88,H-88)

# ═══════════════════════════════════════════════════════════════
#  MAIN GAME CLASS
# ═══════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.state="MENU"
        self.settings_return_state="MENU"
        self.lives=5; self.tick=0
        self.platforms=[]; self.enemies=[]; self.coins=[]
        self.portal=None; self.start_pos=(60,H-80)
        self.flash_alpha=0; self.flash_color=(255,255,255)
        self.level_idx=SD["level"]
        self.coins_got=0
        self.popups=[]
        self.combo=0; self.combo_timer=0
        self.world_transition=0
        self.paused=False
        self.ultimate_t=0; self.skill_weave_t=0; self.shield_cooldown_t=0
        self.rage_cooldown_t=0; self.rage_active_t=0
        self.ghost_cooldown_t=0; self.ghost_active_t=0
        self.ultimate_waves=[]   # [{r,alpha,color}] expanding shockwave rings
        self.healing_dash_used=False; self.completed_level_stars=3
        self.level_start_time=_time.time()
        self.death_world=0
        self.completed_level_idx=0
        self.completed_level_time=0
        self.pending_next_level=0
        self.level_meta=level_meta(self.level_idx)
        self.emotion_profile=get_emotion_profile(self.level_meta["emotion"])
        self.skill_tree=SkillTree(SD.get("emotions", []))
        self.world_events=WorldEventSystem(self.level_meta)
        self.load_level(self.level_idx)

    def load_level(self, idx):
        random.seed(idx*11+7)
        self.level_idx=idx
        self.level_meta=level_meta(idx)
        self.emotion_profile=get_emotion_profile(self.level_meta["emotion"])
        self.skill_tree=SkillTree(SD.get("emotions", []))
        self.world_events=WorldEventSystem(self.level_meta)
        self.platforms,self.enemies,self.coins,self.start_pos,goal=build_level(idx)
        for p in self.platforms:
            p.base_mspeed = p.mspeed
        for en in self.enemies:
            en.base_speed = en.speed
        self.portal=Portal(*goal,world_idx=idx)
        player.spawn(*self.start_pos); player.world_idx=idx
        self.coins_got=0; self.world_transition=35
        self.level_deaths=0; self.level_total_coins=len(self.coins)
        self.healing_dash_used=False
        self.rage_cooldown_t=0; self.rage_active_t=0
        self.ghost_cooldown_t=0; self.ghost_active_t=0
        self.level_start_time=_time.time()
        SD["best"]=max(SD.get("best",0),idx); save_game(SD)
        intro_card.trigger(idx)
        # Ambient music crossfade on level load
        global _last_music_mood
        if MIXER_OK and SETTINGS.get("emotion_music", True):
            _mood=self.emotion_profile.get("mood","balanced")
            _pad=AMBIENT_PADS.get(_mood)
            if _pad and _mood!=_last_music_mood:
                CHANNEL_MUSIC.stop()
                CHANNEL_MUSIC.play(_pad,loops=-1,fade_ms=2000)
                _last_music_mood=_mood
        elif MIXER_OK:
            CHANNEL_MUSIC.stop(); _last_music_mood=None
        
        if not hasattr(self, "checkpoint_data") or getattr(self, "checkpoint_data", {}).get("level_id") != idx:
            self.checkpoint_data = {
                "level_id": idx,
                "checkpoint_id": 0,
                "position": (player.rect.centerx, player.rect.centery),
                "abilities": self.skill_tree.unlocked.copy() if hasattr(self, "skill_tree") else [],
                "emotion_state": self.emotion_profile.copy() if hasattr(self, "emotion_profile") else {}
            }
        elif SETTINGS.get("checkpoint_assist"):
            player.rect.centerx, player.rect.centery = self.checkpoint_data["position"]
            if hasattr(self, "emotion_profile"): self.emotion_profile = self.checkpoint_data["emotion_state"].copy()

    def popup(self, x, y, text, color=(255,255,100)):
        self.popups.append([float(x),float(y),text,color,60])

    def die(self):
        if player.invincible>0: return
        player.hit()
        if SETTINGS.get("dream_mode"):
            player.spawn(*self.start_pos, hit=True); player.world_idx=self.level_idx
            return
        if self.skill_tree.has("shield") and player.invincible==0:
            player.invincible=45
            ps.burst(player.rect.centerx,player.rect.centery,
                     count=20,color=WTHEME(self.level_idx)[3],size=5,world=self.level_idx)
            # skill_weaving: shield + slow_time combo → brief ultra-slow window
            if self.skill_tree.has("skill_weaving") and self.skill_tree.has("slow_time"):
                self.skill_weave_t=180
                ps.burst(player.rect.centerx,player.rect.centery,
                         count=35,color=(180,100,255),size=8,world=self.level_idx)
                self.popup(player.rect.centerx,player.rect.centery-36,"SKILL WEAVE!",(200,120,255))
            return
        # healing_dash: survive a death while dashing, once per level
        if (player.dashing and self.skill_tree.has("healing_dash")
                and not self.healing_dash_used and self.lives<5):
            self.healing_dash_used=True
            self.lives=min(5,self.lives+1)
            player.invincible=90
            ps.burst(player.rect.centerx,player.rect.centery,
                     count=30,color=(80,255,160),size=7,world=self.level_idx)
            self.popup(player.rect.centerx,player.rect.centery-30,"HEALING DASH! +♥",(80,255,160))
            return
        if SETTINGS.get("screen_shake") and not SETTINGS.get("reduce_motion"):
            cam.hit(24,10)
        play(SND_DIE)
        ps.burst(player.rect.centerx,player.rect.centery,
                 count=44,color=(255,65,65),size=9,world=self.level_idx)
        self.flash((255,30,30),245)
        SD["deaths"]+=1; save_game(SD)
        self.combo=0; self.level_deaths+=1; self.lives-=1
        if self.lives<=0:
            self.state="GAME_OVER"
            self.death_world=self.level_idx
            save_game(SD)
        else:
            self.load_level(self.level_idx)
            player.spawn(*self.start_pos, hit=True); player.world_idx=self.level_idx

    def flash(self, color=(255,255,255), strength=200):
        self.flash_alpha=strength; self.flash_color=color

    def next_level(self):
        elapsed=_time.time()-self.level_start_time
        if SD["best_times"][self.level_idx]==0 or elapsed<SD["best_times"][self.level_idx]:
            SD["best_times"][self.level_idx]=round(elapsed,1)
        SD["cleared"][self.level_idx]=True
        # Compute actual earned stars (1 = cleared, +1 no deaths, +1 all coins)
        earned=1
        if self.level_deaths==0: earned+=1
        if self.level_total_coins>0 and self.coins_got>=self.level_total_coins: earned+=1
        elif self.level_total_coins==0: earned+=1  # no coins level → full coin star free
        earned=max(earned, SD["level_stars"][self.level_idx])  # never downgrade best
        SD["level_stars"][self.level_idx]=earned
        self.completed_level_stars=earned
        EMOTIONS.complete_level(self.level_idx, level_meta(self.level_idx)["emotion"], stars=earned)
        self.skill_tree=SkillTree(SD.get("emotions", []))
        play(SND_WIN)
        if SETTINGS.get("screen_shake") and not SETTINGS.get("reduce_motion"):
            cam.hit(12)
        play(SND_WIN)
        self.flash((100,255,200),200)
        ps.burst(player.rect.centerx,player.rect.centery,
                 count=75,color=(100,255,200),size=8,world=self.level_idx)
        nxt=self.level_idx+1
        self.completed_level_idx=self.level_idx
        self.completed_level_time=elapsed
        self.pending_next_level=nxt
        if nxt>=TOTAL_LEVELS:
            self.state="LEVEL_COMPLETE"
        else:
            SD["level"]=nxt; save_game(SD)
            self.state="LEVEL_COMPLETE"
            self.load_level(nxt)

    def run(self):
        while True:
            self.tick+=1
            clock.tick(FPS)

            if self.state=="MENU":
                screen.fill((0,0,0))
                btn,btn_set=draw_menu(screen,self.level_idx,self.tick)
                ps.draw(screen)
                flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn.collidepoint(e.pos):
                            SD["runs"]+=1; save_game(SD); self.state="PLAY"
                        if btn_set.collidepoint(e.pos):
                            self.settings_return_state="MENU"; self.state="SETTINGS"
                    if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_SPACE):
                        SD["runs"]+=1; save_game(SD); self.state="PLAY"
                continue

            # ── SETTINGS ─────────────────────────────────────
            if self.state=="SETTINGS":
                back=settings_screen.draw(screen)
                flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if settings_screen.handle_event(e):
                        continue
                    if e.type==pygame.KEYDOWN:
                        if e.key in (pygame.K_ESCAPE, pygame.K_b):
                            self.state=self.settings_return_state
                            if MIXER_OK: sync_audio_volumes()
                            self.emotion_profile=get_emotion_profile(self.level_meta["emotion"])
                        elif e.key==pygame.K_1: cycle_setting("difficulty",["relaxed","normal","challenge"])
                        elif e.key==pygame.K_2: SETTINGS.toggle("assist_mode")
                        elif e.key==pygame.K_3: SETTINGS.toggle("auto_dash")
                        elif e.key==pygame.K_4: SETTINGS.toggle("screen_shake")
                        elif e.key==pygame.K_5: SETTINGS.toggle("focus_mode")
                        elif e.key==pygame.K_6: SETTINGS.toggle("dream_mode")
                        elif e.key==pygame.K_7: cycle_setting("aura",["purple_dream","blue_calm","red_courage","green_hope","gold_balance"])
                        elif e.key==pygame.K_8: cycle_setting("particle_quality",["low","medium","high"])
                        elif e.key==pygame.K_9: cycle_setting("emotion_intensity",["low","medium","high"])
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and back.collidepoint(e.pos):
                        self.state=self.settings_return_state
                        if MIXER_OK: sync_audio_volumes()
                        # Re-apply emotion profile in case emotion_intensity changed
                        self.emotion_profile=get_emotion_profile(self.level_meta["emotion"])
                continue

            # ── GAME OVER ─────────────────────────────────────
            if self.state=="GAME_OVER":
                screen.fill((0,0,0)); btn,btn_set=draw_gameover(screen,self.death_world)
                ps.draw(screen); flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.KEYDOWN and e.key==pygame.K_RETURN:
                        SD["deaths"]=0; save_game(SD); self.lives=5
                        self.load_level(self.death_world); self.state="PLAY"
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn.collidepoint(e.pos):
                            SD["deaths"]=0; save_game(SD)
                            self.lives=5
                            self.load_level(self.death_world)
                            self.state="PLAY"
                        elif btn_set.collidepoint(e.pos):
                            self.settings_return_state="GAME_OVER"
                            self.state="SETTINGS"
                continue

            # ── LEVEL COMPLETE ───────────────────────────────
            if self.state=="LEVEL_COMPLETE":
                screen.fill((0,0,0)); btn=draw_level_complete(screen,self.completed_level_idx,self.completed_level_time,getattr(self,"completed_level_stars",3))
                ps.draw(screen); flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if self.pending_next_level>=TOTAL_LEVELS:
                            self.state="WIN"
                        else:
                            self.load_level(self.pending_next_level); self.state="PLAY"
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1 and btn.collidepoint(e.pos):
                        if self.pending_next_level>=TOTAL_LEVELS:
                            self.state="WIN"
                        else:
                            self.load_level(self.pending_next_level); self.state="PLAY"
                continue

            # ── WIN ───────────────────────────────────────────
            if self.state=="WIN":
                screen.fill((0,0,0)); btn=draw_win(screen)
                ps.draw(screen); flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn.collidepoint(e.pos):
                            SD.update({"level":0,"best":0,"deaths":0,"runs":0,
                                       "cleared":[False]*TOTAL_LEVELS,
                                       "best_times":[0]*TOTAL_LEVELS,
                                       "completed_levels":[],"stars":0,"emotions":[],
                                       "level_stars":[0]*TOTAL_LEVELS})
                            save_game(SD); self.lives=5; self.level_idx=0
                            self.load_level(0); self.state="MENU"
                continue

            # ── PAUSED ────────────────────────────────────────
            if self.paused:
                pause_btns=draw_pause(screen,self.level_idx)
                flip_display()
                for e in get_events():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.KEYDOWN:
                        if e.key==pygame.K_ESCAPE: self.paused=False; play(SND_PAUSE)
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if pause_btns[0].collidepoint(e.pos): self.paused=False; play(SND_PAUSE)
                        elif pause_btns[1].collidepoint(e.pos):
                            self.paused=False; self.settings_return_state="PLAY"; self.state="SETTINGS"
                            self.paused=False; self.load_level(self.level_idx)
                        elif pause_btns[2].collidepoint(e.pos):
                            self.paused=False; self.load_level(self.level_idx)
                        elif pause_btns[3].collidepoint(e.pos):
                            self.paused=False; self.state="MENU"
                continue

            # ── PLAY ──────────────────────────────────────────
            # Read remappable keys from settings (fall back to defaults)
            _k_left    = SETTINGS.get("key_left",    pygame.K_a)
            _k_right   = SETTINGS.get("key_right",   pygame.K_d)
            _k_jump    = SETTINGS.get("key_jump",    pygame.K_SPACE)
            _k_dash    = SETTINGS.get("key_dash",    pygame.K_LSHIFT)
            _k_shield  = SETTINGS.get("key_skill",   pygame.K_e)
            _k_ghost   = SETTINGS.get("key_ghost",   pygame.K_r)
            _k_ultimate= SETTINGS.get("key_ultimate",pygame.K_q)
            _k_pause   = SETTINGS.get("key_pause",   pygame.K_ESCAPE)

            jump=False; dash=False
            for e in get_events():
                if e.type==pygame.QUIT: sys.exit()
                joy.handle(e)
                if e.type==pygame.KEYDOWN:
                    if e.key==_k_pause:
                        self.paused=True; play(SND_PAUSE)
                    if e.key in (_k_jump, pygame.K_UP, pygame.K_w): jump=True
                    if e.key in (_k_dash, pygame.K_LSHIFT, pygame.K_RSHIFT): dash=True
                    # Shield: remappable (default E)
                    if e.key==_k_shield and self.skill_tree.has("shield") and self.shield_cooldown_t==0:
                        player.invincible=30
                        player.shield_active=True
                        self.shield_cooldown_t=300
                        ps.burst(player.rect.centerx,player.rect.centery,
                                 count=24,color=(80,200,255),size=6,world=self.level_idx)
                        play(SND_BOOST)
                        self.popup(player.rect.centerx,player.rect.centery-36,
                                   "SHIELD!  (0.5s)",(80,200,255))
                    # Ghost Step: remappable (default R)
                    if e.key==_k_ghost and self.skill_tree.has("ghost_step") and self.ghost_cooldown_t==0:
                        self.ghost_active_t=90
                        self.ghost_cooldown_t=900
                        play(SND_BOOST)
                        ps.burst(player.rect.centerx,player.rect.centery,
                                 count=20,color=(180,180,255),size=5,world=self.level_idx)
                        self.popup(player.rect.centerx,player.rect.centery-36,
                                   "GHOST STEP! (1.5s)",(180,180,255))
                    # Ultimate: remappable (default Q)
                    if e.key==_k_ultimate and self.skill_tree.has("ultimate_ability") and self.ultimate_t==0:
                        self.ultimate_t=600
                        for en in self.enemies: en.alive=False
                        self.flash((200,180,255),220)
                        ps.burst(W//2,H//2,count=120,color=(200,160,255),size=10,world=self.level_idx)
                        play(SND_WIN)
                        self.popup(W//2,H//2-60,"ULTIMATE!",(200,160,255))
                        # spawn 4 expanding shockwave rings with staggered delays
                        for delay_r in [0, 8, 18, 30]:
                            self.ultimate_waves.append({
                                "r": float(delay_r), "alpha": 220,
                                "color": (200,160,255) if delay_r%2==0 else (255,220,255),
                                "ox": W//2, "oy": H//2,
                            })
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    if e.pos[1]<H//2: jump=True

            keys=pygame.key.get_pressed()
            dx=0.0
            if keys[_k_left]  or keys[pygame.K_LEFT]:  dx-=1
            if keys[_k_right] or keys[pygame.K_RIGHT]: dx+=1
            dx+=joy.dx
            if SETTINGS.get("auto_dash") and player.dash_t==0 and abs(dx)>0.1:
                dash=True

            speed_scale={"relaxed":0.82,"normal":1.0,"challenge":1.13}.get(SETTINGS.get("difficulty"),1.0)
            if SETTINGS.get("assist_mode"):
                speed_scale*=0.9
            
            # Apply Game Speed Setting
            game_speed = SETTINGS.get("game_speed", 100) / 100.0
            speed_scale *= game_speed
            speed_scale*=self.world_events.intensity()
            if self.skill_tree.has("slow_time"):
                speed_scale*=0.92
            # skill_weaving active window: dramatically slow time
            if self.skill_weave_t>0:
                self.skill_weave_t-=1
                speed_scale*=0.45
            # cooldown ticks
            if self.ultimate_t>0: self.ultimate_t-=1
            if self.shield_cooldown_t>0: self.shield_cooldown_t-=1
            if self.ghost_cooldown_t>0: self.ghost_cooldown_t-=1
            if self.ghost_active_t>0: self.ghost_active_t-=1
            if self.rage_cooldown_t>0: self.rage_cooldown_t-=1
            if self.rage_active_t>0: self.rage_active_t-=1
            # sync skill visuals to player flags
            if player.invincible==0: player.shield_active=False
            player.ghost_active=(self.ghost_active_t>0)
            player.rage_active=(self.rage_active_t>0)
            # rage mode: auto-fire when lives critically low
            if (self.skill_tree.has("rage_mode") and self.lives<=2
                    and self.rage_active_t==0 and self.rage_cooldown_t==0):
                self.rage_active_t=1200    # 20 s
                self.rage_cooldown_t=1200
                play(SND_BOOST)
                self.flash((255,80,40),140)
                self.popup(player.rect.centerx,player.rect.centery-48,
                           "RAGE MODE! (+40% SPD)",(255,100,40))
            # apply rage speed bonus
            if self.rage_active_t>0:
                speed_scale*=1.4

            # ── UPDATE ────────────────────────────────────────
            for p in self.platforms:
                p.mspeed=getattr(p,"base_mspeed",p.mspeed)*speed_scale
                p.update()
            for c in self.coins:
                c.update(player.rect.centerx,player.rect.centery,
                         magnet=(self.level_idx==99))
            player.update(self.platforms,dx,jump,dash,self.emotion_profile,self.skill_tree)
            for en in self.enemies:
                en.speed=getattr(en,"base_speed",en.speed)*speed_scale
                en.update(player.rect.centerx,player.rect.centery)
            weather.update_emit(self.level_idx)
            intro_card.update()
            if self.world_events.has_major_challenge and self.tick%45==0:
                wt=WTHEME(self.level_idx)
                ps.emit(random.randint(80,W-80),random.randint(80,H-100),
                        count=2,life=50,color=wt[3],size=4,spread=1.8,grav=0,shape="ring")

            # Coin collection
            for c in self.coins:
                if c.check(player.rect):
                    self.coins_got+=1; SD["coins"]+=1
                    self.combo+=1; self.combo_timer=180
                    play(SND_COIN)
                    ps.burst(c.x,c.y,count=16,
                             color=hsv(self.tick*0.01%1,0.9,1.0),
                             size=5,world=self.level_idx)
                    self.popup(c.x,c.y-26,"+1 ◆",(255,220,80))
                    if self.combo>=5:
                        ps.burst(player.rect.centerx,player.rect.centery,
                                 count=28,color=(255,200,0),size=7,world=self.level_idx)

            # Coin burst: auto-collect all remaining coins at combo ≥ 10
            if (self.skill_tree.has("coin_burst") and self.combo>=10
                    and any(not c.collected for c in self.coins)):
                burst_count=0
                for c in self.coins:
                    if not c.collected:
                        c.collected=True
                        self.coins_got+=1; SD["coins"]+=1
                        burst_count+=1
                if burst_count:
                    ps.burst(player.rect.centerx,player.rect.centery,
                             count=burst_count*6,color=(255,230,80),size=7,world=self.level_idx)
                    play(SND_COIN)
                    self.popup(player.rect.centerx,player.rect.centery-48,
                               f"COIN BURST! +{burst_count}",(255,220,60))

            # Deaths: fall off + deadly platforms (ghost step bypasses deadly platforms)
            if player.rect.top>H: self.die()
            if self.ghost_active_t==0 and player.check_deadly(self.platforms): self.die()

            # Enemy collisions
            for en in self.enemies:
                if not en.alive: continue
                if player.rect.colliderect(en.get_rect()) and player.invincible==0:
                    self.die(); break
                for b in en.bullets[:]:
                    br=pygame.Rect(int(b["x"])-5,int(b["y"])-5,10,10)
                    if player.rect.colliderect(br) and player.invincible==0:
                        self.die()
                        if b in en.bullets: en.bullets.remove(b)
                        break

            # Checkpoint Assist Tracking
            if self.state == "PLAY" and getattr(player, "on_ground", False) and SETTINGS.get("checkpoint_assist"):
                last_ckpt = self.checkpoint_data.get("position", (0,0))
                if player.rect.centerx > last_ckpt[0] + 900:
                    self.checkpoint_data["position"] = (player.rect.centerx, player.rect.centery)
                    self.checkpoint_data["checkpoint_id"] = self.checkpoint_data.get("checkpoint_id", 0) + 1
                    if hasattr(self, "skill_tree"): self.checkpoint_data["abilities"] = self.skill_tree.unlocked.copy()
                    if hasattr(self, "emotion_profile"): self.checkpoint_data["emotion_state"] = self.emotion_profile.copy()
                    self.popup(player.rect.centerx, player.rect.y - 40, "CHECKPOINT", (100, 255, 100))

            # Portal
            self.portal.update()
            pr=pygame.Rect(self.portal.x-self.portal.r,self.portal.y-self.portal.r,
                           self.portal.r*2,self.portal.r*2)
            if player.rect.colliderect(pr): play(SND_PORTAL); self.next_level()

            # Combo timer
            if self.combo_timer>0:
                self.combo_timer-=1
                if self.combo_timer==0: self.combo=0

            # Ambient particles
            particle_step = 24 if SETTINGS.get("focus_mode") or SETTINGS.get("particle_quality")=="low" else 14 if SETTINGS.get("particle_quality")=="medium" else 9
            if self.tick%particle_step==0:
                wt=WTHEME(self.level_idx)
                pcount=max(1,int(self.emotion_profile.get("particle",1.0)))
            if self.tick%9==0:
                ps.emit(random.randint(0,W),H,count=1,vy=-0.85,life=230,
                        spread=0.4,color=wt[5],size=2,grav=-0.004,fade=True)
                if pcount>1:
                    ps.emit(random.randint(0,W),random.randint(80,H-120),count=pcount-1,
                            life=110,color=wt[3],size=2,spread=0.7,grav=0,fade=True)

            # Popups
            self.popups=[p for p in self.popups if p[4]>0]
            for p in self.popups: p[1]-=0.85; p[4]-=1

            # ── DRAW ──────────────────────────────────────────
            bg.draw(screen,self.level_idx)
            weather.draw(screen)

            # World transition fade
            if self.world_transition>0:
                al=int(255*(self.world_transition/35))
                ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,0,al))
                screen.blit(ov,(0,0)); self.world_transition-=1

            for p in self.platforms: p.draw(screen,self.tick)
            for c in self.coins:     c.draw(screen)
            for en in self.enemies:  en.draw(screen,self.tick)
            self.portal.draw(screen)
            player.draw(screen)
            ps.draw(screen)

            # Ultimate shockwave rings
            next_waves=[]
            for w in self.ultimate_waves:
                w["r"]+=14; w["alpha"]=max(0,w["alpha"]-9)
                if w["alpha"]>0:
                    ws=pygame.Surface((W,H),pygame.SRCALPHA)
                    pygame.draw.circle(ws,(*w["color"],int(w["alpha"])),
                                       (int(w["ox"]),int(w["oy"])),int(w["r"]),4)
                    screen.blit(ws,(0,0))
                    next_waves.append(w)
            self.ultimate_waves=next_waves

            # Off-screen enemy arrows
            draw_edge_indicators(screen,self.enemies,self.tick)

            # Popups
            for p in self.popups:
                a=int(255*(p[4]/60))
                draw_text(screen,p[2],(int(p[0]),int(p[1])),p[3],F_SM,center=True,alpha=a,shadow=False)

            # Flash
            if self.flash_alpha>0:
                fl=pygame.Surface((W,H),pygame.SRCALPHA)
                fl.fill((*self.flash_color,int(self.flash_alpha)))
                screen.blit(fl,(0,0)); self.flash_alpha=max(0,self.flash_alpha-15)

            # Rage Mode: pulsing red vignette at screen edges
            if self.rage_active_t>0:
                rage_pulse=int(20+14*((math.sin(self.tick*0.22)+1)/2))
                rv=pygame.Surface((W,H),pygame.SRCALPHA)
                for vi in range(24,0,-4):
                    aa=max(0,rage_pulse-vi*2)
                    pygame.draw.rect(rv,(220,40,10,aa),(vi,vi,W-vi*2,H-vi*2),vi)
                screen.blit(rv,(0,0))

            # Ghost Step: purple vignette
            if self.ghost_active_t>0:
                gv=pygame.Surface((W,H),pygame.SRCALPHA)
                for vi in range(20,0,-4):
                    aa=max(0,14-vi)
                    pygame.draw.rect(gv,(120,80,220,aa),(vi,vi,W-vi*2,H-vi*2),vi)
                screen.blit(gv,(0,0))

            # HUD
            elapsed=_time.time()-self.level_start_time
            draw_hud(screen,self.level_idx,self.lives,self.tick,
                     len(self.coins),self.coins_got,self.combo,
                     player.dash_t,elapsed,
                     self.shield_cooldown_t,self.skill_tree.has("shield"),
                     self.ghost_cooldown_t,self.ghost_active_t,self.skill_tree.has("ghost_step"),
                     self.rage_cooldown_t,self.rage_active_t,self.skill_tree.has("rage_mode"))
            joy.draw(screen)

            # World intro card (drawn last, on top)
            intro_card.draw(screen)

            cam.update(); cam.apply(screen)
            flip_display()

# ═══════════════════════════════════════════════════════════════
#  LAUNCH
# ═══════════════════════════════════════════════════════════════
if __name__=="__main__":
    Game().run()
    pygame.quit(); sys.exit()
# ════════════════════�
