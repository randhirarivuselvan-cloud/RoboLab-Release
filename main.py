from pathlib import Path
import os, secrets, sqlite3, json, math
from urllib.parse import urlencode
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
DB = BASE / 'data' / 'robolab.db'
STATIC = BASE / 'static'

app = FastAPI(title='RoboLab', version='2.1.0', description='Robotics engineering platform by SynapseX Robotics & Technologies')
SESSION_SECRET = os.getenv('SESSION_SECRET') or secrets.token_urlsafe(48)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET,
                   https_only=os.getenv('COOKIE_SECURE', 'false').lower() == 'true', same_site='lax')
app.mount('/static', StaticFiles(directory=STATIC), name='static')

COMPONENTS = [
 {'id':'esp32','name':'ESP32 DevKit V1','category':'Controller','price':550,'tags':['controller','wifi','bluetooth']},
 {'id':'arduino-uno','name':'Arduino Uno R3 Compatible','category':'Controller','price':450,'tags':['controller','beginner']},
 {'id':'pca9685','name':'PCA9685 16-Channel Servo Driver','category':'Driver','price':180,'tags':['servo','pwm']},
 {'id':'ir-array','name':'5-Channel IR Sensor Array','category':'Sensor','price':180,'tags':['line follower','sensor']},
 {'id':'hc-sr04','name':'HC-SR04 Ultrasonic Sensor','category':'Sensor','price':90,'tags':['distance','sensor']},
 {'id':'mpu6050','name':'MPU6050 IMU','category':'Sensor','price':120,'tags':['imu','gyro','accelerometer']},
 {'id':'mg996r','name':'MG996R Metal Gear Servo','category':'Actuator','price':320,'tags':['servo','robot arm','quadruped']},
 {'id':'tt-motor','name':'TT Gear Motor','category':'Motor','price':110,'tags':['motor','wheeled']},
 {'id':'l298n','name':'L298N Motor Driver','category':'Driver','price':120,'tags':['motor','driver']},
 {'id':'18650-holder','name':'2x18650 Battery Holder','category':'Power','price':70,'tags':['battery','power']},
 {'id':'buck','name':'LM2596 Buck Converter','category':'Power','price':90,'tags':['power','voltage']},
 {'id':'breadboard','name':'830 Point Breadboard','category':'Prototype','price':100,'tags':['prototype','beginner']},
 {'id':'jumper','name':'Jumper Wire Set','category':'Wiring','price':100,'tags':['wiring','prototype']},
]

# Optional live supplier adapters. Configure a JSON endpoint via SUPPLIER_FEEDS.
# Example value: {"demo-shop":"https://example.com/robolab-inventory.json"}
SUPPLIER_FEEDS = json.loads(os.getenv('SUPPLIER_FEEDS', '{}') or '{}')


def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, google_id TEXT UNIQUE, email TEXT UNIQUE, name TEXT, picture TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    return con


def project_plan(prompt: str, budget: int | None = None):
    p=(prompt or '').lower(); selected=[]; qty={}
    def add(i,n=1):
        if i not in selected: selected.append(i)
        qty[i]=qty.get(i,0)+n
    if any(x in p for x in ['line follower','line-following','line following']):
        add('arduino-uno'); add('ir-array'); add('tt-motor',2); add('l298n'); add('18650-holder'); add('breadboard'); add('jumper')
    elif any(x in p for x in ['quadruped','walking robot','robot dog']):
        add('esp32'); add('pca9685'); add('mg996r',12); add('mpu6050'); add('buck'); add('18650-holder'); add('jumper')
    elif any(x in p for x in ['robot arm','robotic arm']):
        add('esp32'); add('pca9685'); add('mg996r',4); add('buck'); add('breadboard'); add('jumper')
    elif any(x in p for x in ['obstacle','avoid']):
        add('arduino-uno'); add('hc-sr04'); add('tt-motor',2); add('l298n'); add('18650-holder'); add('jumper')
    else:
        add('esp32'); add('hc-sr04'); add('tt-motor',2); add('l298n'); add('18650-holder'); add('breadboard'); add('jumper')
    items=[]; total=0
    for c in COMPONENTS:
        if c['id'] in selected:
            q=qty[c['id']]; cost=c['price']*q; total+=cost
            items.append({**c,'quantity':q,'cost':cost})
    alternatives=['Keep a 10–20% contingency for connectors, mounting hardware and shipping.']
    if budget and total>budget:
        alternatives=['Prototype the control logic first and defer non-essential mechanical parts.']
    return {'project':prompt.strip() or 'Robotics prototype','items':items,'total_estimate':total,'budget':budget,'within_budget':(budget is None or total<=budget),'alternatives':alternatives}


def codegen(platform: str, project: str):
    p=(project or '').lower(); platform=(platform or 'arduino').lower()
    if 'line' in p:
        if platform == 'esp32':
            code='''// RoboLab generated ESP32 line-follower starter\nconst int L_IN1=25,L_IN2=26,R_IN1=27,R_IN2=14;\nconst int S1=34,S2=35,S3=32;\nvoid setup(){Serial.begin(115200);pinMode(L_IN1,OUTPUT);pinMode(L_IN2,OUTPUT);pinMode(R_IN1,OUTPUT);pinMode(R_IN2,OUTPUT);}\nvoid motor(int a,int b,bool f){digitalWrite(a,f);digitalWrite(b,!f);}\nvoid loop(){int l=analogRead(S1),c=analogRead(S2),r=analogRead(S3); if(c<1500){motor(L_IN1,L_IN2,1);motor(R_IN1,R_IN2,1);} else if(l<r){motor(L_IN1,L_IN2,0);motor(R_IN1,R_IN2,1);} else {motor(L_IN1,L_IN2,1);motor(R_IN1,R_IN2,0);} delay(20);}\n'''
        else:
            code='''// RoboLab generated Arduino line-follower starter\nconst int L1=5,L2=6,R1=9,R2=10;\nconst int S1=A0,S2=A1,S3=A2;\nvoid setup(){Serial.begin(9600);pinMode(L1,OUTPUT);pinMode(L2,OUTPUT);pinMode(R1,OUTPUT);pinMode(R2,OUTPUT);}\nvoid motor(int a,int b,bool f){digitalWrite(a,f);digitalWrite(b,!f);}\nvoid loop(){int l=analogRead(S1),c=analogRead(S2),r=analogRead(S3); if(c<500){motor(L1,L2,1);motor(R1,R2,1);} else if(l<r){motor(L1,L2,0);motor(R1,R2,1);} else {motor(L1,L2,1);motor(R1,R2,0);} delay(20);}\n'''
    else:
        if platform == 'esp32':
            code='''// RoboLab generated ESP32 project starter\nvoid setup(){Serial.begin(115200);}\nvoid loop(){// Add sensor/actuator logic here\n delay(50);}\n'''
        else:
            code='''// RoboLab generated Arduino project starter\nvoid setup(){Serial.begin(9600);}\nvoid loop(){// Add sensor/actuator logic here\n delay(50);}\n'''
    return {'platform':platform,'project':project,'language':'Arduino C++','code':code}


def circuit_svg(project: str):
    d=project.lower(); nodes=[('Controller','Arduino UNO','90','70'),('Power','Battery','90','250')]
    if 'line' in d:
        nodes += [('Sensors','IR Array','420','70'),('Driver','L298N','420','250'),('Actuators','2x TT Motors','700','160')]
    elif 'quadruped' in d:
        nodes += [('Driver','PCA9685','420','70'),('Sensors','MPU6050','420','250'),('Actuators','12x MG996R','700','160')]
    else:
        nodes += [('Sensor','HC-SR04','420','70'),('Driver','L298N','420','250'),('Actuator','Motors','700','160')]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="380" viewBox="0 0 900 380">','<rect width="100%" height="100%" fill="#09111d"/>','<style>text{font-family:Arial;fill:#e7f4ff} .box{fill:#101d2d;stroke:#39b7ff;stroke-width:2} .line{stroke:#7dd3fc;stroke-width:3;marker-end:url(#a)}</style><defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#7dd3fc"/></marker></defs>']
    for title,label,x,y in nodes:
        svg.append(f'<rect class="box" x="{x}" y="{y}" width="170" height="80" rx="12"/><text x="{int(x)+12}" y="{int(y)+27}" font-size="14">{title}</text><text x="{int(x)+12}" y="{int(y)+53}" font-size="15">{label}</text>')
    for x1,y1,x2,y2 in [('260','110','420','110'),('260','290','420','290'),('590','110','700','170'),('590','290','700','220')]:
        svg.append(f'<line class="line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    svg.append('<text x="30" y="350" font-size="13">RoboLab automatic wiring overview • verify pinout and power ratings before assembly</text></svg>')
    return ''.join(svg)


def cad_scad(project: str):
    p=project.lower(); wheel = 'wheel' in p or 'line' in p or 'obstacle' in p
    if wheel:
        return '''// RoboLab generated OpenSCAD chassis starter\n$fn=64;\nmodule chassis(){ difference(){ cube([140,100,4],center=true); translate([0,0,-2]) cube([110,70,6],center=true); }}\nmodule mount(x,y){ translate([x,y,4]) cylinder(h=8,r=7,center=false); }\nchassis(); mount(-45,-30); mount(45,-30); mount(-45,30); mount(45,30);\n'''
    return '''// RoboLab generated OpenSCAD plate starter\n$fn=64;\ndifference(){ cube([120,90,4],center=true); for(x=[-40,40]) for(y=[-30,30]) translate([x,y,-2]) cylinder(h=8,r=3,center=false); }\n'''


@app.get('/', response_class=HTMLResponse)
async def home(): return (STATIC/'index.html').read_text(encoding='utf-8')

@app.get('/health')
async def health(): return {'status':'online','service':'RoboLab','version':'2.1.0','modules':['planner','availability','firmware','circuit','simulation','cad']}

@app.get('/api/components')
async def components(q:str=''):
    q=q.lower().strip(); data=COMPONENTS if not q else [c for c in COMPONENTS if q in (c['name']+' '+c['category']+' '+' '.join(c['tags'])).lower()]
    return {'components':data}

@app.post('/api/plan')
async def plan(request:Request):
    body=await request.json(); prompt=str(body.get('prompt','')); budget=body.get('budget')
    try: budget=int(budget) if budget not in (None,'') else None
    except: budget=None
    return project_plan(prompt,budget)

@app.post('/api/firmware')
async def firmware(request:Request):
    body=await request.json(); return codegen(str(body.get('platform','arduino')), str(body.get('project','robot project')))

@app.post('/api/circuit')
async def circuit(request:Request):
    body=await request.json(); return Response(circuit_svg(str(body.get('project','robot project'))), media_type='image/svg+xml')

@app.post('/api/cad')
async def cad(request:Request):
    body=await request.json(); return {'format':'OpenSCAD','filename':'robolab_generated.scad','code':cad_scad(str(body.get('project','robot chassis')))}

@app.post('/api/simulate')
async def simulate(request:Request):
    body=await request.json(); project=str(body.get('project','')).lower(); duration=float(body.get('duration',10) or 10); steps=max(20,min(500,int(duration*20)))
    t=[i*duration/(steps-1) for i in range(steps)]; x=[]; y=[]; heading=[]; px=0.0; py=0.0; h=0.0
    for i,_ in enumerate(t):
        if 'line' in project: h=0.12*math.sin(t[i]*2); speed=0.08
        elif 'quadruped' in project: h=0.08*math.sin(t[i]*1.5); speed=0.03
        else: h=0.1*math.sin(t[i]); speed=0.05
        px+=math.cos(h)*speed; py+=math.sin(h)*speed
        x.append(round(px,4)); y.append(round(py,4)); heading.append(round(h,4))
    return {'project':project,'duration_s':duration,'model':'2D kinematic preview','trajectory':{'t':t,'x':x,'y':y,'heading':heading},'note':'Simulation is a lightweight planning preview, not a physics-certified model.'}

@app.get('/api/availability')
async def availability(q:str=''):
    q=q.lower().strip(); matches=[c for c in COMPONENTS if not q or q in (c['name']+' '+' '.join(c['tags'])).lower()]
    live_sources=[]
    if SUPPLIER_FEEDS:
        import urllib.request
        for name,url in SUPPLIER_FEEDS.items():
            try:
                with urllib.request.urlopen(url, timeout=4) as r: payload=json.loads(r.read())
                live_sources.append({'supplier':name,'status':'live','items':payload.get('items',payload)})
            except Exception as exc:
                live_sources.append({'supplier':name,'status':'unavailable','error':str(exc)})
    return {'query':q,'checked_at_utc':__import__('datetime').datetime.utcnow().isoformat()+'Z','source_mode':'live_supplier_feeds' if SUPPLIER_FEEDS else 'local_catalog','suppliers':live_sources,'components':[{'id':c['id'],'name':c['name'],'availability':'catalogued','estimated_price_inr':c['price']} for c in matches]}

@app.get('/api/me')
async def me(request:Request):
    uid=request.session.get('user_id')
    if not uid: return {'authenticated':False}
    con=db(); row=con.execute('SELECT id,email,name,picture FROM users WHERE id=?',(uid,)).fetchone(); con.close()
    return {'authenticated':bool(row),'user':dict(row) if row else None}

@app.get('/api/auth/google')
async def google_login(request:Request):
    cid=os.getenv('GOOGLE_CLIENT_ID'); redirect=os.getenv('GOOGLE_REDIRECT_URI','http://127.0.0.1:8000/api/auth/google/callback')
    if not cid: return JSONResponse({'status':'configuration_required','service':'Google Authentication','google_configured':False},status_code=503)
    state=secrets.token_urlsafe(32); request.session['oauth_state']=state
    params={'client_id':cid,'redirect_uri':redirect,'response_type':'code','scope':'openid email profile','state':state,'access_type':'offline','prompt':'select_account'}
    return RedirectResponse('https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(params))

@app.get('/api/auth/google/callback')
async def google_callback(request:Request):
    code=request.query_params.get('code'); state=request.query_params.get('state')
    if not code or state!=request.session.pop('oauth_state',None): return JSONResponse({'error':'Invalid OAuth state or missing code'},status_code=400)
    import urllib.request
    cid=os.getenv('GOOGLE_CLIENT_ID'); secret=os.getenv('GOOGLE_CLIENT_SECRET'); redirect=os.getenv('GOOGLE_REDIRECT_URI','http://127.0.0.1:8000/api/auth/google/callback')
    if not cid or not secret: return JSONResponse({'error':'Google OAuth is not configured on the server'},status_code=503)
    data=urlencode({'code':code,'client_id':cid,'client_secret':secret,'redirect_uri':redirect,'grant_type':'authorization_code'}).encode()
    try:
        req=urllib.request.Request('https://oauth2.googleapis.com/token',data=data,headers={'Content-Type':'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(req,timeout=10) as r: tokens=json.loads(r.read())
        req=urllib.request.Request('https://openidconnect.googleapis.com/v1/userinfo',headers={'Authorization':'Bearer '+tokens['access_token']})
        with urllib.request.urlopen(req,timeout=10) as r: info=json.loads(r.read())
    except Exception: return JSONResponse({'error':'Google authentication failed'},status_code=502)
    con=db(); con.execute('INSERT INTO users(google_id,email,name,picture) VALUES(?,?,?,?) ON CONFLICT(google_id) DO UPDATE SET email=excluded.email,name=excluded.name,picture=excluded.picture',(info.get('sub'),info.get('email'),info.get('name'),info.get('picture'))); con.commit(); row=con.execute('SELECT id FROM users WHERE google_id=?',(info.get('sub'),)).fetchone(); con.close()
    request.session['user_id']=row['id']; return RedirectResponse('/')

@app.post('/api/auth/logout')
async def logout(request:Request): request.session.clear(); return {'ok':True}

@app.get('/api/location')
async def location(): return {'privacy':'Location is optional and permission-based. Use browser geolocation only when the user explicitly chooses it.','regional_pricing':'Demo estimates use INR and should be replaced with live regional data before commercial launch.'}
