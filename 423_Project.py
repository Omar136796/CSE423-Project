from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

#General
fovY=120
GRID_LENGTH=900
max_border=(GRID_LENGTH-50)
cam_pos=(0,790,790)
border_height=200

#Game State variables
game_over=False
game_complete=False
cheat_mode=False
game_paused=False
bullet_miss_penalty=20
max_bullets_missed=20
missed_bullets_count=0
total_bullets_fired=0
score=0

#Level Variables
level=1
current_wave=1
enemies_remaining=0
enemy_health={}
wave_enemies=[]
wave_complete=False
level_complete=False
enemies_per_level=[2,3,4]
next_wave_timer=0
wave_spawn_delay=2.0
waves_per_level=2

#Vehicle Variables
heavy_vehicle=0        #Tank
medium_vehicle=1       #Jeep
light_vehicle=2        #Sports Car
current_vehicle=medium_vehicle
vehicle_colors=[(0.5,0.5,0.5),(0,0.4,0),(1,0,0)]    #Order Tank,Jeep,Sports car
vehicle_speed=[10,16,24]
vehicle_damage=[50,35,12.5]
vehicle_health=[1000,800,600]
vehicle_positions=[[0,0,0],[0,0,0],[0,0,0]]
vehicle_angles=[0,0,0]
bullets=[]
last_fire_time=[0,0,0]
fire_rates=[1,0.5,0.2]     #2 ta bullet er majher time gap
bullet_speeds=[30,40,50]
bullet_sizes=[16,10,6]

#Enemy Variables
forest_raider_positions=[]
arctic_assault_positions=[]
sandstorm_buggy_positions=[]
enemy_movement_timer=0
enemy_move_interval=0.2
enemy_speeds=[8.0,8.0,8.0]
enemy_bullets=[]
enemy_fire_interval_min=3.0
enemy_fire_interval_max=6.0
enemy_angles={}
enemy_next_fire_time={}
enemy_bullet_speed=30
enemy_shot_damage=50
enemy_scale_by_level={1:0.95,2:0.90,3:0.95}
enemy_bullet_radius_by_level={1:3.0,2:3.5,3:3.0}
enemy_muzzle_local={1:(0.0,-145.0,45.0),2:(0.0,-130.0,75.0),3:(0.0,-160.0,65.0)}

#Ground Items
landmine_positions=[]
landmine_count=3
ammo_box_positions=[]
medical_box_positions=[]
mine_damage=100
medical_box_heal=100
ammo_box_reduce_missed=2

#Obstacles
tree_positions=[]
snowman_positions=[]
sand_mountain_positions=[]
cactus_positions=[]

#Camera
win_w=1000
win_h=800
win_aspect=float(win_w)/float(win_h)
world_fovy=120.0
fp_fovy=90.0
chase_fovy=105.0
cam_world=0
cam_third_person=1
cam_first_person=2
cam_mode=cam_world
fp_eye_z=80.0
fp_look_dist=300.0
fp_fwd_tank=120.0
fp_fwd_jeep=95.0
fp_fwd_sports=110.0
fp_z_tank=160.0
fp_z_jeep=135.0
fp_z_sports=125.0
fp_center_z_tank=140.0
fp_center_z_jeep=120.0
fp_center_z_sports=115.0
chase_dist=420.0
chase_height=240.0
chase_look_ahead=260.0
chase_look_z=90.0

#Weather
weather=True
is_day_mode=False
sky_t=0.0
sky_transition_speed=0.35
last_sky_time=None
sky_w=1000
sky_h=800
sky_body_y=int(sky_h*0.45)
sky_moon_sun_x=int(sky_w*0.50)
sky_moon_sun_y=int(sky_h*0.62)
stars2d=[]
clouds3d=[]
cloud_count_3d=10
star_count_2d=220
night_mode=True
star_count=900
star_radius=4500
stars=[]
moon_pos=(0,GRID_LENGTH+1800,2000)
moon_r=220
snowflakes=[]
raindrops=[]
max_snowflakes=260
max_raindrops=420
snow_fall_speed_min=45.0
snow_fall_speed_max=85.0
snow_spiral_radius_min=6.0
snow_spiral_radius_max=20.0
snow_spin_speed_min=1.6
snow_spin_speed_max=3.4
rain_fall_speed_min=520.0
rain_fall_speed_max=720.0
rain_stick_length_min=26.0
rain_stick_length_max=44.0
rain_wind_angle=0.0
rain_wind_target=0.0
rain_wind_change_time=0.0

_QUADRIC=None
def get_quadric():
    global _QUADRIC
    if _QUADRIC is None:
        _QUADRIC=gluNewQuadric()
    return _QUADRIC

def update_sky_layout_from_window():
    global sky_w,sky_h,sky_body_y,sky_moon_sun_x,sky_moon_sun_y,win_w,win_h
    sky_w=win_w
    sky_h=win_h
    sky_body_y=int(sky_h*0.45)
    sky_moon_sun_x=int(sky_w*0.50)
    sky_moon_sun_y=int(sky_h*0.66)
    init_stars_2d()
    init_clouds_3d()
    init_snow()
    init_rain()

def reshape(w,h):
    global win_w,win_h,win_aspect
    if h==0:
        h=1
    win_w=int(w)
    win_h=int(h)
    win_aspect=float(win_w)/float(win_h)
    glViewport(0,0,win_w,win_h)
    update_sky_layout_from_window()

def update_max_border():
    global max_border,cam_mode
    if cam_mode==cam_first_person:
        max_border=(GRID_LENGTH-100)
    else:
        max_border=(GRID_LENGTH-50)

def draw_fp_weapon_only():
    vx=vehicle_positions[current_vehicle][0]
    vy=vehicle_positions[current_vehicle][1]
    vz=vehicle_positions[current_vehicle][2]
    ang=vehicle_angles[current_vehicle]
    ang_rad=math.radians(ang)
    fx=math.sin(ang_rad)
    fy=-math.cos(ang_rad)

    if current_vehicle==heavy_vehicle:
        base_fwd=110.0
        base_z=95.0
        barrel_len=140.0
        barrel_w=26.0
    elif current_vehicle==medium_vehicle:
        base_fwd=95.0
        base_z=105.0
        barrel_len=100.0
        barrel_w=12.0
    else:
        base_fwd=105.0
        base_z=90.0
        barrel_len=110.0
        barrel_w=10.0

    desired_tip_fwd=base_fwd+barrel_len
    tip_fwd=compute_safe_fp_forward(vx,vy,fx,fy,desired_tip_fwd,safe_margin=12.0)
    eff_barrel_len=max(2.0,min(barrel_len,tip_fwd))
    eff_base_fwd=max(0.0,tip_fwd-eff_barrel_len)
    bx=vx+fx*eff_base_fwd
    by=vy+fy*eff_base_fwd
    bz=vz+base_z

    glPushMatrix()
    glTranslatef(bx,by,bz)
    glRotatef(ang,0,0,1)

    if current_vehicle==heavy_vehicle:
        glColor3f(0.35,0.35,0.35)
    else:
        glColor3f(0.1,0.1,0.1)

    if current_vehicle!=light_vehicle:
        glPushMatrix()
        glTranslatef(0,-eff_barrel_len*0.5,0)
        glScalef(barrel_w,eff_barrel_len,barrel_w)
        glutSolidCube(1)
        glPopMatrix()
    else:
        for offx in (-10,10):
            glPushMatrix()
            glTranslatef(offx,-eff_barrel_len*0.5,0)
            glScalef(barrel_w,eff_barrel_len,barrel_w)
            glutSolidCube(1)
            glPopMatrix()

        glColor3f(0.8,0.0,0.0)
        glPushMatrix()
        glTranslatef(0,10,-5)
        glScalef(25,25,10)
        glutSolidCube(1)
        glPopMatrix()

    glPopMatrix()

def limiter(v):
    if v<0:return 0.0
    if v>1:return 1.0
    return v

def lerp(a,b,t):
    return a+(b-a)*t

def init_stars_2d():
    global stars2d
    stars2d=[]
    for _ in range(star_count_2d):
        if random.random()<0.65:
            y=random.randint(sky_body_y+5,int(sky_h*0.70))
        else:
            y=random.randint(int(sky_h*0.70),sky_h-5)
        x=random.randint(5,sky_w-5)
        size=random.choice([1,1,1,2,2,3])
        brightness=random.uniform(0.75,1.0)
        stars2d.append((x,y,size,brightness))

def init_clouds_3d():
    global clouds3d
    clouds3d=[]
    outside_margin=0.10
    outer=GRID_LENGTH*(1.0+outside_margin)
    tries=0
    while len(clouds3d)<cloud_count_3d and tries<12000:
        tries+=1
        x=random.uniform(-outer,outer)
        y=random.uniform(-outer,outer)
        z=random.uniform(560.0,840.0)
        scale=random.uniform(0.95,2.10)
        ok=True
        for c in clouds3d:
            dx=x-c["x"]
            dy=y-c["y"]
            min_d=(260.0*scale)+(260.0*c["scale"])
            if (dx*dx+dy*dy)<(min_d*min_d):
                ok=False
                break
        if ok:
            clouds3d.append({
                "x":x,
                "y":y,
                "z":z,
                "scale":scale,
                "seed":random.random()*1000.0
            })

def draw_cloud_shape_3d(cx,cy,cz,scale,t_day):
    q=get_quadric()
    night_c=0.72
    day_c=0.97
    c=night_c+(day_c-night_c)*t_day
    glColor3f(c,c,c)
    s=float(scale)
    r0=110.0*s
    rS=78.0*s
    off=95.0*s
    dz1=18.0*s
    dz2=10.0*s
    spheres=[
        (0.0,0.0,0.0,r0),
        (-off,0.0,dz1,rS),
        (off,0.0,dz2,rS),
        (0.0,-off,dz2,rS),
        (0.0,off,dz1,rS),
    ]
    for ox,oy,oz,rr in spheres:
        glPushMatrix()
        glTranslatef(cx+ox,cy+oy,cz+oz)
        gluSphere(q,rr,14,14)
        glPopMatrix()

def draw_clouds_3d():
    global sky_t
    if not clouds3d:
        return
    t_day=limiter(sky_t)
    for c in clouds3d:
        draw_cloud_shape_3d(c["x"],c["y"],c["z"],c["scale"],t_day)

FILLED_CIRCLE_CACHE={}

def get_filled_circle_offsets(r):
    global FILLED_CIRCLE_CACHE
    r=int(r)
    pts=FILLED_CIRCLE_CACHE.get(r)
    if pts is not None:
        return pts
    pts=[]
    rr=r*r
    for dy in range(-r,r+1):
        dx=int((rr-dy*dy)**0.5)
        for x in range(-dx,dx+1):
            pts.append((x,dy))
    FILLED_CIRCLE_CACHE[r]=pts
    return pts

def draw_filled_circle(cx,cy,r):
    pts=get_filled_circle_offsets(r)
    glBegin(GL_POINTS)
    for dx,dy in pts:
        glVertex2f(cx+dx,cy+dy)
    glEnd()

def draw_sun_2d(cx,cy,day_intensity):
    if day_intensity<=0.0:
        return
    r_outer=46
    r_mid=36
    r_inner=26
    glColor3f(1.00*day_intensity,0.62*day_intensity,0.00*day_intensity)
    draw_filled_circle(cx,cy,r_outer)
    glColor3f(1.00*day_intensity,0.78*day_intensity,0.20*day_intensity)
    draw_filled_circle(cx,cy,r_mid)
    glColor3f(1.00*day_intensity,0.92*day_intensity,0.30*day_intensity)
    draw_filled_circle(cx,cy,r_inner)

def draw_moon_2d(cx,cy,night_intensity):
    if night_intensity<=0.0:
        return
    R=30
    m=0.92*night_intensity
    glColor3f(m,m,m)
    draw_filled_circle(cx,cy,R)
    cut_r=0.03
    cut_g=0.04
    cut_b=0.08
    glColor3f(cut_r,cut_g,cut_b)
    cut_x=int(R*0.55)
    cut_y=int(R*0.05)
    draw_filled_circle(cx+cut_x,cy+cut_y,R)
    draw_filled_circle(cx+cut_x+1,cy+cut_y,R-2)

def draw_cloud_shape_2d(cx,cy,scale,intensity):
    if intensity<=0.0:
        return
    s=float(scale)
    r_grey=int(34*s)
    r_w1=int(46*s)
    r_w2=int(36*s)
    x_g,y_g=int(cx-42*s),int(cy-6*s)
    x_w1,y_w1=int(cx-8*s),int(cy+6*s)
    x_w2,y_w2=int(cx+44*s),int(cy)
    w=0.85+0.15*intensity
    g=0.75*w
    glColor3f(g,g,g)
    draw_filled_circle(x_g,y_g,r_grey)
    glColor3f(w,w,w)
    draw_filled_circle(x_w1,y_w1,r_w1)
    glColor3f(w,w,w)
    draw_filled_circle(x_w2,y_w2,r_w2)

def draw_sky_background_2d():
    global sky_t
    t=limiter(sky_t)
    night_intensity=1.0-t
    day_intensity=t
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0,sky_w,0,sky_h,-10.0,10.0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    top_r=lerp(0.02,0.35,t)
    top_g=lerp(0.03,0.70,t)
    top_b=lerp(0.08,0.95,t)
    bot_r=lerp(0.01,0.55,t)
    bot_g=lerp(0.02,0.82,t)
    bot_b=lerp(0.05,0.98,t)
    glBegin(GL_QUADS)
    glColor3f(bot_r,bot_g,bot_b)
    glVertex3f(0,0,0)
    glVertex3f(sky_w,0,0)
    glColor3f(top_r,top_g,top_b)
    glVertex3f(sky_w,sky_h,0)
    glVertex3f(0,sky_h,0)
    glEnd()
    if night_intensity>0.01:
        for (sx,sy,size,bright) in stars2d:
            glPointSize(size)
            b=bright*night_intensity
            glColor3f(b,b,b)
            glBegin(GL_POINTS)
            glVertex3f(sx,sy,0)
            glEnd()
            my=sky_body_y-(sy-sky_body_y)*0.60
            if 0<=my<=sky_body_y:
                glBegin(GL_POINTS)
                glVertex3f(sx,my,0)
                glEnd()
        glPointSize(1)
    draw_moon_2d(sky_moon_sun_x,sky_moon_sun_y,night_intensity)
    draw_sun_2d(sky_moon_sun_x,sky_moon_sun_y,day_intensity)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def vehicle_forward_vec_deg(angle_deg):
    ang=math.radians(angle_deg)
    fx=math.sin(ang)
    fy=-math.cos(ang)
    return fx,fy

def compute_safe_fp_forward(vx,vy,fx,fy,desired_fwd,safe_margin=8.0):
    limit=(GRID_LENGTH-safe_margin)
    t_max=desired_fwd
    if abs(fx)>1e-6:
        if fx>0:
            t_x=(limit-vx)/fx
        else:
            t_x=(-limit-vx)/fx
        t_max=min(t_max,t_x)
    if abs(fy)>1e-6:
        if fy>0:
            t_y=(limit-vy)/fy
        else:
            t_y=(-limit-vy)/fy
        t_max=min(t_max,t_y)
    if t_max<0.0:
        t_max=0.0
    return t_max

def compute_camera_for_mode():
    global cam_mode
    if cam_mode==cam_world:
        x,y,z=cam_pos
        return (x,y,z),(0,0,0),(0,0,1)
    vx=vehicle_positions[current_vehicle][0]
    vy=vehicle_positions[current_vehicle][1]
    vz=vehicle_positions[current_vehicle][2]
    ang=vehicle_angles[current_vehicle]
    fx,fy=vehicle_forward_vec_deg(ang)
    if cam_mode==cam_first_person:
        if current_vehicle==heavy_vehicle:
            fwd=fp_fwd_tank
            ez=fp_z_tank
            cz=fp_center_z_tank
        elif current_vehicle==medium_vehicle:
            fwd=fp_fwd_jeep
            ez=fp_z_jeep
            cz=fp_center_z_jeep
        else:
            fwd=fp_fwd_sports
            ez=fp_z_sports
            cz=fp_center_z_sports
        safe_fwd=compute_safe_fp_forward(vx,vy,fx,fy,fwd,safe_margin=10.0)
        eyeX=vx+fx*safe_fwd
        eyeY=vy+fy*safe_fwd
        eyeZ=ez
        centerX=eyeX+fx*fp_look_dist
        centerY=eyeY+fy*fp_look_dist
        centerZ=cz
        return (eyeX,eyeY,eyeZ),(centerX,centerY,centerZ),(0,0,1)
    eyeX=vx-fx*chase_dist
    eyeY=vy-fy*chase_dist
    eyeZ=chase_height
    centerX=vx+fx*chase_look_ahead
    centerY=vy+fy*chase_look_ahead
    centerZ=chase_look_z
    return (eyeX,eyeY,eyeZ),(centerX,centerY,centerZ),(0,0,1)

def transform_sky_towards_day():
    global last_sky_time,sky_t,game_paused
    if game_paused:
        return
    now=time.time()
    if last_sky_time is None:
        last_sky_time=now
    dt=now-last_sky_time
    last_sky_time=now
    target=1.0 if is_day_mode else 0.0
    if sky_t<target:
        sky_t=limiter(sky_t+sky_transition_speed*dt)
    elif sky_t>target:
        sky_t=limiter(sky_t-sky_transition_speed*dt)

def init_snow():
    global snowflakes
    snowflakes=[]
    for _ in range(max_snowflakes):
        snowflakes.append({
            'cx':random.uniform(-GRID_LENGTH,GRID_LENGTH),
            'cy':random.uniform(-GRID_LENGTH,GRID_LENGTH),
            'z':random.uniform(650.0,950.0),
            'radius':random.uniform(snow_spiral_radius_min,snow_spiral_radius_max),
            'angle':random.uniform(0.0,math.tau),
            'spin':random.uniform(snow_spin_speed_min,snow_spin_speed_max),
            'fall_speed':random.uniform(snow_fall_speed_min,snow_fall_speed_max),
            'size':random.uniform(2.0,5.0)
        })

def update_snow(dt):
    global game_paused
    if game_paused:
        return
    for s in snowflakes:
        s['angle']+=s['spin']*dt
        s['z']-=s['fall_speed']*dt
        if s['z']<=2.0:
            s['cx']=random.uniform(-GRID_LENGTH,GRID_LENGTH)
            s['cy']=random.uniform(-GRID_LENGTH,GRID_LENGTH)
            s['z']=random.uniform(650.0,950.0)
            s['radius']=random.uniform(snow_spiral_radius_min,snow_spiral_radius_max)
            s['angle']=random.uniform(0.0,math.tau)
            s['spin']=random.uniform(snow_spin_speed_min,snow_spin_speed_max)
            s['fall_speed']=random.uniform(snow_fall_speed_min,snow_fall_speed_max)
            s['size']=random.uniform(2.0,5.0)

def init_rain():
    global raindrops
    raindrops=[]
    for _ in range(max_raindrops):
        raindrops.append({
            'x':random.uniform(-GRID_LENGTH,GRID_LENGTH),
            'y':random.uniform(-GRID_LENGTH,GRID_LENGTH),
            'z':random.uniform(650.0,950.0),
            'speed':random.uniform(rain_fall_speed_min,rain_fall_speed_max),
            'length':random.uniform(rain_stick_length_min,rain_stick_length_max),
        })

def update_rain(dt):
    global game_paused
    if game_paused:
        return
    for r in raindrops:
        r['z']-=r['speed']*dt
        if r['z']<=0.0:
            r['x']=random.uniform(-GRID_LENGTH,GRID_LENGTH)
            r['y']=random.uniform(-GRID_LENGTH,GRID_LENGTH)
            r['z']=random.uniform(650.0,950.0)
            r['speed']=random.uniform(rain_fall_speed_min,rain_fall_speed_max)
            r['length']=random.uniform(rain_stick_length_min,rain_stick_length_max)

def draw_rain():
    glColor3f(0.70,0.85,1.00)
    glLineWidth(2.0)
    for r in raindrops:
        glBegin(GL_LINES)
        glVertex3f(r['x'],r['y'],r['z'])
        glVertex3f(r['x'],r['y'],r['z']-r['length'])
        glEnd()
    glLineWidth(1.0)

def draw_snow():
    if level==2:
        glColor3f(1.0,1.0,1.0)
    elif level==3:
        glColor3f(0.76,0.698,0.502)
    for s in snowflakes:
        x=s['cx']+math.cos(s['angle'])*s['radius']
        y=s['cy']+math.sin(s['angle'])*s['radius']
        glPushMatrix()
        glTranslatef(x,y,s['z'])
        gluSphere(get_quadric(),s['size'],8,8)
        glPopMatrix()

def draw_tank(color):
    glColor3f(*color)
    glPushMatrix()
    glScalef(100,160,40)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,50)
    glColor3f(0.4,0.4,0.4)
    glScalef(60,80,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-80,50)   #muzzle
    glColor3f(0.3,0.3,0.3)
    glScalef(10,100,10)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.2,0.2,0.2)
    glPushMatrix()
    glTranslatef(-60,0,-10)
    glScalef(10,170,20)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(60,0,-10)
    glScalef(10,170,20)
    glutSolidCube(1)
    glPopMatrix()
    for i in range(6):
        glPushMatrix()
        glTranslatef(-60,-70+i*28,-20)
        glColor3f(0.1,0.1,0.1)
        gluSphere(gluNewQuadric(),10,10,10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(60,-70+i*28,-20)
        glColor3f(0.1,0.1,0.1)
        gluSphere(gluNewQuadric(),10,10,10)
        glPopMatrix()

def draw_jeep(color):
    glColor3f(*color)
    glPushMatrix()
    glScalef(80,120,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,20,40)
    glColor3f(0.7,0.7,0.8)
    glScalef(70,60,10)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.3,0.3,0.3)
    glPushMatrix()
    glTranslatef(-30,50,50)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(30,50,50)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    wheel_positions=[(-50,-50,-20),(50,-50,-20),(-50,50,-20),(50,50,-20)]
    for pos in wheel_positions:
        glPushMatrix()
        glTranslatef(*pos)
        glColor3f(0.1,0.1,0.1)
        gluSphere(gluNewQuadric(),16,10,10)
        glPopMatrix()
    glColor3f(1.0,1.0,0.8)
    glPushMatrix()
    glTranslatef(-30,-70,10)
    gluSphere(gluNewQuadric(),6,10,10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(30,-70,10)
    gluSphere(gluNewQuadric(),6,10,10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,70)
    glColor3f(0.2,0.2,0.2)
    glPushMatrix()
    glScalef(20,20,5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.3,0.3,0.3)
    glPushMatrix()
    glTranslatef(0,0,10)
    glScalef(8,8,15)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-40,20)
    glColor3f(0.1,0.1,0.1)
    glScalef(6,80,6)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(15,0,15)
    glColor3f(0.4,0.4,0.0)
    glScalef(10,15,8)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()

def draw_sports_car(color):
    glColor3f(*color)
    glPushMatrix()
    glScalef(60,140,20)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,30,30)
    glRotatef(-30,1,0,0)
    glColor3f(0.7,0.7,0.9)
    glScalef(56,40,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,70,30)
    glColor3f(0.2,0.2,0.2)
    glScalef(40,4,10)
    glutSolidCube(1)
    glPopMatrix()
    wheel_positions=[(-40,-60,-16),(40,-60,-16),(-40,60,-16),(40,60,-16)]
    for pos in wheel_positions:
        glPushMatrix()
        glTranslatef(*pos)
        glColor3f(0.0,0.0,0.0)
        gluSphere(gluNewQuadric(),12,10,10)
        glPopMatrix()
    glColor3f(0.3,0.3,0.3)
    glPushMatrix()
    glTranslatef(-16,80,-10)
    glScalef(4,20,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(16,80,-10)
    glScalef(4,20,4)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1.0,1.0,0.9)
    glPushMatrix()
    glTranslatef(-20,-70,6)
    glScalef(2,8,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20,-70,6)
    glScalef(2,8,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,50)
    glColor3f(0.15,0.15,0.15)
    glPushMatrix()
    glScalef(15,15,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,10)
    glColor3f(0.25,0.25,0.25)
    glScalef(6,10,12)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-4,-35,18)
    glColor3f(0.1,0.1,0.1)
    glScalef(3,60,3)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(4,-35,18)
    glColor3f(0.1,0.1,0.1)
    glScalef(3,60,3)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,10,20)
    glColor3f(0.5,0.5,0.0)
    glScalef(8,15,6)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()

def draw_car():
    global current_vehicle,vehicle_positions,vehicle_angles,vehicle_colors
    pos=vehicle_positions[current_vehicle]
    angle=vehicle_angles[current_vehicle]
    color=vehicle_colors[current_vehicle]
    glPushMatrix()
    glTranslatef(pos[0],pos[1],pos[2])
    glRotatef(angle,0,0,1)
    if current_vehicle==heavy_vehicle:
        draw_tank(color)
    elif current_vehicle==medium_vehicle:
        draw_jeep(color)
    else:
        draw_sports_car(color)
    glPopMatrix()

def draw_forest_raider(x,y,z):
    glPushMatrix()
    glTranslatef(x,y,z)
    s=enemy_scale_by_level[1]
    glScalef(s,s,s)
    glColor3f(0.3,0.5,0.2)
    glPushMatrix()
    glScalef(70,110,25)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.4,0.3,0.2)
    glPushMatrix()
    glTranslatef(-25,40,30)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(30,40,30)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-25,-40,30)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(25,-40,30)
    glScalef(4,4,30)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,40,50)
    glScalef(50,4,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-40,50)
    glScalef(50,4,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-25,0,50)
    glScalef(4,80,4)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(25,0,50)
    glScalef(4,80,4)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.2,0.2,0.2)
    wheel_positions=[(-40,-60,-15),(40,-60,-15),(-40,60,-15),(40,60,-15)]
    for pos in wheel_positions:
        glPushMatrix()
        glTranslatef(*pos)
        gluSphere(gluNewQuadric(),12,10,10)
        glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-70,30)
    glColor3f(0.3,0.3,0.3)
    glPushMatrix()
    glScalef(20,20,5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.4,0.4,0.4)
    glPushMatrix()
    glTranslatef(0,0,10)
    glScalef(8,8,15)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.2,0.2,0.2)
    glPushMatrix()
    glTranslatef(0,-40,15)
    glScalef(5,70,5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.5,0.5,0.0)
    glPushMatrix()
    glTranslatef(12,0,15)
    glScalef(8,10,6)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()
    glColor3f(0.4,0.3,0.2)
    patches=[(-20,20,15),(20,-20,15),(-15,-30,15),(25,30,15)]
    for patch in patches:
        glPushMatrix()
        glTranslatef(*patch)
        glScalef(15,20,1)
        glutSolidCube(1)
        glPopMatrix()
    glPopMatrix()

def draw_arctic_assault_vehicle(x,y,z):
    glPushMatrix()
    glTranslatef(x,y,z)
    s=enemy_scale_by_level[2]
    glScalef(s,s,s)
    glColor3f(0.9,0.95,1.0)
    glPushMatrix()
    glScalef(90,140,35)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.7,0.7,0.8)
    glPushMatrix()
    glTranslatef(0,80,-5)
    glScalef(60,10,15)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.2,0.2,0.2)
    glPushMatrix()
    glTranslatef(-55,0,-10)
    glScalef(10,150,25)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(55,0,-10)
    glScalef(10,150,25)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.15,0.15,0.15)
    for i in range(5):
        glPushMatrix()
        glTranslatef(-55,-50+i*25,-20)
        gluSphere(gluNewQuadric(),8,10,10)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(55,-50+i*25,-20)
        gluSphere(gluNewQuadric(),8,10,10)
        glPopMatrix()
    glColor3f(0.8,0.85,0.9)
    glPushMatrix()
    glTranslatef(0,-20,50)
    glScalef(50,40,20)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-80,50)
    glColor3f(0.3,0.3,0.3)
    glPushMatrix()
    glScalef(30,30,8)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.4,0.4,0.4)
    glPushMatrix()
    glTranslatef(0,0,15)
    glScalef(15,20,20)
    glutSolidCube(1)
    glPopMatrix()
    tube_positions=[(-8,-25,25),(0,-25,25),(8,-25,25)]
    for tube_x in tube_positions:
        glPushMatrix()
        glTranslatef(tube_x[0],tube_x[1],tube_x[2])
        glColor3f(0.6,0.6,0.6)
        glPushMatrix()
        glScalef(4,50,4)
        glutSolidCube(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0,-35,0)
        glColor3f(1.0,0.0,0.0)
        gluSphere(gluNewQuadric(),5,8,8)
        glPopMatrix()
        glPopMatrix()
    glColor3f(0.95,0.98,1.0)
    snow_patches=[(-30,50,20),(30,-40,20),(-25,-30,20),(35,35,20)]
    for patch in snow_patches:
        glPushMatrix()
        glTranslatef(*patch)
        glScalef(8,8,2)
        gluSphere(gluNewQuadric(),1,6,6)
        glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def draw_sandstorm_buggy(x,y,z):
    glPushMatrix()
    glTranslatef(x,y,z)
    s=enemy_scale_by_level[3]
    glScalef(s,s,s)
    glColor3f(0.45,0.35,0.25)
    glPushMatrix()
    glScalef(80,130,20)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.65,0.55,0.45)
    suspension_positions=[(-35,-60,10),(35,-60,10),(-35,60,10),(35,60,10)]
    for pos in suspension_positions:
        glPushMatrix()
        glTranslatef(*pos)
        glScalef(5,5,15)
        glutSolidCube(1)
        glPopMatrix()
    glColor3f(0.15,0.15,0.15)
    wheel_positions=[(-40,-60,-20),(40,-60,-20),(-40,60,-20),(40,60,-20)]
    for pos in wheel_positions:
        glPushMatrix()
        glTranslatef(*pos)
        gluSphere(gluNewQuadric(),18,12,12)
        glPopMatrix()
    glColor3f(0.45,0.35,0.25)
    glPushMatrix()
    glTranslatef(0,-40,20)
    glScalef(70,40,5)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.5,0.5,0.5)
    cans=[(-45,50,15),(45,50,15),(-45,-50,15),(45,-50,15)]
    for can in cans:
        glPushMatrix()
        glTranslatef(*can)
        glScalef(6,6,10)
        glutSolidCube(1)
        glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-70,45)
    glColor3f(0.25,0.25,0.25)
    glPushMatrix()
    glScalef(25,25,6)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.35,0.35,0.35)
    glPushMatrix()
    glTranslatef(0,0,10)
    glScalef(10,10,12)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.45,0.35,0.25)
    glPushMatrix()
    glTranslatef(0,0,25)
    glScalef(25,5,20)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.2,0.2,0.2)
    glPushMatrix()
    glTranslatef(0,-50,20)
    glScalef(6,80,6)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.6,0.55,0.45)
    glPushMatrix()
    glTranslatef(15,-10,15)
    glScalef(12,30,8)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()
    glColor3f(0.6,0.52,0.42)
    glPushMatrix()
    glTranslatef(0,70,25)
    glutSolidCube(40)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(45,0,25)
    glutSolidCube(30)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-45,0,25)
    glutSolidCube(30)
    glPopMatrix()
    glColor3f(0.7,0.65,0.55)
    dust_patches=[(-30,40,25),(30,-40,25),(-20,-50,25),(25,50,25)]
    for patch in dust_patches:
        glPushMatrix()
        glTranslatef(*patch)
        glScalef(10,10,2)
        gluSphere(gluNewQuadric(),1,6,6)
        glPopMatrix()
    glPopMatrix()

def draw_enemies():
    if not wave_enemies:
        return
    if level==1:
        for pos in wave_enemies:
            if enemy_health.get(pos,0)>0:    #shudhu beche ase emon enemy draw
                glPushMatrix()
                glTranslatef(pos[0],pos[1],pos[2])
                glRotatef(enemy_angles.get(pos,0),0,0,1)
                draw_forest_raider(0,0,0)
                glPopMatrix()
    elif level==2:
        for pos in wave_enemies:
            if enemy_health.get(pos,0)>0:
                glPushMatrix()
                glTranslatef(pos[0],pos[1],pos[2])
                glRotatef(enemy_angles.get(pos,0),0,0,1)
                draw_arctic_assault_vehicle(0,0,0)
                glPopMatrix()
    elif level==3:
        for pos in wave_enemies:
            if enemy_health.get(pos,0)>0:
                glPushMatrix()
                glTranslatef(pos[0],pos[1],pos[2])
                glRotatef(enemy_angles.get(pos,0),0,0,1)
                draw_sandstorm_buggy(0,0,0)
                glPopMatrix()

def draw_bullets():
    for bullet in bullets[:]:
        glPushMatrix()
        glTranslatef(bullet['x'],bullet['y'],bullet['z'])
        if bullet['vehicle_type']==heavy_vehicle:
            glColor3f(1,0,0)
        elif bullet['vehicle_type']==medium_vehicle:
            glColor3f(1,0,0)
        else:
            glColor3f(1,0,0)
        gluSphere(gluNewQuadric(),bullet['size'],8,8)
        glPopMatrix()

def update_bullets():
    global missed_bullets_count,score,total_bullets_fired,game_over,cheat_mode,game_paused
    if game_paused:
        return
    current_time=time.time()
    for bullet in bullets[:]:
        new_x=bullet['x']+bullet['dx']*bullet_speeds[bullet['vehicle_type']]
        new_y=bullet['y']+bullet['dy']*bullet_speeds[bullet['vehicle_type']]
        bullet_hit=False
        hit_enemy=False
        for enemy_pos in wave_enemies[:]:
            if enemy_health.get(enemy_pos,0)>0:
                enemy_x,enemy_y,enemy_z=enemy_pos
                enemy_radius=get_enemy_radius(level)
                distance=math.sqrt((new_x-enemy_x)**2+(new_y-enemy_y)**2)
                if distance<bullet['size']+enemy_radius:
                    damage=vehicle_damage[bullet['vehicle_type']]
                    enemy_health[enemy_pos]-=damage
                    bullet_hit=True
                    hit_enemy=True
                    break
        if not bullet_hit:
            if not cheat_mode:
                if check_bullet_collision(new_x,new_y,bullet['size']):
                    bullet_hit=True
                    missed_bullets_count+=1
                    score=max(0,score-bullet_miss_penalty)
                    if missed_bullets_count>=max_bullets_missed:
                        game_over=True
        if bullet_hit:
            bullets.remove(bullet)
            continue
        bullet['x']=new_x
        bullet['y']=new_y
        if (abs(bullet['x'])>GRID_LENGTH+100 or
            abs(bullet['y'])>GRID_LENGTH+100 or
            bullet['z']<0 or bullet['z']>500):
            if not cheat_mode:
                missed_bullets_count+=1
                score=max(0,score-bullet_miss_penalty)
                if missed_bullets_count>=max_bullets_missed:
                    game_over=True
            bullets.remove(bullet)
            continue

def fire_bullet():
    global last_fire_time,bullets,total_bullets_fired,game_paused
    if game_paused==True:
        return
    
    current_time=time.time()
    vehicle_type=current_vehicle
    if (current_time-last_fire_time[vehicle_type])<fire_rates[vehicle_type]:   #2 ta fire er moddhe enough time hoise naki
        return
    
    last_fire_time[vehicle_type]=current_time
    total_bullets_fired+=1
    pos=vehicle_positions[current_vehicle]
    angle=vehicle_angles[current_vehicle]
    angle_rad=math.radians(angle)
    dx=math.sin(angle_rad)
    dy=-math.cos(angle_rad)          #vehicle er nozzle -y axis e;y er component sin(theta)

    if vehicle_type==heavy_vehicle:

        nozzle_offset_x=0                    #Line 632;Tank er nozzle position
        nozzle_offset_y=-80
        nozzle_offset_z=50

        rotated_x=(nozzle_offset_x*math.cos(angle_rad))-(nozzle_offset_y*math.sin(angle_rad))   #vehicle er sathe jate nozzle o nore
        rotated_y=(nozzle_offset_x*math.sin(angle_rad))+(nozzle_offset_y*math.cos(angle_rad))   #rotation formula 

        bullet_x=pos[0]+rotated_x
        bullet_y=pos[1]+rotated_y
        bullet_z=pos[2]+nozzle_offset_z

        bullets.append({'x':bullet_x,'y':bullet_y,'z':bullet_z,'dx':dx,'dy':dy,'size':bullet_sizes[vehicle_type],'vehicle_type':vehicle_type,'creation_time':current_time})
    elif vehicle_type==medium_vehicle:

        nozzle_offset_x=0
        nozzle_offset_y=-40
        nozzle_offset_z=70

        rotated_x=(nozzle_offset_x*math.cos(angle_rad))-(nozzle_offset_y*math.sin(angle_rad))
        rotated_y=(nozzle_offset_x*math.sin(angle_rad))+(nozzle_offset_y*math.cos(angle_rad))

        bullet_x=pos[0]+rotated_x
        bullet_y=pos[1]+rotated_y
        bullet_z=pos[2]+nozzle_offset_z

        bullets.append({'x':bullet_x,'y':bullet_y,'z':bullet_z,'dx':dx,'dy':dy,'size':bullet_sizes[vehicle_type],'vehicle_type':vehicle_type,'creation_time':current_time})
    else:
        two_barrels=[(-4,-35,50),(4,-35,50)]     #sports car e 2 ta barrel

        for barrel in two_barrels:
            nozzle_offset_x,nozzle_offset_y,nozzle_offset_z=barrel
            rotated_x=(nozzle_offset_x*math.cos(angle_rad))-(nozzle_offset_y*math.sin(angle_rad))
            rotated_y=(nozzle_offset_x*math.sin(angle_rad))+(nozzle_offset_y*math.cos(angle_rad))

            bullet_x=pos[0]+rotated_x
            bullet_y=pos[1]+rotated_y
            bullet_z=pos[2]+nozzle_offset_z

            bullets.append({'x':bullet_x,'y':bullet_y,'z':bullet_z,'dx':dx,'dy':dy,'size':bullet_sizes[vehicle_type],'vehicle_type':vehicle_type,'creation_time':current_time})
        total_bullets_fired+=1

def get_enemy_weapon_nozzle_position(enemy_x, enemy_y, enemy_z, level, enemy_angle):
    angle_rad=math.radians(enemy_angle)
    mx,my,mz=enemy_muzzle_local[level] # level wise enemy er muzzle position
    s=enemy_scale_by_level[level]

    mx*=s
    my*=s
    mz*=s

    rotated_x=(mx*math.cos(angle_rad))-(my*math.sin(angle_rad))
    rotated_y=(mx*math.sin(angle_rad))+(my*math.cos(angle_rad))

    bullet_x=enemy_x+rotated_x
    bullet_y=enemy_y+rotated_y
    bullet_z=enemy_z+mz
    
    return bullet_x, bullet_y, bullet_z

def get_enemy_radius(level):
    if level==1:
        return 60
    elif level==2:
        return 70
    else:
        return 65

def get_angle_to_player(enemy_x,enemy_y,player_x,player_y):
    dx=player_x-enemy_x
    dy=player_y-enemy_y
    angle_rad=math.atan2(dx,-dy)
    angle_deg=math.degrees(angle_rad)
    if angle_deg<0:
        angle_deg+=360
    return angle_deg

def rotate_enemy_toward_angle(enemy_pos,target_angle,rotation_speed=10.0):
    current_angle=enemy_angles.get(enemy_pos,0)
    angle_diff=(target_angle-current_angle)%360
    if angle_diff>180:
        angle_diff-=360
    if abs(angle_diff)<rotation_speed:
        new_angle=target_angle
    else:                          #target er dike rotate korbe
        new_angle=current_angle+(rotation_speed if angle_diff>0 else -rotation_speed)
    enemy_angles[enemy_pos]=(new_angle%360)
    return new_angle

def update_enemy_position(old_pos,new_pos,angle):
    if old_pos in enemy_health:
        health=enemy_health.pop(old_pos)
        enemy_health[new_pos]=health
    if old_pos in enemy_angles:
        enemy_angles[new_pos]=angle
        enemy_angles.pop(old_pos)
        enemy_angles[new_pos]=angle
    if old_pos in enemy_next_fire_time:
        fire_time=enemy_next_fire_time.pop(old_pos)
        enemy_next_fire_time[new_pos]=fire_time
    if old_pos in wave_enemies:
        index=wave_enemies.index(old_pos)
        wave_enemies[index]=new_pos

def is_enemy_position_valid(x,y,original_enemy_pos):
    enemy_radius=get_enemy_radius(level)
    if not (-max_border<=x<=max_border and -max_border<=y<=max_border):
        return False
    
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<(enemy_radius+tree_radius):
                return False
            
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<(enemy_radius+snowman_radius):
                return False
            
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<(enemy_radius+base_radius):
                return False
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<(enemy_radius+cactus_radius):
                return False
            
    player_pos=vehicle_positions[current_vehicle]    #player er sathe collision
    player_radius=50
    distance_to_player=math.sqrt((x-player_pos[0])**2+(y-player_pos[1])**2)
    if distance_to_player<enemy_radius+player_radius:
        return False
    
    for enemy_pos in wave_enemies:                   #enemy er sathe collision
        if enemy_pos==original_enemy_pos: #nije baad e
            continue
        if enemy_health.get(enemy_pos,0)>0:
            other_x,other_y,_=enemy_pos
            other_radius=get_enemy_radius(level)
            distance=math.sqrt((x-other_x)**2+(y-other_y)**2)
            if distance<(enemy_radius+other_radius):
                return False
    return True

def move_enemies():
    global enemy_movement_timer,game_paused
    
    if game_paused==True:
        return
    
    current_time=time.time()
    if (current_time-enemy_movement_timer)<enemy_move_interval:   #enemy 0.2s por por norbe
        return
    
    enemy_movement_timer=current_time
    player_pos=vehicle_positions[current_vehicle]
    player_x,player_y=player_pos[0],player_pos[1]
    for enemy_pos in wave_enemies[:]:
        if enemy_health.get(enemy_pos,0)<=0:
            continue                             #dead enemy gula skip
        enemy_x,enemy_y,enemy_z=enemy_pos
        distance_to_player=math.sqrt((enemy_x-player_x)**2+(enemy_y-player_y)**2)
        desired_angle=get_angle_to_player(enemy_x,enemy_y,player_x,player_y)
        current_angle=rotate_enemy_toward_angle(enemy_pos,desired_angle,rotation_speed=10.0)
        enemy_speed=enemy_speeds[level-1]      #enemy_speeds=[8.0,8.0,8.0]
        move_successful=False
        movement_attempts=[(current_angle,enemy_speed),((current_angle+45)%360,enemy_speed*0.8),((current_angle-45)%360,enemy_speed*0.8),((current_angle+90)%360,enemy_speed*0.6),((current_angle-90)%360,enemy_speed*0.6),((current_angle+180)%360,enemy_speed*0.5),(random.uniform(0,360),enemy_speed*0.7),(random.uniform(0,360),enemy_speed*0.7)]

        #8 type er movement attempt:1.Direct path,2.45° right,3.45° left,90° right,90° left,6.Reverse,7.Random 1,8.Random 2

        for attempt_angle,attempt_speed in movement_attempts:
            if move_successful:
                break
            angle_rad=math.radians(attempt_angle)
            if distance_to_player>200:           #jodi player theke dure thake shamne agabe
                move_x=math.sin(angle_rad)*attempt_speed
                move_y=-math.cos(angle_rad)*attempt_speed
                new_x=enemy_x+move_x
                new_y=enemy_y+move_y
            elif distance_to_player<150:         #jodi beshi kase ashe pisabe
                move_x=-math.sin(angle_rad)*(attempt_speed*0.5)
                move_y=math.cos(angle_rad)*(attempt_speed*0.5)
                new_x=enemy_x+move_x
                new_y=enemy_y+move_y
            else:                                 #optimal distance e thakle daray thakbe
                new_x=enemy_x
                new_y=enemy_y
                if attempt_angle==current_angle:
                    move_successful=True
                    continue
            if is_enemy_position_valid(new_x,new_y,enemy_pos):         #new position valid naki check
                enemy_angles[enemy_pos]=attempt_angle
                update_enemy_position(enemy_pos,(new_x,new_y,enemy_z),attempt_angle)
                move_successful=True
                break
        if not move_successful:                     #valid position na paile player er dike face kore thakbe
            enemy_angles[enemy_pos]=desired_angle

def enemy_fire():
    global enemy_next_fire_time, level, game_paused
    if game_paused==True:
        return
    
    current_time=time.time()
    player_pos=vehicle_positions[current_vehicle]
    player_x,player_y=player_pos[0],player_pos[1]

    for enemy_pos in wave_enemies[:]:
        if enemy_health.get(enemy_pos, 0)<=0: #dead enemy hoile shoot korbe na
            continue
        if current_time<enemy_next_fire_time.get(enemy_pos, 0):    #last shot theke enough time na hoile
            continue

        enemy_x,enemy_y,enemy_z=enemy_pos
        enemy_angle=enemy_angles.get(enemy_pos, 0)
        angle_to_player=get_angle_to_player(enemy_x,enemy_y,player_x,player_y)
        angle_diff = abs((angle_to_player-enemy_angle)%360)

        if angle_diff>180:
            angle_diff=(360-angle_diff)

        distance_to_player=math.sqrt((enemy_x-player_x)**2+(enemy_y-player_y)**2)

        if angle_diff<=30 and distance_to_player<=800:       #fire korar condition
            bullet_x,bullet_y,bullet_z=get_enemy_weapon_nozzle_position(enemy_x,enemy_y,enemy_z,level,enemy_angle)
            angle_rad=math.radians(enemy_angle)
            dir_x=math.sin(angle_rad)
            dir_y=-math.cos(angle_rad)

            # level wise bullet creat
            if level==1:
                enemy_bullets.append({'x': bullet_x, 'y': bullet_y, 'z': bullet_z, 'dx': dir_x, 'dy': dir_y, 'size': enemy_bullet_radius_by_level[1], 'creation_time': current_time, 'damage': 5})
            
            elif level==2:
                enemy_bullets.append({'x': bullet_x, 'y': bullet_y, 'z': bullet_z, 'dx': dir_x, 'dy': dir_y, 'size': enemy_bullet_radius_by_level[2], 'creation_time': current_time, 'damage': 7})
            else:
                enemy_bullets.append({'x': bullet_x, 'y': bullet_y, 'z': bullet_z, 'dx': dir_x, 'dy': dir_y, 'size': enemy_bullet_radius_by_level[3], 'creation_time': current_time, 'damage': 10})
            
            enemy_next_fire_time[enemy_pos]=current_time +random.uniform(enemy_fire_interval_min*0.5, enemy_fire_interval_max*0.5)

def draw_enemy_bullets():
    for bullet in enemy_bullets[:]:
        glPushMatrix()
        glTranslatef(bullet['x'],bullet['y'],bullet['z'])
        glColor3f(1,0,1)
        gluSphere(gluNewQuadric(),bullet['size'],8,8)
        glPopMatrix()

def update_enemy_bullets():
    global current_vehicle,game_over,vehicle_health,vehicle_positions,vehicle_angles,cheat_mode,game_paused
    if game_paused:
        return
    current_time=time.time()
    for bullet in enemy_bullets[:]:
        bullet['x']+=bullet['dx']*enemy_bullet_speed
        bullet['y']+=bullet['dy']*enemy_bullet_speed
        player_pos=vehicle_positions[current_vehicle]
        player_radius=50
        distance=math.sqrt((bullet['x']-player_pos[0])**2+
                            (bullet['y']-player_pos[1])**2)
        if distance<bullet['size']+player_radius:
            if not cheat_mode:
                vehicle_health[current_vehicle]-=enemy_shot_damage
                if vehicle_health[current_vehicle]<=0:
                    vehicle_health[current_vehicle]=0
                    for i in range(3):
                        if vehicle_health[i]>0:
                            current_x,current_y,current_z=vehicle_positions[current_vehicle]
                            current_angle=vehicle_angles[current_vehicle]
                            current_vehicle=i
                            vehicle_positions[current_vehicle]=[current_x,current_y,current_z]
                            vehicle_angles[current_vehicle]=current_angle
                            break
                    else:
                        game_over=True
            enemy_bullets.remove(bullet)
            continue
        if check_enemy_bullet_collision(bullet['x'],bullet['y'],bullet['size']):
            enemy_bullets.remove(bullet)
            continue
        if (abs(bullet['x'])>GRID_LENGTH+100 or
            abs(bullet['y'])>GRID_LENGTH+100 or
            bullet['z']<0 or bullet['z']>500):
            enemy_bullets.remove(bullet)
        elif current_time-bullet['creation_time']>8:
            enemy_bullets.remove(bullet)

def check_enemy_bullet_collision(x,y,radius):
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<radius+tree_radius:
                return True
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<radius+snowman_radius:
                return True
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<radius+base_radius:
                return True
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<radius+cactus_radius:
                return True
    return False

def init_wave_enemies():
    global wave_enemies,enemies_remaining,enemy_health,wave_complete,next_wave_timer,enemy_angles,enemy_next_fire_time
    
    #Ager shob wave er data clear
    wave_enemies=[]
    enemy_health={}
    enemy_angles={}
    enemy_next_fire_time={}
    wave_complete=False
    next_wave_timer=0
    num_enemies=enemies_per_level[level-1]  #enemies_per_level=[2,3,4] for levels 1,2,3
    enemies_remaining=num_enemies 

    for i in range(num_enemies):
        position_found=False
        attempts=0
        while not (position_found) and attempts<100:
            x=random.randint(-GRID_LENGTH+400,GRID_LENGTH-400)
            y=random.randint(-GRID_LENGTH+400,GRID_LENGTH-400)
            if (is_position_valid(x,y,enemy_type="enemy") and not (is_too_close_to_player(x,y))):   #jate player theke min 400 distance e thake
                too_close=False
                for enemy in wave_enemies:
                    dist=math.sqrt((x-enemy[0])**2+(y-enemy[1])**2)
                    if dist<250:                                      #2 ta enemy er moddhe min distance 250
                        too_close=True
                        break
                if not too_close:
                    if level==1:
                        enemy_z=50       #enemy height
                    elif level==2:
                        enemy_z=60
                    else:
                        enemy_z=55

                    enemy_pos=(x,y,enemy_z)
                    wave_enemies.append(enemy_pos)
                    enemy_angles[enemy_pos]=random.uniform(0,360)  #random dike face kore thakbe
                    enemy_health[enemy_pos]=100
                    enemy_next_fire_time[enemy_pos]=time.time()+random.uniform(0,enemy_fire_interval_max)  #2 ta fire er time diff
                    position_found=True

            attempts+=1
        if not position_found:  #jodi valid pos na pai taile corner e rakhbo
            corner_positions=[(-GRID_LENGTH+500,-GRID_LENGTH+500),(GRID_LENGTH-500,-GRID_LENGTH+500),(-GRID_LENGTH+500,GRID_LENGTH-500),(GRID_LENGTH-500,GRID_LENGTH-500)]
            corner=corner_positions[i%len(corner_positions)]
            if level==1:
                enemy_z=50
            elif level==2:
                enemy_z=60
            else:
                enemy_z=55
            enemy_pos=(corner[0],corner[1],enemy_z)
            wave_enemies.append(enemy_pos)
            enemy_angles[enemy_pos]=random.uniform(0,360)
            enemy_health[enemy_pos]=100
            enemy_next_fire_time[enemy_pos]=time.time()+random.uniform(0,enemy_fire_interval_max)

def check_bullet_collision(bullet_x,bullet_y,bullet_radius):
    for enemy_pos in wave_enemies[:]:
        if enemy_health.get(enemy_pos,0)>0:
            enemy_x,enemy_y,enemy_z=enemy_pos
            enemy_radius=get_enemy_radius(level)
            distance=math.sqrt((bullet_x-enemy_x)**2+(bullet_y-enemy_y)**2)
            if distance<bullet_radius+enemy_radius:
                return True
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((bullet_x-tree_x)**2+(bullet_y-tree_y)**2)
            if distance<bullet_radius+tree_radius:
                return True
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((bullet_x-snowman_x)**2+(bullet_y-snowman_y)**2)
            if distance<bullet_radius+snowman_radius:
                return True
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((bullet_x-mountain_x)**2+(bullet_y-mountain_y)**2)
            if distance<bullet_radius+base_radius:
                return True
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((bullet_x-cactus_x)**2+(bullet_y-cactus_y)**2)
            if distance<bullet_radius+cactus_radius:
                return True
    return False

def is_position_valid(x,y,enemy_type="enemy"):     #for enemy
    if enemy_type=="enemy":
        enemy_radius=60
    else:
        enemy_radius=50

    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<(enemy_radius+tree_radius):
                return False
            
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<(enemy_radius+snowman_radius):
                return False
            
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<(enemy_radius+base_radius):
                return False
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<(enemy_radius+cactus_radius):
                return False
    return True

def is_too_close_to_player(x,y):                  #for enemy
    player_pos=vehicle_positions[current_vehicle]
    distance=math.sqrt((x-player_pos[0])**2+(y-player_pos[1])**2)
    if distance<400:
        return True
    return False

def is_colliding_with_enemies(x,y):
    player_radius=50
    for enemy_pos in wave_enemies:

        if enemy_health.get(enemy_pos,0)>0:    #Jei enemy gula beche ase
            enemy_x,enemy_y,enemy_z=enemy_pos
            enemy_radius=get_enemy_radius(level)
            distance=math.sqrt((x-enemy_x)**2+(y-enemy_y)**2)

            if distance<(player_radius+enemy_radius):
                return True
    return False

def is_position_valid_for_player(x,y):
    if not (-max_border<=x<=max_border and -max_border<=y<=max_border):
        return False
    if is_colliding_with_obstacles(x,y):
        return False
    if is_colliding_with_enemies(x,y):
        return False
    return True

def init_tree_positions():
    global tree_positions
    tree_positions=[
        (-GRID_LENGTH+400,-GRID_LENGTH+450),
        (GRID_LENGTH-450,-GRID_LENGTH+400),
        (-GRID_LENGTH+500,GRID_LENGTH-350),
        (GRID_LENGTH-250,GRID_LENGTH-100),
        (-GRID_LENGTH+200,300),
        (-GRID_LENGTH+400,0),
        (GRID_LENGTH-400,0),
        (0,450),
    ]

def init_snowman_positions():
    global snowman_positions
    snowman_positions=[
        (-GRID_LENGTH+300,-GRID_LENGTH+300),
        (GRID_LENGTH-300,-GRID_LENGTH+300),
        (-GRID_LENGTH+300,GRID_LENGTH-300),
        (GRID_LENGTH-300,GRID_LENGTH-300),
        (0,-GRID_LENGTH+400),
        (0,GRID_LENGTH-400),
        (-GRID_LENGTH+400,0),
        (GRID_LENGTH-400,0),
        (-400,-400),
        (400,400),
        (-200,500)
    ]

def draw_tree(x,y):
    glPushMatrix()
    glTranslatef(x,y,0)
    glColor3f(0.4,0.2,0.1)
    glPushMatrix()
    glTranslatef(0,0,10)
    gluCylinder(gluNewQuadric(),40,40,100,12,5)
    glPopMatrix()
    glTranslatef(0,0,100)
    glColor3f(0.0,0.6,0.0)
    glPushMatrix()
    gluCylinder(gluNewQuadric(),50,0,110,16,2)
    glPopMatrix()
    glPopMatrix()

def draw_grass_patch(x,y,size):
    glPushMatrix()
    glTranslatef(x,y,0.1)
    glColor3f(0.1,0.7,0.1)
    glBegin(GL_QUADS)
    glVertex3f(-size,-size,0)
    glVertex3f(size,-size,0)
    glVertex3f(size,size,0)
    glVertex3f(-size,size,0)
    glEnd()
    glPopMatrix()

def draw_snowman(x,y):
    glPushMatrix()
    glTranslatef(x,y,0)
    glColor3f(1.0,1.0,1.0)
    glPushMatrix()
    glTranslatef(0,0,40)
    gluSphere(gluNewQuadric(),40,20,20)
    glPopMatrix()
    glColor3f(1.0,1.0,1.0)
    glPushMatrix()
    glTranslatef(0,0,110)
    gluSphere(gluNewQuadric(),30,20,20)
    glPopMatrix()
    glColor3f(1.0,1.0,1.0)
    glPushMatrix()
    glTranslatef(0,0,160)
    gluSphere(gluNewQuadric(),20,20,20)
    glPopMatrix()
    glColor3f(0.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(-6,20,160)
    gluSphere(gluNewQuadric(),3,10,10)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(6,20,160)
    gluSphere(gluNewQuadric(),3,10,10)
    glPopMatrix()
    glColor3f(1.0,0.5,0.0)
    glPushMatrix()
    glTranslatef(0,20,160)
    glRotatef(-90,1,0,0)
    gluCylinder(gluNewQuadric(),3,0,25,10,2)
    glPopMatrix()
    glPopMatrix()

def init_sand_mountain_positions():
    global sand_mountain_positions
    sand_mountain_positions=[
        (-GRID_LENGTH+200,-GRID_LENGTH+200,140,90),
        (GRID_LENGTH-400,-GRID_LENGTH+400,135,85),
        (-GRID_LENGTH+300,GRID_LENGTH-250,145,95),
        (GRID_LENGTH-500,GRID_LENGTH-500,130,88),
        (0,-GRID_LENGTH+300,120,80),
        (0,GRID_LENGTH-200,125,82),
        (-GRID_LENGTH+500,0,115,78),
        (GRID_LENGTH-500,0,118,80),
        (-500,500,110,75),
        (500,-500,112,76)
    ]

def draw_sand_mountain(x,y,height,base_radius):
    glPushMatrix()
    glTranslatef(x,y,0)
    glColor3f(0.88,0.82,0.62)
    gluCylinder(gluNewQuadric(),base_radius,0,height,16,5)
    glPopMatrix()

def init_cactus_positions():
    global cactus_positions
    cactus_positions=[
        (-GRID_LENGTH+300,0,110),
        (GRID_LENGTH-200,0,115),
        (0,-GRID_LENGTH+700,120),
        (0,GRID_LENGTH-500,118),
    ]

def draw_cactus(x,y,height):
    glPushMatrix()
    glTranslatef(x,y,0)
    glColor3f(0.2,0.6,0.2)
    gluCylinder(gluNewQuadric(),25,15,height,12,5)
    side_sphere_positions=[
        (20,0,height*0.3,18),
        (-20,0,height*0.5,20),
        (0,25,height*0.7,22),
        (0,-20,height*0.4,16),
        (25,20,height*0.8,15)
    ]
    for sphere_x,sphere_y,sphere_z,sphere_radius in side_sphere_positions:
        glPushMatrix()
        glTranslatef(sphere_x,sphere_y,sphere_z)
        glColor3f(0.25,0.65,0.25)
        gluSphere(gluNewQuadric(),sphere_radius,12,12)
        glPopMatrix()
    glPopMatrix()

def is_colliding_with_obstacles(x,y):
    vehicle_radius=50
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<(vehicle_radius+tree_radius):
                return True
            
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<(vehicle_radius+snowman_radius):
                return True
            
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<(vehicle_radius+base_radius):
                return True
            
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<(vehicle_radius+cactus_radius):
                return True
    return False

def update_wave_state():
    global enemies_remaining,wave_complete,current_wave,next_wave_timer,score,enemy_next_fire_time,enemy_angles,level,game_complete,game_paused
    global vehicle_positions,vehicle_angles
    if game_paused:
        return
    current_time=time.time()
    alive_enemies=0
    enemies_to_remove=[]
    for enemy_pos in wave_enemies[:]:
        if enemy_health.get(enemy_pos,0)<=0:
            enemies_to_remove.append(enemy_pos)
        else:
            alive_enemies+=1
    for enemy_pos in enemies_to_remove:
        if enemy_pos in wave_enemies:
            wave_enemies.remove(enemy_pos)
        if enemy_pos in enemy_health:
            del enemy_health[enemy_pos]
        if enemy_pos in enemy_angles:
            del enemy_angles[enemy_pos]
        if enemy_pos in enemy_next_fire_time:
            del enemy_next_fire_time[enemy_pos]
        score+=100
    enemies_remaining=alive_enemies
    if enemies_remaining==0 and not wave_complete and next_wave_timer==0:
        wave_complete=True
        next_wave_timer=current_time+wave_spawn_delay
    if wave_complete and next_wave_timer>0 and current_time>=next_wave_timer:
        if current_wave<waves_per_level:
            current_wave+=1
            init_wave_enemies()
        else:
            if level<3:
                level+=1
                current_wave=1
                for i in range(3):
                    vehicle_positions[i]=[0,0,0]
                    vehicle_angles[i]=0
                init_level_obstacles()
                init_landmine_positions()
                init_ammo_medical_boxes()
                init_wave_enemies()
            else:
                game_complete=True

def draw_arena():
    global tree_positions,tree_positions
    if level==1:
        if not tree_positions:
            init_tree_positions()
        glBegin(GL_QUADS)
        glColor3f(0.2,0.8,0.2)
        glVertex3f(-GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,GRID_LENGTH,0)
        glVertex3f(-GRID_LENGTH,GRID_LENGTH,0)
        glEnd()
        grass_patches=[
            (-600,-600,30),(-200,-700,25),(400,-500,35),
            (-500,300,28),(100,100,32),(600,-200,27),
            (300,600,29),(-700,-100,26),(500,400,31),
            (-300,500,24)
        ]
        for patch in grass_patches:
            draw_grass_patch(patch[0],patch[1],patch[2])
        draw_enemies()
        draw_landmines()
        draw_ammo_medical_boxes()
        for x,y in tree_positions:
            draw_tree(x,y)
    elif level==2:
        glBegin(GL_QUADS)
        glColor3f(0.4,0.8,1.0)
        glVertex3f(-GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,GRID_LENGTH,0)
        glVertex3f(-GRID_LENGTH,GRID_LENGTH,0)
        glEnd()
        draw_enemies()
        draw_landmines()
        draw_ammo_medical_boxes()
        for x,y in snowman_positions:
            draw_snowman(x,y)
    elif level==3:
        glBegin(GL_QUADS)
        glColor3f(0.76,0.70,0.50)
        glVertex3f(-GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,-GRID_LENGTH,0)
        glVertex3f(GRID_LENGTH,GRID_LENGTH,0)
        glVertex3f(-GRID_LENGTH,GRID_LENGTH,0)
        glEnd()
        draw_enemies()
        draw_landmines()
        draw_ammo_medical_boxes()
        for x,y,height,base_radius in sand_mountain_positions:
            draw_sand_mountain(x,y,height,base_radius)
        for x,y,height in cactus_positions:
            draw_cactus(x,y,height)

def draw_border():
    z_offset=0.1
    glBegin(GL_QUADS)
    glColor3f(0,1,1)
    glVertex3f(GRID_LENGTH,-GRID_LENGTH,z_offset)
    glVertex3f(GRID_LENGTH,-GRID_LENGTH,border_height)
    glVertex3f(GRID_LENGTH,GRID_LENGTH,border_height)
    glVertex3f(GRID_LENGTH,GRID_LENGTH,z_offset)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0,1,1)
    glVertex3f(-GRID_LENGTH,-GRID_LENGTH,z_offset)
    glVertex3f(-GRID_LENGTH,-GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,GRID_LENGTH,z_offset)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0,0,1)
    glVertex3f(GRID_LENGTH,-GRID_LENGTH,z_offset)
    glVertex3f(GRID_LENGTH,-GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,-GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,-GRID_LENGTH,z_offset)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0,0,1)
    glVertex3f(GRID_LENGTH,GRID_LENGTH,z_offset)
    glVertex3f(GRID_LENGTH,GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,GRID_LENGTH,border_height)
    glVertex3f(-GRID_LENGTH,GRID_LENGTH,z_offset)
    glEnd()

def draw_landmine(x,y):
    glPushMatrix()
    glTranslatef(x,y,5)
    glColor3f(0.15,0.15,0.15)
    glPushMatrix()
    glScalef(25,25,10)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.4,0.4,0.4)
    glPushMatrix()
    glTranslatef(0,0,8)
    glScalef(20,20,4)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1.0,1.0,0.0)
    glPushMatrix()
    glTranslatef(0,0,6)
    glScalef(22,5,2)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,6)
    glScalef(5,22,2)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(0,0,12)
    gluSphere(gluNewQuadric(),4,8,8)
    glPopMatrix()
    glPopMatrix()

def init_landmine_positions():
    global landmine_positions
    landmine_positions=[]
    attempts=0
    while len(landmine_positions)<landmine_count and attempts<200:
        attempts+=1
        x=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
        y=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
        if (is_landmine_position_valid(x,y) and
            not is_too_close_to_player(x,y) and
            not is_too_close_to_enemies(x,y)):
            too_close=False
            for mine_x,mine_y in landmine_positions:
                dist=math.sqrt((x-mine_x)**2+(y-mine_y)**2)
                if dist<200:
                    too_close=True
                    break
            if not too_close:
                landmine_positions.append((x,y))

def is_landmine_position_valid(x,y):
    landmine_radius=30
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<landmine_radius+tree_radius:
                return False
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<landmine_radius+snowman_radius:
                return False
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<landmine_radius+base_radius:
                return False
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<landmine_radius+cactus_radius:
                return False
    if not (-max_border<=x<=max_border and -max_border<=y<=max_border):
        return False
    return True

def is_too_close_to_enemies(x,y):
    landmine_radius=30
    for enemy_pos in wave_enemies:
        if enemy_health.get(enemy_pos,0)>0:
            enemy_x,enemy_y,_=enemy_pos
            enemy_radius=get_enemy_radius(level)
            distance=math.sqrt((x-enemy_x)**2+(y-enemy_y)**2)
            if distance<landmine_radius+enemy_radius+50:
                return True
    return False

def draw_landmines():
    for x,y in landmine_positions:
        draw_landmine(x,y)

def init_ammo_medical_boxes():
    global ammo_box_positions,medical_box_positions
    ammo_box_positions=[]
    medical_box_positions=[]
    for _ in range(2):
        position_found=False
        attempts=0
        while not position_found and attempts<100:
            attempts+=1
            x=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
            y=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
            if (is_box_position_valid(x,y) and
                not is_too_close_to_player(x,y) and
                not is_too_close_to_enemies(x,y) and
                not is_too_close_to_other_boxes(x,y)):
                ammo_box_positions.append((x,y,20))
                position_found=True
    for _ in range(2):
        position_found=False
        attempts=0
        while not position_found and attempts<100:
            attempts+=1
            x=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
            y=random.randint(-GRID_LENGTH+300,GRID_LENGTH-300)
            if (is_box_position_valid(x,y) and
                not is_too_close_to_player(x,y) and
                not is_too_close_to_enemies(x,y) and
                not is_too_close_to_other_boxes(x,y)):
                medical_box_positions.append((x,y,20))
                position_found=True

def is_box_position_valid(x,y):
    box_radius=40
    if level==1:
        for tree_x,tree_y in tree_positions:
            tree_radius=50
            distance=math.sqrt((x-tree_x)**2+(y-tree_y)**2)
            if distance<box_radius+tree_radius:
                return False
    elif level==2:
        for snowman_x,snowman_y in snowman_positions:
            snowman_radius=40
            distance=math.sqrt((x-snowman_x)**2+(y-snowman_y)**2)
            if distance<box_radius+snowman_radius:
                return False
    elif level==3:
        for mountain_x,mountain_y,height,base_radius in sand_mountain_positions:
            distance=math.sqrt((x-mountain_x)**2+(y-mountain_y)**2)
            if distance<box_radius+base_radius:
                return False
        for cactus_x,cactus_y,height in cactus_positions:
            cactus_radius=30
            distance=math.sqrt((x-cactus_x)**2+(y-cactus_y)**2)
            if distance<box_radius+cactus_radius:
                return False
    if not (-max_border<=x<=max_border and -max_border<=y<=max_border):
        return False
    return True

def is_too_close_to_other_boxes(x,y):
    for box_x,box_y,box_z in ammo_box_positions+medical_box_positions:
        distance=math.sqrt((x-box_x)**2+(y-box_y)**2)
        if distance<150:
            return True
    return False

def draw_ammo_box(x,y,z):
    glPushMatrix()
    glTranslatef(x,y,z)
    glColor3f(0.05,0.05,0.05)
    glPushMatrix()
    glScalef(40,40,25)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0.1,0.1,0.1)
    glPushMatrix()
    glTranslatef(0,0,25)
    glPushMatrix()
    glScalef(8,8,12)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,12)
    glColor3f(0.8,0.8,0.8)
    gluSphere(gluNewQuadric(),6,10,10)
    glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def draw_medical_box(x,y,z):
    glPushMatrix()
    glTranslatef(x,y,z)
    glColor3f(1.0,1.0,1.0)
    glPushMatrix()
    glScalef(40,40,25)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(0,0,15)
    glScalef(8,30,3)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,15)
    glScalef(30,8,3)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1.0,0.0,0.0)
    glPushMatrix()
    glTranslatef(0,0,25)
    glPushMatrix()
    glScalef(5,5,10)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glScalef(10,5,5)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()
    glPopMatrix()

def draw_ammo_medical_boxes():
    for x,y,z in ammo_box_positions:
        draw_ammo_box(x,y,z)
    for x,y,z in medical_box_positions:
        draw_medical_box(x,y,z)

def check_mine_supplies_collision():
    global vehicle_health,current_vehicle,missed_bullets_count,landmine_positions,ammo_box_positions,medical_box_positions,game_paused
    global mine_damage,medical_box_heal,ammo_box_reduce_missed
    if game_paused:
        return
    player_x,player_y,player_z=vehicle_positions[current_vehicle]
    player_radius=50
    for i,(mine_x,mine_y) in enumerate(landmine_positions[:]):
        distance=math.sqrt((player_x-mine_x)**2+(player_y-mine_y)**2)
        if distance<player_radius+25:
            vehicle_health[current_vehicle]-=mine_damage
            vehicle_health[current_vehicle]=max(0,vehicle_health[current_vehicle])
            landmine_positions.pop(i)
            break
    for i,(med_x,med_y,med_z) in enumerate(medical_box_positions[:]):
        distance=math.sqrt((player_x-med_x)**2+(player_y-med_y)**2)
        if distance<player_radius+40:
            vehicle_health[current_vehicle]+=medical_box_heal
            medical_box_positions.pop(i)
            break
    for i,(ammo_x,ammo_y,ammo_z) in enumerate(ammo_box_positions[:]):
        distance=math.sqrt((player_x-ammo_x)**2+(player_y-ammo_y)**2)
        if distance<player_radius+40:
            missed_bullets_count=max(0,missed_bullets_count-ammo_box_reduce_missed)
            ammo_box_positions.pop(i)
            break

def cheat_mode_auto_target_fire():
    global vehicle_angles,current_vehicle,fire_rates,last_fire_time,game_paused
    if game_paused:
        return
    if not wave_enemies or not cheat_mode:  #shudhu enemy thakle and cheat mode on e kaaj korbe
        return
    
    nearest_enemy=None
    min_distance=float('inf')
    player_pos=vehicle_positions[current_vehicle]

    for enemy_pos in wave_enemies:
        if enemy_health.get(enemy_pos,0)>0:  # jara beche ase
            enemy_x,enemy_y,enemy_z=enemy_pos
            distance=math.sqrt((player_pos[0]-enemy_x)**2+(player_pos[1]-enemy_y)**2)
            if distance<min_distance:
                min_distance=distance
                nearest_enemy=enemy_pos

    if nearest_enemy!=None:
        enemy_x,enemy_y,enemy_z=nearest_enemy
        dx=enemy_x-player_pos[0]
        dy=enemy_y-player_pos[1]
        angle_rad=math.atan2(dx,-dy)
        target_angle_deg=math.degrees(angle_rad)

        if target_angle_deg<0:
            target_angle_deg+=360

        current_angle=vehicle_angles[current_vehicle]
        
        rotation_speed=4.0             #koto fast rotate korbe

        angle_diff=(target_angle_deg-current_angle)%360
        if angle_diff>180:
            angle_diff-=360

        if abs(angle_diff)<rotation_speed:       # vehicle er new angle update
            new_angle=target_angle_deg
        else:
            new_angle=current_angle+(rotation_speed if angle_diff>0 else -rotation_speed)
        vehicle_angles[current_vehicle]=new_angle%360

        if abs(angle_diff)<=10:    #diff 10 degree hole fire korbe
            current_time=time.time()
            vehicle_type=current_vehicle
            if current_time-last_fire_time[vehicle_type]>=fire_rates[vehicle_type]:  # 2 ta bullet er time er difference
                fire_bullet()

def init_level_obstacles():
    global tree_positions,snowman_positions,sand_mountain_positions,cactus_positions
    if level==1:
        init_tree_positions()
    elif level==2:
        init_snowman_positions()
    elif level==3:
        init_sand_mountain_positions()
        init_cactus_positions()

def restart_game():
    global level,current_wave,score,game_complete,bullets,enemy_bullets,cheat_mode,vehicle_positions,vehicle_angles,cam_mode,game_over,vehicle_health,current_vehicle,weather,game_paused,missed_bullets_count,total_bullets_fired,landmine_positions,ammo_box_positions,medical_box_positions,is_day_mode
    level=1
    current_wave=1
    current_vehicle=medium_vehicle
    score=0
    game_complete=False
    is_day_mode=False
    game_over=False
    weather=True
    cheat_mode=False
    game_paused=False
    missed_bullets_count=0
    total_bullets_fired=0
    vehicle_health=[1000,800,600]
    bullets.clear()
    enemy_bullets.clear()
    landmine_positions.clear()
    ammo_box_positions.clear()
    medical_box_positions.clear()
    for i in range(3):
        vehicle_positions[i]=[0,0,0]
        vehicle_angles[i]=0
    cam_mode=cam_world
    init_level_obstacles()
    init_landmine_positions()
    init_ammo_medical_boxes()
    init_wave_enemies()

def draw_text(x,y,text,font=GLUT_BITMAP_HELVETICA_18,color=None):
    if color is not None:
        glColor3f(*color)
    else:
        glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    global win_w,win_h
    gluOrtho2D(0,win_w,0,win_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x,y)
    for ch in text:
        glutBitmapCharacter(font,ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_rect_2d(x,y,w,h):
    glBegin(GL_QUADS)
    glVertex2f(x,y)
    glVertex2f(x+w,y)
    glVertex2f(x+w,y+h)
    glVertex2f(x,y+h)
    glEnd()

def draw_health_bar(x,y,w,h,health,max_health,label,fill_rgb=(0.2,0.9,0.2)):
    if max_health<=0:
        ratio=0.0
    else:
        ratio=health/float(max_health)
        if ratio<0.0:ratio=0.0
        if ratio>1.0:ratio=1.0
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    global win_w,win_h
    gluOrtho2D(0,win_w,0,win_h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(0.10,0.10,0.10)
    draw_rect_2d(x,y,w,h)
    glColor3f(*fill_rgb)
    draw_rect_2d(x+2,y+2,(w-4)*ratio,h-4)
    glColor3f(0,0,0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(x,y)
    glVertex2f(x+w,y)
    glVertex2f(x+w,y+h)
    glVertex2f(x,y+h)
    glEnd()
    glLineWidth(1.0)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    draw_text(x,y+h+6,f"{label}:{int(health)}/{int(max_health)}",GLUT_BITMAP_HELVETICA_12)

def draw_vehicle_health_bars():
    max_vals=[1000,800,600]
    labels=["Tank","Jeep","Sports"]
    fills=[
        (0.2,0.9,0.2),
        (0.2,0.7,1.0),
        (1.0,0.6,0.2),
    ]
    x=10
    y0=565
    w=220
    h=16
    gap=34
    for i in range(3):
        draw_health_bar(
            x,y0-i*gap,w,h,
            vehicle_health[i],max_vals[i],
            labels[i],
            fill_rgb=fills[i]
        )

def keyboardListener(key,x,y):
    global current_vehicle,vehicle_positions,vehicle_angles,game_complete,game_over,vehicle_health,cheat_mode,game_paused,cam_mode
    if (key==b'r' or key==b'R'):
        restart_game()
        return
    if game_over==True:
        return
    if game_complete==True:
        return
    if game_paused==True:
        return
    if key==b'1':
        if vehicle_health[heavy_vehicle]>0:                                       #jodi Tank mara na jay,tailei shudhu switch
            current_x,current_y,current_z=vehicle_positions[current_vehicle]      #ager vehicle er position and angle save
            current_angle=vehicle_angles[current_vehicle]

            current_vehicle=heavy_vehicle           #vehicle switch

            vehicle_positions[current_vehicle]=[current_x,current_y,current_z] #new vehicle jate ager tar same position ar angle e ashe
            vehicle_angles[current_vehicle]=current_angle
    elif key==b'2':
        if vehicle_health[medium_vehicle]>0:
            current_x,current_y,current_z=vehicle_positions[current_vehicle]
            current_angle=vehicle_angles[current_vehicle]
            current_vehicle=medium_vehicle
            vehicle_positions[current_vehicle]=[current_x,current_y,current_z]
            vehicle_angles[current_vehicle]=current_angle
    elif key==b'3':
        if vehicle_health[light_vehicle]>0:
            current_x,current_y,current_z=vehicle_positions[current_vehicle]
            current_angle=vehicle_angles[current_vehicle]
            current_vehicle=light_vehicle
            vehicle_positions[current_vehicle]=[current_x,current_y,current_z]
            vehicle_angles[current_vehicle]=current_angle
    if key==b' ':
        fire_bullet()
    
    #################### Vehicle Movement #############################

    speed=vehicle_speed[current_vehicle]
    angle_rad=math.radians(vehicle_angles[current_vehicle])
    dell_x=math.sin(angle_rad)
    dell_y=math.cos(angle_rad)
    new_x=vehicle_positions[current_vehicle][0]
    new_y=vehicle_positions[current_vehicle][1]

    if key==b'w' or key==b'W':
        potential_x=new_x+(speed*dell_x)
        potential_y=new_y-(speed*dell_y)
        if is_position_valid_for_player(potential_x,potential_y)==True:
            vehicle_positions[current_vehicle][0]=potential_x
            vehicle_positions[current_vehicle][1]=potential_y

    if key==b's' or key==b'S':
        potential_x=new_x-(speed*dell_x)
        potential_y=new_y+(speed*dell_y)
        if is_position_valid_for_player(potential_x,potential_y)==True:
            vehicle_positions[current_vehicle][0]=potential_x
            vehicle_positions[current_vehicle][1]=potential_y

    if key==b'a' or key==b'A':
        vehicle_angles[current_vehicle]+=5
    if key==b'd' or key==b'D':
        vehicle_angles[current_vehicle]-=5

    #######################################################################

    if key==b'v' or key==b'V':
        cam_mode=(cam_mode+1)%3
    global is_day_mode
    if key==b't' or key==b'T':
        is_day_mode=not is_day_mode
    global weather
    if key==b'q' or key==b'Q':
        weather=not(weather)
    if key==b'c' or key==b'C':
        cheat_mode=not cheat_mode
        return

def specialKeyListener(key,x,y):
    global cam_mode,game_complete,game_over,game_paused
    if game_complete or game_over:
        return
    if game_paused:
        return
    if cam_mode!=cam_world:
        return
    global cam_pos
    x_pos,y_pos,z_pos=cam_pos
    if key==GLUT_KEY_DOWN:
        z_pos-=10
    elif key==GLUT_KEY_UP:
        z_pos+=10
    elif key==GLUT_KEY_LEFT:
        angle=math.atan2(y_pos,x_pos)
        angle=angle-math.radians(2)
        radius=math.sqrt(x_pos**2+y_pos**2)
        x_pos=radius*math.cos(angle)
        y_pos=radius*math.sin(angle)
    elif key==GLUT_KEY_RIGHT:
        angle=math.atan2(y_pos,x_pos)
        angle=angle+math.radians(2)
        radius=math.sqrt(x_pos**2+y_pos**2)
        x_pos=radius*math.cos(angle)
        y_pos=radius*math.sin(angle)
    cam_pos=(x_pos,y_pos,z_pos)

def mouseListener(button,state,x,y):
    global game_paused
    if state==GLUT_DOWN:
        if button==GLUT_LEFT_BUTTON:
            game_paused=not game_paused
        elif button==GLUT_RIGHT_BUTTON:
            glutLeaveMainLoop()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    global win_aspect
    gluPerspective(fovY,win_aspect,0.1,3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    eye,center,up=compute_camera_for_mode()
    gluLookAt(
        eye[0],eye[1],eye[2],
        center[0],center[1],center[2],
        up[0],up[1],up[2]
    )

def update_fov_for_camera_mode():
    global fovY,cam_mode
    if cam_mode==cam_first_person:
        fovY=fp_fovy
    elif cam_mode==cam_third_person:
        fovY=chase_fovy
    else:
        fovY=world_fovy

def idle():
    global game_over,game_complete,current_vehicle,game_paused
    if game_over or game_complete:
        glutPostRedisplay()
        return
    if game_paused:
        glutPostRedisplay()
        return
    update_fov_for_camera_mode()
    transform_sky_towards_day()
    dt=0.016
    cheat_mode_auto_target_fire()
    if level==2:
        update_snow(dt)
    elif level==1:
        update_rain(dt)
    elif level==3:
        update_snow(dt)
    if not game_complete:
        check_mine_supplies_collision()
        update_bullets()
        update_enemy_bullets()
        move_enemies()
        enemy_fire()
        update_wave_state()
    glutPostRedisplay()

def showScreen():
    global cam_mode,game_complete,game_over,cheat_mode,game_paused
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    if game_over:
        if missed_bullets_count>=max_bullets_missed:
            draw_text(400,400,f"GAME OVER - Too many missed bullets!",GLUT_BITMAP_TIMES_ROMAN_24)
            draw_text(400,370,f"Missed {missed_bullets_count}/{max_bullets_missed} bullets",GLUT_BITMAP_HELVETICA_18)
        else:
            draw_text(400,400,"GAME OVER - All Vehicles Destroyed!",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(400,340,f"Score:{score}",GLUT_BITMAP_HELVETICA_18)
        draw_text(400,310,"Press R to Restart",GLUT_BITMAP_HELVETICA_18)
        glutSwapBuffers()
        return
    if game_complete:
        draw_text(400,400,f"Congratulations!!! You have completed the game.",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(400,370,f"Score:{score}",GLUT_BITMAP_HELVETICA_18)
        draw_text(400,310,"Press R to Restart",GLUT_BITMAP_HELVETICA_18)
        glutSwapBuffers()
        return
    glViewport(0,0,win_w,win_h)
    draw_sky_background_2d()
    glClear(GL_DEPTH_BUFFER_BIT)
    setupCamera()
    draw_clouds_3d()
    draw_border()
    draw_arena()
    draw_enemy_bullets()
    draw_bullets()
    if cam_mode==cam_first_person:
        draw_fp_weapon_only()
    else:
        draw_car()
    if level==2 and weather==True:
        draw_snow()
    elif level==1 and weather==True:
        draw_rain()
    elif level==3 and weather==True:
        draw_snow()
    vehicle_names=["Tank (Heavy)","Jeep (Medium)","Sports Car (Light)"]
    current_name=vehicle_names[current_vehicle]
    draw_vehicle_health_bars()
    draw_text(10,750,f"Level:{level}")
    draw_text(10,730,f"Wave:{current_wave}/2")
    draw_text(10,710,f"Score:{score}")
    draw_text(10,690,f"Missed Bullets:{missed_bullets_count}/{max_bullets_missed}")
    draw_text(10,670,f"Bullets Fired:{total_bullets_fired}")
    draw_text(10,650,f"Enemies Remaining:{enemies_remaining}")
    draw_text(10,630,f"Current Vehicle:{current_name}")
    if cheat_mode:
        draw_text(10,610,f"Cheat Mode:ON")
    else:
        draw_text(10,610,f"Cheat Mode:OFF")
    draw_text(785,760,f"Pause/Resume:Left Click")
    draw_text(785,735,f"Exit:Right Click")
    draw_text(785,710,f"Restart:Press 'R'")
    if missed_bullets_count>=max_bullets_missed*0.7:
        warning_text=f"WARNING:{max_bullets_missed-missed_bullets_count} misses until game over!"
        draw_text(10,470,warning_text,GLUT_BITMAP_HELVETICA_18,color=(1.0,0.0,0.0))
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE|GLUT_RGB|GLUT_DEPTH)
    glutInitWindowSize(1000,800)
    glutInitWindowPosition(0,0)
    wind=glutCreateWindow(b"Vehicle Combat")
    init_level_obstacles()
    init_landmine_positions()
    init_ammo_medical_boxes()
    init_wave_enemies()
    init_stars_2d()
    init_clouds_3d()
    glutReshapeFunc(reshape)
    update_sky_layout_from_window()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__=="__main__":
    main()