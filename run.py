"""
╔══════════════════════════════════════════════════════════════════════════╗
║        EMOTION ARCHITECT  ◆  TRANSCENDENT EDITION  ◆  v3.0             ║
║        20 Worlds. No mercy. No checkpoints. Only suffering.             ║
╠══════════════════════════════════════════════════════════════════════════╣
║  Controls:                                                               ║
║    A / D  or  ←→      Move                                              ║
║    SPACE / W / ↑       Jump  (INSTANT — zero frame delay)               ║
║    SPACE (air)         Coyote jump (150ms grace window)                 ║
║    ESC                 Pause                                             ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import math, random, sys, os, json
import pygame
from pygame import gfxdraw

# ═══════════════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════════════
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)

W, H   = 1280, 720
FPS    = 60
SAVE   = "ea_transcendent.json"

screen  = pygame.display.set_mode((W, H))
pygame.display.set_caption("EMOTION ARCHITECT: TRANSCENDENT")
clock   = pygame.time.Clock()

# ═══════════════════════════════════════════════════════════════
#  FONTS
# ═══════════════════════════════════════════════════════════════
def mkfont(names, size, bold=False):
    for n in names:
        try:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f: return f
        except: pass
    return pygame.font.SysFont("arial", size, bold=bold)

F_TINY  = mkfont(["Consolas","Lucida Console","Courier New"], 13)
F_SM    = mkfont(["Consolas","Lucida Console","Courier New"], 17)
F_MD    = mkfont(["Trebuchet MS","Segoe UI","Tahoma"],        22, bold=True)
F_LG    = mkfont(["Trebuchet MS","Segoe UI","Tahoma"],        36, bold=True)
F_XL    = mkfont(["Impact","Arial Black","Arial"],            64, bold=True)
F_TITLE = mkfont(["Impact","Arial Black","Arial"],            100,bold=True)

# ═══════════════════════════════════════════════════════════════
#  SAVE
# ═══════════════════════════════════════════════════════════════
def load_save():
    if os.path.exists(SAVE):
        try:
            with open(SAVE) as f: return json.load(f)
        except: pass
    return {"level":0,"best":0,"deaths":0,"runs":0,"coins":0}

def save_game(d):
    with open(SAVE,"w") as f: json.dump(d,f)

SD = load_save()

# ═══════════════════════════════════════════════════════════════
#  MATH HELPERS
# ═══════════════════════════════════════════════════════════════
def clamp(x,a,b): return max(a,min(b,x))
def lerp(a,b,t):  return a+(b-a)*t
def lerpC(c1,c2,t): return tuple(int(lerp(c1[i],c2[i],t)) for i in range(3))
def dist2(ax,ay,bx,by): return math.hypot(ax-bx, ay-by)

def hsv(h,s,v):
    import colorsys
    r,g,b = colorsys.hsv_to_rgb(h%1.0,s,v)
    return (int(r*255),int(g*255),int(b*255))

def draw_text(surf,txt,pos,color=(255,255,255),font=None,center=False,shadow=True,alpha=255):
    f = font or F_SM
    if shadow:
        sr = f.render(txt,True,(0,0,0))
        ox = pos[0]-(sr.get_width()//2 if center else 0)
        surf.blit(sr,(ox+2,pos[1]+2))
    r = f.render(txt,True,color)
    if alpha < 255:
        r.set_alpha(alpha)
    x = pos[0]-r.get_width()//2 if center else pos[0]
    surf.blit(r,(x,pos[1]))

def circ(surf,color,pos,radius,alpha=255):
    x,y,r = int(pos[0]),int(pos[1]),int(radius)
    if r<=0: return
    if alpha<255:
        s = pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*color[:3],alpha),(r,r),r)
        surf.blit(s,(x-r,y-r))
    else:
        try:
            gfxdraw.aacircle(surf,x,y,r,color)
            gfxdraw.filled_circle(surf,x,y,r,color)
        except:
            pygame.draw.circle(surf,color,(x,y),r)

# ═══════════════════════════════════════════════════════════════
#  SOUND (procedural)
# ═══════════════════════════════════════════════════════════════
def gen_sound(freq=440,dur=0.1,vol=0.35,wave="sine",sweep=0):
    rate = 44100
    n    = int(rate*dur)
    buf  = bytearray(n*2)
    for i in range(n):
        t   = i/rate
        env = min(1.0, (n-i)/max(1,n*0.15))
        f   = freq * (1 + sweep*t)
        if   wave=="sine":   s = math.sin(math.tau*f*t)
        elif wave=="square": s = 1.0 if math.sin(math.tau*f*t)>0 else -1.0
        elif wave=="saw":    s = 2*(f*t%1)-1
        elif wave=="noise":  s = random.uniform(-1,1)
        else:                s = math.sin(math.tau*f*t)
        v = clamp(int(s*env*vol*32767),-32768,32767)
        buf[i*2]=v&0xFF; buf[i*2+1]=(v>>8)&0xFF
    snd = pygame.mixer.Sound(buffer=bytes(buf))
    snd.set_volume(vol)
    return snd

try:
    SND_JUMP   = gen_sound(520, 0.07, 0.28,"sine",   sweep=0.5)
    SND_LAND   = gen_sound(180, 0.06, 0.20,"sine",   sweep=-0.3)
    SND_DIE    = gen_sound(110, 0.55, 0.45,"square", sweep=-0.8)
    SND_WIN    = gen_sound(800, 0.35, 0.38,"sine",   sweep=0.3)
    SND_COIN   = gen_sound(880, 0.09, 0.25,"sine",   sweep=0.2)
    SND_PORTAL = gen_sound(440, 0.22, 0.32,"saw",    sweep=0.4)
    SND_DASH   = gen_sound(300, 0.05, 0.20,"saw",    sweep=1.0)
    SOUND_OK   = True
except:
    SOUND_OK   = False

def play(snd):
    if SOUND_OK:
        try: snd.play()
        except: pass

# ═══════════════════════════════════════════════════════════════
#  PARTICLES
# ═══════════════════════════════════════════════════════════════
class Particle:
    __slots__=["x","y","vx","vy","life","ml","color","size","grav","fade","rot","shape"]
    def __init__(self,x,y,vx,vy,life,color,size=3,grav=0.0,fade=True,shape="circle"):
        self.x,self.y     = float(x),float(y)
        self.vx,self.vy   = float(vx),float(vy)
        self.life=self.ml = int(life)
        self.color=color; self.size=size; self.grav=grav
        self.fade=fade; self.rot=random.uniform(0,6.28); self.shape=shape

    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=self.grav; self.vx*=0.96
        self.rot+=0.1; self.life-=1
        return self.life>0

    def draw(self,surf):
        t   = self.life/self.ml
        alp = int(255*t) if self.fade else 255
        s   = max(1,int(self.size*t))
        c   = tuple(min(255,max(0,int(self.color[i]))) for i in range(3))
        if self.shape=="square":
            sq=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
            sq.fill((*c,alp))
            surf.blit(sq,(int(self.x)-s,int(self.y)-s))
        elif self.shape=="star":
            pts=[]
            for k in range(5):
                a=self.rot+k*math.tau/5
                r2=s*2 if k%2==0 else s
                pts.append((self.x+math.cos(a)*r2,self.y+math.sin(a)*r2))
            if len(pts)>=3:
                ss=pygame.Surface((s*6,s*6),pygame.SRCALPHA)
                off=(s*3,s*3)
                adj=[(p[0]-self.x+off[0],p[1]-self.y+off[1]) for p in pts]
                pygame.draw.polygon(ss,(*c,alp),adj)
                surf.blit(ss,(self.x-off[0],self.y-off[1]))
        else:
            try:
                gfxdraw.filled_circle(surf,int(self.x),int(self.y),s,(*c,alp))
            except:
                pygame.draw.circle(surf,c,(int(self.x),int(self.y)),s)

class PS:
    def __init__(self,mx=3500):
        self.pool=[]; self.mx=mx

    def emit(self,x,y,vx=0,vy=0,spread=3,count=5,life=40,
             color=(255,200,100),size=4,grav=0.05,fade=True,shape="circle"):
        for _ in range(count):
            a=random.uniform(0,math.tau); sp=random.uniform(0,spread)
            self.pool.append(Particle(
                x+random.uniform(-2,2), y+random.uniform(-2,2),
                vx+math.cos(a)*sp, vy+math.sin(a)*sp,
                life+random.randint(-life//5,life//5),
                color,size,grav,fade,shape))
        if len(self.pool)>self.mx:
            self.pool=self.pool[-self.mx:]

    def burst(self,x,y,count=20,color=(255,200,50),size=5):
        self.emit(x,y,spread=7,count=count,life=55,color=color,
                  size=size,grav=0.12,shape="circle")
        self.emit(x,y,spread=5,count=count//2,life=40,color=(255,255,255),
                  size=size//2,grav=0.08,shape="star")

    def draw(self,surf):
        self.pool=[p for p in self.pool if p.update()]
        for p in self.pool: p.draw(surf)

ps = PS()

# ═══════════════════════════════════════════════════════════════
#  CAMERA
# ═══════════════════════════════════════════════════════════════
class Camera:
    def __init__(self):
        self.shake=0.0; self.ox=self.oy=0.0
        self.chromatic=0.0

    def hit(self,s=14,ch=0):
        self.shake=max(self.shake,s)
        self.chromatic=max(self.chromatic,ch)

    def update(self):
        if self.shake>0.1:
            self.ox=random.gauss(0,self.shake*0.5)
            self.oy=random.gauss(0,self.shake*0.5)
            self.shake*=0.75
        else:
            self.shake=self.ox=self.oy=0
        if self.chromatic>0.1:
            self.chromatic*=0.8
        else:
            self.chromatic=0

    def apply(self,surf):
        if self.shake>0.5:
            dst=pygame.Surface((W,H)); dst.fill((0,0,0))
            dst.blit(surf,(int(self.ox),int(self.oy)))
            surf.blit(dst,(0,0))
        if self.chromatic>1:
            ch=int(self.chromatic)
            r_surf=pygame.Surface((W,H),pygame.SRCALPHA)
            r_surf.blit(surf,(0,0))
            r_surf.fill((255,0,0,40),special_flags=pygame.BLEND_RGBA_MULT)
            b_surf=pygame.Surface((W,H),pygame.SRCALPHA)
            b_surf.blit(surf,(0,0))
            b_surf.fill((0,0,255,40),special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(r_surf,(-ch,0),special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(b_surf,(ch,0), special_flags=pygame.BLEND_RGBA_ADD)

cam = Camera()

# ═══════════════════════════════════════════════════════════════
#  COIN
# ═══════════════════════════════════════════════════════════════
class Coin:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.t=random.uniform(0,6.28)
        self.collected=False; self.r=8

    def update(self): self.t+=0.06

    def draw(self,surf):
        if self.collected: return
        bob=math.sin(self.t)*4
        c=hsv(self.t*0.05%1,0.9,1.0)
        gls=pygame.Surface((30,30),pygame.SRCALPHA)
        pygame.draw.circle(gls,(*c,60),(15,15),14)
        surf.blit(gls,(self.x-15,self.y-15+bob))
        circ(surf,c,(self.x,self.y+bob),self.r)
        circ(surf,(255,255,255),(self.x-2,self.y-2+bob),3)

    def check(self,prect):
        if self.collected: return False
        cr=pygame.Rect(self.x-self.r,self.y-self.r,self.r*2,self.r*2)
        if prect.colliderect(cr):
            self.collected=True; return True
        return False

# ═══════════════════════════════════════════════════════════════
#  PLATFORM
# ═══════════════════════════════════════════════════════════════
class Platform:
    def __init__(self,x,y,w,h,color=(60,80,120),deadly=False,
                 moving=False,mx=0,my=0,mrange=100,mspeed=1.5,
                 phase=False,phase_time=90,crumble=False,boost=False):
        self.rect=pygame.Rect(x,y,w,h)
        self.ox,self.oy=x,y
        self.color=color; self.deadly=deadly
        self.moving=moving; self.mx=mx; self.my=my
        self.mrange=mrange; self.mspeed=mspeed
        self.phase=phase; self.phase_time=phase_time
        self.phase_timer=random.randint(0,phase_time)
        self.visible=True; self.t=0.0
        self.crumble=crumble   # falls after player stands on it
        self.crumble_timer=0
        self.crumbling=False
        self.boost=boost       # bounce pad
        self.prev_rect=pygame.Rect(x,y,w,h)

    def update(self):
        self.prev_rect=self.rect.copy()
        self.t+=0.02
        if self.moving:
            s=math.sin(self.t*self.mspeed)
            self.rect.x=int(self.ox+self.mx*s*self.mrange)
            self.rect.y=int(self.oy+self.my*s*self.mrange)
        if self.phase:
            self.phase_timer=(self.phase_timer+1)%(self.phase_time*2)
            self.visible=self.phase_timer<self.phase_time
        if self.crumbling:
            self.crumble_timer+=1
            if self.crumble_timer>40:
                self.visible=False

    def draw(self,surf,tick):
        if not self.visible:
            if self.phase and (self.phase_time*2-self.phase_timer)<22:
                t=(self.phase_time*2-self.phase_timer)/22
                a=pygame.Surface((self.rect.w,self.rect.h),pygame.SRCALPHA)
                a.fill((*self.color,int(70*t)))
                surf.blit(a,self.rect.topleft)
            return
        c=self.color
        if self.deadly:
            pulse=(math.sin(tick*0.09)+1)/2
            c=lerpC((210,15,15),(255,90,40),pulse)
        elif self.boost:
            pulse=(math.sin(tick*0.12)+1)/2
            c=lerpC((20,180,20),(100,255,100),pulse)
        elif self.moving:
            c=lerpC(self.color,(180,220,255),0.35)
        elif self.crumbling:
            t=self.crumble_timer/40
            c=lerpC(self.color,(180,80,20),t)
        # Shadow
        shadow=pygame.Surface((self.rect.w,8),pygame.SRCALPHA)
        shadow.fill((0,0,0,40))
        surf.blit(shadow,(self.rect.x,self.rect.bottom))
        # Body
        pygame.draw.rect(surf,c,self.rect,border_radius=5)
        # Top highlight
        hi=lerpC(c,(255,255,255),0.4)
        pygame.draw.rect(surf,hi,
            pygame.Rect(self.rect.x+2,self.rect.y,self.rect.w-4,4),border_radius=3)
        # Side depth
        dk=lerpC(c,(0,0,0),0.3)
        pygame.draw.rect(surf,dk,
            pygame.Rect(self.rect.x,self.rect.y+4,3,self.rect.h-4))
        # Boost arrow
        if self.boost:
            ax=self.rect.centerx; ay=self.rect.y-2
            pts=[(ax,ay-10),(ax-8,ay+2),(ax+8,ay+2)]
            pygame.draw.polygon(surf,(200,255,200),pts)
        # Crumble cracks
        if self.crumbling and self.crumble_timer>10:
            for i in range(3):
                cx=self.rect.x+random.randint(10,self.rect.w-10)
                cy=self.rect.y+random.randint(2,self.rect.h-2)
                pygame.draw.line(surf,(0,0,0),(cx,cy),(cx+random.randint(-8,8),cy+random.randint(-4,4)),1)

# ═══════════════════════════════════════════════════════════════
#  ENEMIES — massively upgraded
# ═══════════════════════════════════════════════════════════════
class Enemy:
    def __init__(self,x,y,etype="patrol",color=(200,50,50),
                 px1=0,px2=0,speed=2.0,size=18,
                 ocx=0,ocy=0,orb_r=80,orb_spd=0.02,
                 shoot_iv=0,hp=1):
        self.x,self.y=float(x),float(y)
        self.etype=etype; self.color=color; self.speed=speed; self.size=size
        self.px1,self.px2=px1,px2; self.dir=1
        self.ocx,self.ocy=float(ocx),float(ocy)
        self.orb_r=orb_r; self.orb_spd=orb_spd
        self.angle=random.uniform(0,math.tau)
        self.shoot_iv=shoot_iv; self.shoot_t=0
        self.bullets=[]; self.alive=True; self.t=0.0
        self.hp=hp; self.max_hp=hp
        self.hurt_t=0
        self.warn_ring=0.0   # telegraphs shoot

    def update(self,px=0,py=0):
        self.t+=1
        if self.hurt_t>0: self.hurt_t-=1
        if not self.alive: return
        if self.etype=="patrol":
            self.x+=self.speed*self.dir
            if self.x<self.px1: self.dir=1
            if self.x>self.px2: self.dir=-1
        elif self.etype=="orbit":
            self.angle+=self.orb_spd
            self.x=self.ocx+math.cos(self.angle)*self.orb_r
            self.y=self.ocy+math.sin(self.angle)*self.orb_r
        elif self.etype=="chase":
            dx=px-self.x; dy=py-self.y
            d=math.hypot(dx,dy)
            if d>0: self.x+=(dx/d)*self.speed; self.y+=(dy/d)*self.speed
        elif self.etype=="sine":
            self.x+=self.speed
            self.y=self.ocy+math.sin(self.t*0.05)*self.orb_r
            if self.x>self.px2: self.x=self.px1
        elif self.etype=="zigzag":
            self.x+=self.speed*self.dir
            if self.t%30==0: self.dir*=-1
            self.y=self.ocy+math.sin(self.t*0.08)*self.orb_r
        elif self.etype=="teleport":
            if self.t%120==0:
                self.x=random.uniform(100,W-100)
                self.y=random.uniform(100,H-200)
                ps.emit(self.x,self.y,count=15,life=30,color=self.color,spread=5)
        if self.shoot_iv>0:
            self.shoot_t+=1
            self.warn_ring=max(0,(self.shoot_t-(self.shoot_iv-25))/25)
            if self.shoot_t>=self.shoot_iv:
                self.shoot_t=0; self.warn_ring=0
                dx=px-self.x; dy=py-self.y; d=math.hypot(dx,dy)
                if d>0:
                    spd=5.0
                    self.bullets.append({"x":self.x,"y":self.y,
                        "vx":(dx/d)*spd,"vy":(dy/d)*spd,"life":200})
                    # triple shot at high hp
                    if self.max_hp>=3:
                        for ang_off in [-0.25,0.25]:
                            a=math.atan2(dy,dx)+ang_off
                            self.bullets.append({"x":self.x,"y":self.y,
                                "vx":math.cos(a)*spd,"vy":math.sin(a)*spd,"life":200})
        for b in self.bullets:
            b["x"]+=b["vx"]; b["y"]+=b["vy"]; b["life"]-=1
        self.bullets=[b for b in self.bullets if b["life"]>0]

    def get_rect(self):
        s=self.size
        return pygame.Rect(int(self.x-s//2),int(self.y-s//2),s,s)

    def draw(self,surf,tick):
        if not self.alive: return
        pulse=(math.sin(tick*0.1)+1)/2
        hurt=self.hurt_t/8
        c=lerpC(self.color,(255,255,255),max(pulse*0.25,hurt*0.8))
        # Warn ring
        if self.warn_ring>0:
            wr=int(self.size*1.5+self.warn_ring*20)
            wc=(*hsv(0.0,0.9,1.0),int(180*self.warn_ring))
            gs=pygame.Surface((wr*2+4,wr*2+4),pygame.SRCALPHA)
            pygame.draw.circle(gs,wc,(wr+2,wr+2),wr,3)
            surf.blit(gs,(self.x-wr-2,self.y-wr-2))
        # Glow aura
        gsize=self.size*3
        gls=pygame.Surface((gsize*2,gsize*2),pygame.SRCALPHA)
        ga=int(30+pulse*20)
        pygame.draw.circle(gls,(*self.color,ga),(gsize,gsize),gsize)
        surf.blit(gls,(self.x-gsize,self.y-gsize))
        # Body
        circ(surf,c,(self.x,self.y),self.size//2)
        # Inner detail
        ic=lerpC(c,(255,255,255),0.5)
        circ(surf,ic,(self.x,self.y),self.size//4)
        # Eyes
        eye_x=self.x+(self.size//5)*(self.dir if self.etype=="patrol" else 1)
        eye_y=self.y-self.size//7
        circ(surf,(255,255,255),(eye_x,eye_y),3)
        circ(surf,(20,20,20),(eye_x+1,eye_y),2)
        # HP bar
        if self.max_hp>1:
            bw=self.size+8; bh=4
            bx=self.x-bw//2; by=self.y-self.size//2-10
            pygame.draw.rect(surf,(60,20,20),(bx,by,bw,bh),border_radius=2)
            fw=int(bw*(self.hp/self.max_hp))
            pygame.draw.rect(surf,(220,60,60),(bx,by,fw,bh),border_radius=2)
        # Bullets
        for b in self.bullets:
            circ(surf,(255,230,60),(b["x"],b["y"]),5)
            ps.emit(b["x"],b["y"],count=1,life=6,color=(255,200,0),size=3,spread=0.5)

# ═══════════════════════════════════════════════════════════════
#  PORTAL
# ═══════════════════════════════════════════════════════════════
class Portal:
    def __init__(self,x,y):
        self.x,self.y=x,y; self.r=32; self.t=0.0; self.pulse=0.0

    def update(self):
        self.t+=0.05
        self.pulse=(math.sin(self.t*2)+1)/2
        # Ring of particles
        for i in range(2):
            a=self.t+i*math.pi
            px=self.x+math.cos(a)*(self.r+8)
            py=self.y+math.sin(a)*(self.r+8)
            ps.emit(px,py,count=1,life=25,
                    color=hsv((self.t*0.08)%1,0.9,1.0),size=4,spread=0.8,grav=-0.02)

    def draw(self,surf):
        # Outer glow rings
        for ring in range(5,0,-1):
            a=50-ring*8
            c=(*hsv((self.t*0.06+ring*0.08)%1,0.9,1.0),a)
            rs=self.r+ring*7+int(self.pulse*5)
            gs=pygame.Surface((rs*2+8,rs*2+8),pygame.SRCALPHA)
            pygame.draw.circle(gs,c,(rs+4,rs+4),rs,3)
            surf.blit(gs,(self.x-rs-4,self.y-rs-4))
        # Inner fill
        circ(surf,hsv(self.t*0.06%1,0.7,0.9),(self.x,self.y),self.r+int(self.pulse*3))
        circ(surf,(255,255,255),(self.x,self.y),self.r//2)
        # Label
        draw_text(surf,"EXIT",(self.x,self.y-self.r-24),
                  (255,255,180),F_TINY,center=True,shadow=True)

# ═══════════════════════════════════════════════════════════════
#  PLAYER  — coyote time + jump buffer + dash
# ═══════════════════════════════════════════════════════════════
class Player:
    SIZE    = 22
    GRAVITY = 0.52
    JUMP    = -13.2
    SPEED   = 5.8
    DASH_V  = 14.0
    DASH_DUR= 8
    COYOTE  = 9    # frames of coyote time
    JBUFFER = 8    # jump buffer frames

    def __init__(self):
        self.rect    = pygame.Rect(0,0,self.SIZE,self.SIZE)
        self.vx=self.vy=0.0
        self.on_ground=False
        self.coyote_t=0      # counts down from COYOTE when leaving ground
        self.jbuffer_t=0     # counts down — "I pressed jump, land me soon"
        self.trail=[]
        self.t=0
        self.dash_t=0        # dash cooldown
        self.dashing=False
        self.dash_dir=1
        self.invincible=0    # frames after death
        self.last_vx=0.0

    def spawn(self,x,y):
        self.rect.x,self.rect.y=x,y
        self.vx=self.vy=0.0
        self.on_ground=False
        self.coyote_t=0; self.jbuffer_t=0
        self.dash_t=0; self.dashing=False
        self.invincible=60
        self.trail.clear()

    def update(self,platforms,dx,jump,dash):
        self.t+=1
        if self.invincible>0: self.invincible-=1
        if self.dash_t>0: self.dash_t-=1

        # ── DASH ─────────────────────────────────────────────────
        if dash and self.dash_t==0 and not self.dashing:
            self.dashing=True
            self.dash_dir=1 if dx>=0 else -1
            self.dashing_t=self.DASH_DUR
            self.dash_t=35
            self.vy*=0.3
            play(SND_DASH)
            ps.emit(self.rect.centerx,self.rect.centery,
                    count=12,life=20,color=(180,220,255),size=5,spread=4,grav=0)

        if self.dashing:
            self.dashing_t-=1
            self.vx=self.dash_dir*self.DASH_V
            if self.dashing_t<=0:
                self.dashing=False

        # ── HORIZONTAL ───────────────────────────────────────────
        if not self.dashing:
            self.vx=dx*self.SPEED
        self.last_vx=self.vx

        # ── COYOTE COUNTER ───────────────────────────────────────
        was_grounded=self.on_ground
        if was_grounded:
            self.coyote_t=self.COYOTE
        elif self.coyote_t>0:
            self.coyote_t-=1

        # ── JUMP BUFFER ──────────────────────────────────────────
        if jump:
            self.jbuffer_t=self.JBUFFER
        elif self.jbuffer_t>0:
            self.jbuffer_t-=1

        # ── JUMP EXECUTION (instant — before gravity) ────────────
        can_jump = self.coyote_t>0   # ground or coyote window
        if self.jbuffer_t>0 and can_jump:
            self.vy=self.JUMP
            self.coyote_t=0
            self.jbuffer_t=0
            play(SND_JUMP)
            ps.emit(self.rect.centerx,self.rect.bottom,
                    count=12,life=22,color=(200,230,255),size=4,spread=3.5,grav=-0.05)

        # ── GRAVITY ──────────────────────────────────────────────
        if not self.dashing:
            self.vy+=self.GRAVITY
        self.vy=clamp(self.vy,-20,18)

        # ── MOVE & COLLIDE ───────────────────────────────────────
        self.rect.x+=int(self.vx)
        self.rect.x=clamp(self.rect.x,20,W-40)
        self._res_x(platforms)

        prev_y=self.rect.y
        self.rect.y+=int(self.vy)
        self.on_ground=False
        landed=self._res_y(platforms)
        if landed and not was_grounded and abs(self.vy)>3:
            play(SND_LAND)
            ps.emit(self.rect.centerx,self.rect.bottom,
                    count=8,life=18,color=(160,200,255),size=3,spread=2,grav=0.05)

        # Trail
        self.trail.append((self.rect.centerx,self.rect.centery,
                           hsv(self.t*0.006%1,0.9,1.0)))
        if len(self.trail)>22: self.trail.pop(0)

    def _res_x(self,platforms):
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vx>0: self.rect.right=p.rect.left
                elif self.vx<0: self.rect.left=p.rect.right

    def _res_y(self,platforms):
        landed=False
        for p in platforms:
            if not p.visible: continue
            if self.rect.colliderect(p.rect):
                if self.vy>0:
                    self.rect.bottom=p.rect.top
                    self.vy=0; self.on_ground=True; landed=True
                    if p.crumble and not p.crumbling:
                        p.crumbling=True
                    if p.boost:
                        self.vy=-18
                        ps.burst(self.rect.centerx,self.rect.bottom,
                                 color=(100,255,100))
                elif self.vy<0:
                    self.rect.top=p.rect.bottom; self.vy=0
        return landed

    def check_deadly(self,platforms):
        if self.invincible>0: return False
        for p in platforms:
            if p.deadly and p.visible and self.rect.colliderect(p.rect):
                return True
        return False

    def draw(self,surf):
        # Trail
        for i,(tx,ty,tc) in enumerate(self.trail):
            t=i/len(self.trail)
            alp=int(110*t)
            s=max(2,int(7*t))
            gs=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*tc,alp),(s,s),s)
            surf.blit(gs,(tx-s,ty-s))

        # Invincibility flicker
        if self.invincible>0 and (self.invincible//4)%2==1:
            return

        c=hsv(self.t*0.006%1,0.8,1.0)

        # Glow
        gls=pygame.Surface((64,64),pygame.SRCALPHA)
        pygame.draw.circle(gls,(*c,45),(32,32),30)
        surf.blit(gls,(self.rect.centerx-32,self.rect.centery-32))

        # Dash ghost
        if self.dashing:
            for i in range(3):
                gx=self.rect.x-self.dash_dir*i*10
                ga=pygame.Surface((self.SIZE,self.SIZE),pygame.SRCALPHA)
                ga.fill((*c,60-i*20))
                surf.blit(ga,(gx,self.rect.y))

        # Body
        pygame.draw.rect(surf,c,self.rect,border_radius=6)
        # Highlight
        pygame.draw.rect(surf,(255,255,255),
            pygame.Rect(self.rect.x+3,self.rect.y+3,self.rect.w-6,4),border_radius=3)

        # Eyes — face direction
        face=1 if self.vx>=0 else -1
        ey=self.rect.y+7
        for off in [6,14]:
            ex=self.rect.x+off
            circ(surf,(255,255,255),(ex,ey),3)
            circ(surf,(0,0,0),(ex+face,ey),2)

        # Dash indicator on feet
        if self.dash_t==0:
            pygame.draw.rect(surf,(100,255,200),
                pygame.Rect(self.rect.x,self.rect.bottom-2,self.rect.w,2),border_radius=1)

player=Player()

# ═══════════════════════════════════════════════════════════════
#  BACKGROUND
# ═══════════════════════════════════════════════════════════════
PALETTES=[
    ((8,4,18),(50,35,110)),    # 0  Void
    ((4,14,4),(25,75,25)),     # 1  Forest
    ((18,4,4),(90,18,18)),     # 2  Fire
    ((4,18,28),(18,75,120)),   # 3  Ocean
    ((18,14,0),(95,75,0)),     # 4  Desert
    ((0,14,18),(0,65,85)),     # 5  Ice
    ((14,0,14),(65,0,65)),     # 6  Neon
    ((18,8,0),(85,38,0)),      # 7  Lava
    ((0,0,18),(0,0,95)),       # 8  Space
    ((14,14,14),(75,75,75)),   # 9  Glitch
    ((10,0,18),(48,0,95)),     # 10 Dream
    ((0,18,0),(0,95,0)),       # 11 Toxic
    ((18,0,9),(95,0,45)),      # 12 Blood Moon
    ((4,4,18),(22,22,95)),     # 13 Crystal
    ((18,4,0),(95,22,0)),      # 14 Volcanic
    ((0,18,18),(0,95,95)),     # 15 Cyber
    ((10,9,0),(58,55,0)),      # 16 Ruins
    ((14,0,4),(78,0,22)),      # 17 Nightmare
    ((0,4,14),(0,22,75)),      # 18 Abyss
    ((12,12,12),(180,180,200)),# 19 FINAL
]

class Background:
    def __init__(self):
        self.stars=[(random.randint(0,W),random.randint(0,H),
                     random.uniform(0.4,2.2),random.uniform(0,6.28)) for _ in range(220)]
        self.t=0
        # Pre-build scanline surface
        self.scanlines=pygame.Surface((W,H),pygame.SRCALPHA)
        for y in range(0,H,4):
            pygame.draw.line(self.scanlines,(0,0,0,10),(0,y),(W,y))

    def draw(self,surf,idx):
        self.t+=1
        c1,c2=PALETTES[idx%len(PALETTES)]
        # Gradient
        for y in range(0,H,2):
            c=lerpC(c1,c2,y/H)
            pygame.draw.rect(surf,c,(0,y,W,2))
        # Stars
        for sx,sy,ss,sp in self.stars:
            tw=(math.sin(self.t*0.035+sp)+1)/2
            br=int(80+170*tw)
            col=(br,br,min(255,br+50))
            r=max(1,int(ss*tw))
            pygame.draw.circle(surf,col,(sx,sy),r)
        # Scanlines
        surf.blit(self.scanlines,(0,0))

bg=Background()

# ═══════════════════════════════════════════════════════════════
#  LEVEL DATA — 20 worlds, massively expanded
# ═══════════════════════════════════════════════════════════════
PLAT_COLS=[
    (65,55,125),(48,95,55),(130,55,38),(45,95,155),
    (145,125,45),(45,135,155),(155,45,155),(155,95,38),
    (38,38,155),(95,95,95),(95,45,155),(45,155,45),
    (155,45,75),(55,55,175),(175,75,38),(38,175,175),
    (125,115,45),(135,38,55),(38,55,145),(190,190,190),
]
MSGS=[
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
    "FINAL WORLD. Transcend or be consumed.",
]

def P(*a,**k): return Platform(*a,**k)
def E(*a,**k): return Enemy(*a,**k)
def C(x,y): return Coin(x,y)

def build_level(idx):
    pc=PLAT_COLS[idx%len(PLAT_COLS)]
    dc=(195,28,28)

    def walls():
        return [P(0,H-28,W,28,pc),P(0,0,18,H,pc),P(W-18,0,18,H,pc)]

    platforms=[]; enemies=[]; coins=[]; start=(60,H-80); goal=(W-100,80)

    # ── WORLD 1 — Tutorial ──────────────────────────────────────
    if idx==0:
        platforms=walls()+[
            P(100,560,220,18,pc), P(370,490,200,18,pc),
            P(620,420,200,18,pc), P(880,350,200,18,pc),
            P(620,260,200,18,pc), P(370,170,200,18,pc),
            P(100,100,240,18,pc),
        ]
        enemies=[E(370,460,"patrol",(200,50,50),370,560,speed=2.5),
                 E(620,390,"patrol",(220,80,30),620,800,speed=3.0)]
        coins=[C(310,460),C(560,390),C(810,320),C(560,230),C(310,140)]
        start=(60,520); goal=(200,60)

    # ── WORLD 2 — Moving Platforms ──────────────────────────────
    elif idx==1:
        platforms=walls()+[
            P(80,560,160,18,pc),
            P(300,500,120,18,pc,moving=True,mx=1,mrange=80,mspeed=1.2),
            P(520,440,110,18,pc),
            P(700,375,100,18,pc,moving=True,mx=1,mrange=65,mspeed=1.9),
            P(870,310,180,18,pc),
            P(700,225,120,18,pc),
            P(460,160,200,18,pc),
            P(200,100,180,18,pc),
            P(400,545,55,18,dc,deadly=True),
            P(760,395,55,18,dc,deadly=True),
        ]
        enemies=[E(520,410,"patrol",(200,80,50),520,630,speed=3.2),
                 E(870,280,"patrol",(180,50,200),870,1050,speed=2.8)]
        coins=[C(460,475),C(660,350),C(400,130)]
        start=(50,530); goal=(260,60)

    # ── WORLD 3 — Orbit enemies ──────────────────────────────────
    elif idx==2:
        platforms=walls()+[
            P(80,560,140,18,pc),
            P(290,490,105,18,pc,moving=True,mx=1,mrange=100,mspeed=2.1),
            P(490,430,100,18,dc,deadly=True),
            P(650,378,145,18,pc),
            P(850,308,82,18,pc,moving=True,mx=1,mrange=85,mspeed=2.6),
            P(665,238,125,18,pc), P(440,178,105,18,pc),
            P(225,128,165,18,pc), P(50,78,210,18,pc),
            P(510,565,78,18,dc,deadly=True),
            P(760,565,78,18,dc,deadly=True),
        ]
        enemies=[E(650,348,"patrol",(230,60,60),650,780,speed=3.6),
                 E(440,148,"orbit",(180,60,230),ocx=440,ocy=178,orb_r=62,orb_spd=0.045)]
        coins=[C(400,460),C(700,300),C(380,100)]
        start=(50,530); goal=(110,45)

    # ── WORLD 4 — Phasing platforms ──────────────────────────────
    elif idx==3:
        platforms=walls()+[
            P(80,558,125,18,pc),
            P(265,488,82,18,pc,phase=True,phase_time=70),
            P(430,428,105,18,pc),
            P(595,358,82,18,pc,phase=True,phase_time=60),
            P(755,288,125,18,pc),
            P(935,218,82,18,pc,moving=True,mx=0,my=1,mrange=62,mspeed=2.1),
            P(735,148,145,18,pc), P(490,98,205,18,pc),
            P(245,128,145,18,pc), P(50,78,205,18,pc),
            P(355,575,105,18,dc,deadly=True),
            P(660,575,105,18,dc,deadly=True),
        ]
        enemies=[E(430,398,"patrol",(230,100,40),430,565,speed=4.1),
                 E(755,258,"orbit",(200,50,50),ocx=835,ocy=288,orb_r=82,orb_spd=0.052),
                 E(490,68,"patrol",(160,60,230),490,695,speed=3.6)]
        coins=[C(595,328),C(735,118),C(245,98)]
        start=(50,528); goal=(110,48)

    # ── WORLD 5 — Crumble + boost ────────────────────────────────
    elif idx==4:
        platforms=walls()+[
            P(80,558,105,18,pc),
            P(250,490,85,18,pc,crumble=True),
            P(420,430,85,18,pc,phase=True,phase_time=55),
            P(590,368,85,18,pc,boost=True),
            P(760,308,100,18,pc,moving=True,mx=0,my=1,mrange=75,mspeed=3.0),
            P(590,228,85,18,pc,phase=True,phase_time=50),
            P(420,168,85,18,pc,crumble=True),
            P(250,108,95,18,pc),
            P(80,88,185,18,pc),
            P(360,575,82,18,dc,deadly=True),
            P(615,575,82,18,dc,deadly=True),
            P(870,575,82,18,dc,deadly=True),
        ]
        enemies=[E(250,458,"patrol",(230,80,50),250,370,speed=4.1),
                 E(590,338,"orbit",(200,50,200),ocx=640,ocy=368,orb_r=72,orb_spd=0.065),
                 E(420,138,"patrol",(50,200,200),420,540,speed=4.6),
                 E(700,280,"sine",(200,155,50),px1=200,px2=900,ocy=280,orb_r=62,speed=3.1)]
        coins=[C(590,340),C(420,140),C(250,80)]
        start=(50,528); goal=(140,48)

    # ── WORLDS 6–19 — Procedural escalating horror ───────────────
    else:
        diff=(idx-5)/14.0
        random.seed(idx*7+13)
        steps=8+idx//3
        xs=[80]+[random.randint(120,W-220) for _ in range(steps-2)]+[W-200]
        ys=[H-80]
        for i in range(1,steps):
            ys.append(max(75,ys[-1]-random.randint(45,95)))

        platforms=walls()
        for i,(x,y) in enumerate(zip(xs,ys)):
            w=max(55,190-idx*6)
            is_d  =random.random()<diff*0.38
            is_m  =random.random()<diff*0.62
            is_ph =random.random()<diff*0.42
            is_cr =random.random()<diff*0.25 and not is_d and not is_m
            is_b  =random.random()<0.08 and not is_d
            c=dc if is_d else pc
            platforms.append(P(x,y,w,18,c,
                deadly=is_d,
                moving=(is_m and not is_d),
                mx=random.choice([-1,0,1]),my=random.choice([-1,0,1]),
                mrange=55+idx*5,mspeed=1.1+diff*3.2,
                phase=(is_ph and not is_d and not is_m),
                phase_time=max(22,78-idx*3),
                crumble=is_cr, boost=is_b))
            # Coin on platforms occasionally
            if random.random()<0.35 and not is_d:
                coins.append(C(x+w//2, y-20))

        for i in range(idx//2):
            sx=random.randint(100,W-200)
            platforms.append(P(sx,H-28,62,28,dc,deadly=True))

        enemy_count=3+idx//2
        for i in range(enemy_count):
            spd=2.8+diff*4.8
            ec=hsv(random.random(),0.85,1.0)
            etype=random.choices(
                ["patrol","orbit","chase","sine","zigzag","teleport"],
                weights=[3,2,2,2,1,max(0,idx-12)])[0]
            sv=max(1,int(1+diff*2))  # shooter hp scales
            si=max(35,110-idx*4) if idx>=8 and random.random()<0.4 else 0
            if etype=="patrol":
                ex=random.randint(160,W-160); ey=random.randint(210,H-100)
                enemies.append(E(ex,ey,"patrol",ec,px1=ex-130,px2=ex+130,speed=spd,shoot_iv=si,hp=sv))
            elif etype=="orbit":
                cx,cy=random.randint(320,W-320),random.randint(210,H-210)
                enemies.append(E(cx,cy,"orbit",ec,ocx=cx,ocy=cy,orb_r=65+idx*4,orb_spd=0.022+diff*0.065,shoot_iv=si))
            elif etype=="chase":
                ex=random.randint(210,W-210); ey=random.randint(110,H-210)
                enemies.append(E(ex,ey,"chase",ec,speed=spd*0.62,hp=sv))
            elif etype=="sine":
                ey=random.randint(210,H-210)
                enemies.append(E(210,ey,"sine",ec,px1=110,px2=W-110,ocy=ey,orb_r=65+idx*3,speed=spd*0.72,shoot_iv=si))
            elif etype=="zigzag":
                ey=random.randint(150,H-200)
                enemies.append(E(300,ey,"zigzag",ec,ocy=ey,orb_r=50+idx*3,speed=spd*0.9))
            elif etype=="teleport":
                enemies.append(E(400,300,"teleport",ec,hp=sv+1))

        start=(50,H-82); goal=(W-105,82)

    return platforms,enemies,coins,start,goal

# ═══════════════════════════════════════════════════════════════
#  HUD
# ═══════════════════════════════════════════════════════════════
def draw_hud(surf,idx,lives,tick,coins_total,coins_got):
    # ── top bar background ───────────────────────────────────────
    bar=pygame.Surface((W,64),pygame.SRCALPHA)
    bar.fill((0,0,0,110))
    surf.blit(bar,(0,0))

    # Lives (animated hearts)
    for i in range(5):
        filled=i<lives
        hx=W-168+i*30; hy=28
        c=(255,75,75) if filled else (55,55,70)
        pulse=1.0+(math.sin(tick*0.08+i)*0.1) if filled else 1.0
        r=int(11*pulse)
        heart_pts=[]
        for a in range(32):
            ang=a/32*math.tau
            x2=hx+r*math.sin(ang)*(1+0.28*math.cos(4*ang))
            y2=hy-r*math.cos(ang)*(1-0.28*abs(math.sin(ang)))
            heart_pts.append((x2,y2))
        if len(heart_pts)>=3:
            pygame.draw.polygon(surf,c,heart_pts)
            if filled:
                pygame.draw.polygon(surf,lerpC(c,(255,255,255),0.4),heart_pts,1)

    # World info
    name=MSGS[idx] if idx<len(MSGS) else "???"
    draw_text(surf,f"WORLD {idx+1:02d}/20",(W//2,8),
              hsv(tick*0.004%1,0.6,1.0),F_MD,center=True,shadow=True)
    draw_text(surf,name,(W//2,34),(180,180,220),F_TINY,center=True,shadow=True)

    # Stats top-left
    draw_text(surf,f"BEST W{SD['best']+1}",(24,8),(160,160,240),F_TINY,shadow=True)
    draw_text(surf,f"DEATHS {SD['deaths']}",(24,26),(200,100,100),F_TINY,shadow=True)

    # Coin counter
    cc=hsv(tick*0.008%1,0.9,1.0)
    draw_text(surf,f"◆ {coins_got}/{coins_total}",(24,44),cc,F_TINY,shadow=True)

    # Dash indicator (bottom)
    if player.dash_t==0:
        draw_text(surf,"DASH READY",(W-20,H-30),(100,255,200),F_TINY,shadow=True)
        # align right
        r2=F_TINY.render("DASH READY",True,(100,255,200))
        surf.blit(r2,(W-r2.get_width()-20,H-30))
    else:
        pct=1-(player.dash_t/35)
        bw=120; bx=W-bw-20; by=H-26
        pygame.draw.rect(surf,(40,40,60),(bx,by,bw,10),border_radius=5)
        pygame.draw.rect(surf,(100,255,200),(bx,by,int(bw*pct),10),border_radius=5)
        draw_text(surf,"DASH",(bx+bw//2,by-14),(100,200,160),F_TINY,center=True)

    # Controls hint
    draw_text(surf,"A/D Move  |  SPACE Jump  |  SHIFT Dash  |  ESC Pause",
              (W//2,H-16),(90,90,130),F_TINY,center=True,shadow=False)

def draw_hud(surf,idx,lives,tick,coins_total,coins_got):
    bar=pygame.Surface((W,64),pygame.SRCALPHA)
    bar.fill((0,0,0,115))
    surf.blit(bar,(0,0))
    for i in range(5):
        filled=i<lives
        hx=W-170+i*30; hy=28
        c=(255,75,75) if filled else (55,55,70)
        pulse=1.0+(math.sin(tick*0.08+i)*0.1) if filled else 1.0
        r=int(11*pulse)
        heart_pts=[]
        for a in range(32):
            ang=a/32*math.tau
            x2=hx+r*math.sin(ang)*(1+0.28*math.cos(4*ang))
            y2=hy-r*math.cos(ang)*(1-0.28*abs(math.sin(ang)))
            heart_pts.append((x2,y2))
        if len(heart_pts)>=3:
            pygame.draw.polygon(surf,c,heart_pts)
            if filled:
                pygame.draw.polygon(surf,lerpC(c,(255,255,255),0.4),heart_pts,1)
    name=MSGS[idx] if idx<len(MSGS) else "???"
    draw_text(surf,f"WORLD {idx+1:02d}/20",(W//2,8),
              hsv(tick*0.004%1,0.7,1.0),F_MD,center=True)
    draw_text(surf,name,(W//2,34),(180,180,220),F_TINY,center=True)
    draw_text(surf,f"BEST: W{SD['best']+1}",(24,8),(160,160,240),F_TINY)
    draw_text(surf,f"DEATHS: {SD['deaths']}",(24,26),(200,100,100),F_TINY)
    cc=hsv(tick*0.008%1,0.9,1.0)
    cstr=f"◆ {coins_got}/{coins_total}"
    draw_text(surf,cstr,(24,44),cc,F_TINY)
    # Dash bar
    bw=110; bx=W-bw-22; by=H-24
    if player.dash_t==0:
        pygame.draw.rect(surf,(100,255,200),(bx,by,bw,8),border_radius=4)
        draw_text(surf,"DASH",(bx+bw//2,by-16),(100,255,200),F_TINY,center=True)
    else:
        pct=1-(player.dash_t/35)
        pygame.draw.rect(surf,(30,30,50),(bx,by,bw,8),border_radius=4)
        pygame.draw.rect(surf,(60,180,140),(bx,by,int(bw*pct),8),border_radius=4)
        draw_text(surf,"DASH",(bx+bw//2,by-16),(80,140,110),F_TINY,center=True)
    draw_text(surf,"A/D:Move  SPACE:Jump  SHIFT:Dash  ESC:Pause",
              (W//2,H-16),(80,80,120),F_TINY,center=True,shadow=False)

# ═══════════════════════════════════════════════════════════════
#  SCREENS
# ═══════════════════════════════════════════════════════════════
def draw_menu(surf,idx):
    t=pygame.time.get_ticks()/1000.0
    for y in range(0,H,2):
        c=lerpC((4,0,12),(16,4,45),y/H)
        pygame.draw.rect(surf,c,(0,y,W,2))
    # Nebula blobs
    for i in range(4):
        nx=W//4*(i+0.5); ny=H//2+math.sin(t*0.3+i)*80
        nr=int(120+math.sin(t*0.2+i*1.5)*40)
        gc=(*hsv((t*0.04+i*0.25)%1,0.7,0.5),18)
        gls=pygame.Surface((nr*2,nr*2),pygame.SRCALPHA)
        pygame.draw.circle(gls,gc,(nr,nr),nr)
        surf.blit(gls,(nx-nr,ny-nr))
    # Glow behind title
    for ring in range(6,0,-1):
        gls=pygame.Surface((W,200),pygame.SRCALPHA)
        c=(*hsv((t*0.04)%1,0.85,1.0),12*ring)
        pygame.draw.ellipse(gls,c,(80,5,W-160,190))
        surf.blit(gls,(0,75))
    # Title
    c1=hsv(t*0.04%1,0.9,1.0); c2=hsv((t*0.04+0.18)%1,0.9,1.0)
    t1=F_TITLE.render("EMOTION",True,c1)
    t2=F_TITLE.render("ARCHITECT",True,c2)
    sub=F_LG.render("T R A N S C E N D E N T   E D I T I O N",True,(210,210,255))
    surf.blit(t1,(W//2-t1.get_width()//2,72))
    surf.blit(t2,(W//2-t2.get_width()//2,172))
    surf.blit(sub,(W//2-sub.get_width()//2,278))
    # Stats panel
    px=W//2-220; py=325
    panel=pygame.Surface((440,90),pygame.SRCALPHA)
    panel.fill((255,255,255,10))
    pygame.draw.rect(panel,(255,255,255,30),(0,0,440,90),2,border_radius=8)
    surf.blit(panel,(px,py))
    draw_text(surf,f"Current World: {idx+1} / 20",(W//2,335),(200,255,200),F_MD,center=True)
    draw_text(surf,f"Best: World {SD['best']+1}   Deaths: {SD['deaths']}   Runs: {SD['runs']}   Coins: {SD['coins']}",
              (W//2,365),(180,180,255),F_SM,center=True)
    draw_text(surf,"NEW: DASH (Shift) · Coyote Jump · Crumble Platforms · Shooters",
              (W//2,395),(140,200,180),F_TINY,center=True)
    # Buttons
    btn_play=pygame.Rect(W//2-130,430,260,58)
    btn_rst =pygame.Rect(W//2-130,502,260,46)
    for r in range(5,0,-1):
        bc=(*hsv(t*0.08%1,0.8,1.0),20)
        gs=pygame.Surface((btn_play.w+r*12,btn_play.h+r*12),pygame.SRCALPHA)
        pygame.draw.rect(gs,bc,(0,0,btn_play.w+r*12,btn_play.h+r*12),border_radius=16)
        surf.blit(gs,(btn_play.x-r*6,btn_play.y-r*6))
    pygame.draw.rect(surf,hsv(t*0.08%1,0.7,0.88),btn_play,border_radius=14)
    pygame.draw.rect(surf,(255,255,255,180),btn_play,2,border_radius=14)
    draw_text(surf,"► TRANSCEND",(btn_play.centerx,btn_play.centery),(0,0,0),F_LG,center=True)
    pygame.draw.rect(surf,(55,28,28),btn_rst,border_radius=10)
    pygame.draw.rect(surf,(140,45,45),btn_rst,2,border_radius=10)
    draw_text(surf,"RESET PROGRESS",(btn_rst.centerx,btn_rst.centery),(200,100,100),F_SM,center=True)
    draw_text(surf,"20 WORLDS · NO CHECKPOINTS · HARDCORE",
              (W//2,H-28),(110,75,75),F_TINY,center=True)
    return btn_play,btn_rst

def draw_gameover(surf):
    t=pygame.time.get_ticks()/1000.0
    for y in range(0,H,2):
        c=lerpC((28,0,0),(75,8,8),y/H)
        pygame.draw.rect(surf,c,(0,y,W,2))
    pulse=(math.sin(t*1.5)+1)/2
    c=lerpC((200,30,30),(255,60,60),pulse)
    txt=F_TITLE.render("GAME OVER",True,c)
    surf.blit(txt,(W//2-txt.get_width()//2,140))
    draw_text(surf,"The void has swallowed you whole.",(W//2,290),(220,145,145),F_MD,center=True)
    draw_text(surf,"All progress erased. All hope gone.",(W//2,328),(180,95,95),F_SM,center=True)
    draw_text(surf,f"You reached World {SD['best']+1}.",(W//2,368),(200,145,95),F_SM,center=True)
    btn=pygame.Rect(W//2-150,430,300,62)
    pygame.draw.rect(surf,(130,18,18),btn,border_radius=14)
    pygame.draw.rect(surf,(255,55,55),btn,2,border_radius=14)
    draw_text(surf,"RISE FROM NOTHING",(btn.centerx,btn.centery),(255,200,200),F_LG,center=True)
    return btn

def draw_win(surf):
    t=pygame.time.get_ticks()/1000.0
    for y in range(0,H,2):
        c=lerpC((4,4,18),(18,8,55),y/H)
        pygame.draw.rect(surf,c,(0,y,W,2))
    c=hsv(t*0.08%1,0.85,1.0)
    txt=F_TITLE.render("TRANSCENDED",True,c)
    surf.blit(txt,(W//2-txt.get_width()//2,110))
    draw_text(surf,"You have mastered the Emotion Architect.",(W//2,270),(220,220,255),F_MD,center=True)
    draw_text(surf,"20 worlds. Conquered. You are beyond human.",(W//2,312),(175,255,175),F_SM,center=True)
    draw_text(surf,f"Total Deaths: {SD['deaths']}   Coins: {SD['coins']}",(W//2,350),(200,200,255),F_SM,center=True)
    for _ in range(6):
        ps.emit(random.randint(0,W),random.randint(0,H),
                count=3,life=85,spread=5,color=hsv(random.random(),0.9,1.0),size=7,grav=-0.02)
    btn=pygame.Rect(W//2-130,420,260,58)
    pygame.draw.rect(surf,(25,75,25),btn,border_radius=14)
    pygame.draw.rect(surf,(100,255,100),btn,2,border_radius=14)
    draw_text(surf,"PLAY AGAIN",(btn.centerx,btn.centery),(200,255,200),F_LG,center=True)
    return btn

# ═══════════════════════════════════════════════════════════════
#  JOYSTICK
# ═══════════════════════════════════════════════════════════════
class Joystick:
    def __init__(self,x,y,r=52):
        self.base=(x,y); self.r=r
        self.stick=[float(x),float(y)]
        self.drag=False; self.dx=self.dy=0.0

    def handle(self,e):
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if math.hypot(e.pos[0]-self.base[0],e.pos[1]-self.base[1])<=self.r:
                self.drag=True
        elif e.type==pygame.MOUSEBUTTONUP and e.button==1:
            self.drag=False; self.stick=list(self.base); self.dx=self.dy=0.0
        elif e.type==pygame.MOUSEMOTION and self.drag:
            dx=e.pos[0]-self.base[0]; dy=e.pos[1]-self.base[1]
            d=math.hypot(dx,dy)
            if d>self.r: dx,dy=dx/d*self.r,dy/d*self.r
            self.stick=[self.base[0]+dx,self.base[1]+dy]
            self.dx,self.dy=dx/self.r,dy/self.r

    def draw(self,surf):
        gls=pygame.Surface((self.r*2+24,self.r*2+24),pygame.SRCALPHA)
        pygame.draw.circle(gls,(255,255,255,18),(self.r+12,self.r+12),self.r)
        pygame.draw.circle(gls,(255,255,255,55),(self.r+12,self.r+12),self.r,2)
        surf.blit(gls,(self.base[0]-self.r-12,self.base[1]-self.r-12))
        sx,sy=int(self.stick[0]),int(self.stick[1])
        sr=int(self.r*0.4)
        gs=pygame.Surface((sr*2+8,sr*2+8),pygame.SRCALPHA)
        pygame.draw.circle(gs,(255,255,255,175),(sr+4,sr+4),sr)
        surf.blit(gs,(sx-sr-4,sy-sr-4))

joy=Joystick(85,H-85)

# ═══════════════════════════════════════════════════════════════
#  MAIN GAME
# ═══════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.state="MENU"
        self.lives=5; self.tick=0
        self.platforms=[]; self.enemies=[]; self.coins=[]
        self.portal=None; self.start_pos=(60,H-80)
        self.flash_alpha=0; self.flash_color=(255,255,255)
        self.level_idx=SD["level"]
        self.coins_got=0
        self.score_popups=[]   # [(x,y,text,color,life)]
        self.load_level(self.level_idx)

    def load_level(self,idx):
        random.seed(idx*7+13)
        self.level_idx=idx
        self.platforms,self.enemies,self.coins,self.start_pos,goal=build_level(idx)
        self.portal=Portal(*goal)
        player.spawn(*self.start_pos)
        self.coins_got=0
        SD["best"]=max(SD.get("best",0),idx)
        save_game(SD)

    def flash(self,color=(255,255,255),strength=200):
        self.flash_alpha=strength; self.flash_color=color

    def popup(self,x,y,text,color=(255,255,100)):
        self.score_popups.append([x,y,text,color,50])

    def die(self):
        if player.invincible>0: return
        cam.hit(22,8)
        play(SND_DIE)
        ps.burst(player.rect.centerx,player.rect.centery,
                 count=35,color=(255,80,80),size=7)
        self.flash((255,40,40),230)
        SD["deaths"]+=1; save_game(SD)
        self.lives-=1
        if self.lives<=0:
            self.state="GAME_OVER"
            SD["level"]=0; SD["best"]=0; save_game(SD)
        else:
            player.spawn(*self.start_pos)

    def next_level(self):
        play(SND_WIN)
        cam.hit(10)
        self.flash((100,255,200),190)
        ps.burst(player.rect.centerx,player.rect.centery,
                 count=60,color=(100,255,200),size=6)
        nxt=self.level_idx+1
        if nxt>=20:
            self.state="WIN"
        else:
            SD["level"]=nxt; save_game(SD)
            self.load_level(nxt)

    def run(self):
        while True:
            self.tick+=1
            dt=clock.tick(FPS)

            # ── MENU ────────────────────────────────────────────
            if self.state=="MENU":
                screen.fill((0,0,0))
                btn_play,btn_rst=draw_menu(screen,self.level_idx)
                ps.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn_play.collidepoint(e.pos):
                            SD["runs"]+=1; save_game(SD); self.state="PLAY"
                        if btn_rst.collidepoint(e.pos):
                            SD.update({"level":0,"best":0,"deaths":0,"runs":0,"coins":0})
                            save_game(SD); self.level_idx=0; self.lives=5
                            self.load_level(0)
                    if e.type==pygame.KEYDOWN and e.key in (pygame.K_RETURN,pygame.K_SPACE):
                        SD["runs"]+=1; save_game(SD); self.state="PLAY"
                continue

            # ── GAME OVER ───────────────────────────────────────
            if self.state=="GAME_OVER":
                screen.fill((0,0,0))
                btn=draw_gameover(screen)
                ps.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn.collidepoint(e.pos):
                            SD.update({"level":0,"best":0,"deaths":0})
                            save_game(SD); self.lives=5; self.level_idx=0
                            self.load_level(0); self.state="MENU"
                continue

            # ── WIN ─────────────────────────────────────────────
            if self.state=="WIN":
                screen.fill((0,0,0))
                btn=draw_win(screen)
                ps.draw(screen)
                pygame.display.flip()
                for e in pygame.event.get():
                    if e.type==pygame.QUIT: sys.exit()
                    if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                        if btn.collidepoint(e.pos):
                            SD.update({"level":0,"best":0,"deaths":0,"runs":0})
                            save_game(SD); self.lives=5; self.level_idx=0
                            self.load_level(0); self.state="MENU"
                continue

            # ── PLAY ────────────────────────────────────────────
            # ── INPUT (KEYDOWN = instant jump, zero delay) ──────
            jump=False; dash=False
            for e in pygame.event.get():
                if e.type==pygame.QUIT: sys.exit()
                joy.handle(e)
                if e.type==pygame.KEYDOWN:
                    if e.key==pygame.K_ESCAPE: self.state="MENU"
                    # ▼▼ INSTANT JUMP — KEYDOWN fires the exact frame ▼▼
                    if e.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w): jump=True
                    if e.key in (pygame.K_LSHIFT,pygame.K_RSHIFT):       dash=True
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    if e.pos[1]<H//2: jump=True

            keys=pygame.key.get_pressed()
            dx=0.0
            if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx-=1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx+=1
            dx+=joy.dx

            # ── UPDATE ──────────────────────────────────────────
            for p in self.platforms: p.update()
            for c in self.coins:     c.update()
            player.update(self.platforms,dx,jump,dash)
            for en in self.enemies:
                en.update(player.rect.centerx,player.rect.centery)

            # Coin collection
            for c in self.coins:
                if c.check(player.rect):
                    self.coins_got+=1; SD["coins"]+=1
                    play(SND_COIN)
                    ps.burst(c.x,c.y,count=12,
                             color=hsv(self.tick*0.01%1,0.9,1.0),size=4)
                    self.popup(c.x,c.y-20,"+1 ◆",(255,220,80))

            # Deaths
            if player.rect.top>H: self.die()
            if player.check_deadly(self.platforms): self.die()
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

            # Portal
            self.portal.update()
            pr=pygame.Rect(self.portal.x-self.portal.r,self.portal.y-self.portal.r,
                           self.portal.r*2,self.portal.r*2)
            if player.rect.colliderect(pr):
                play(SND_PORTAL)
                self.next_level()

            # Ambient particles
            if self.tick%10==0:
                c1,c2=PALETTES[self.level_idx%len(PALETTES)]
                ps.emit(random.randint(0,W),H,count=1,vy=-0.9,life=220,
                        spread=0.4,color=c2,size=2,grav=-0.004,fade=True)

            # Score popups
            self.score_popups=[p for p in self.score_popups if p[4]>0]
            for p in self.score_popups:
                p[1]-=0.8; p[4]-=1

            # ── DRAW ────────────────────────────────────────────
            bg.draw(screen,self.level_idx)

            for p in self.platforms: p.draw(screen,self.tick)
            for c in self.coins:     c.draw(screen)
            for en in self.enemies:  en.draw(screen,self.tick)
            self.portal.draw(screen)
            player.draw(screen)
            ps.draw(screen)

            # Score popups
            for p in self.score_popups:
                a=int(255*(p[4]/50))
                draw_text(screen,p[2],(int(p[0]),int(p[1])),p[3],F_SM,center=True,alpha=a)

            # Flash
            if self.flash_alpha>0:
                fl=pygame.Surface((W,H),pygame.SRCALPHA)
                fl.fill((*self.flash_color,int(self.flash_alpha)))
                screen.blit(fl,(0,0))
                self.flash_alpha=max(0,self.flash_alpha-14)

            # HUD
            draw_hud(screen,self.level_idx,self.lives,self.tick,
                     len(self.coins),self.coins_got)
            joy.draw(screen)

            cam.update(); cam.apply(screen)
            pygame.display.flip()

# ═══════════════════════════════════════════════════════════════
#  LAUNCH
# ═══════════════════════════════════════════════════════════════
if __name__=="__main__":
    game=Game()
    game.run()
    pygame.quit()
    sys.exit()
