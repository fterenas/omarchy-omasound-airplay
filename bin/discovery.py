#!/usr/bin/env python3
from paths import STATE_DIR, RUNTIME_DIR, SENDER
import ipaddress,json,os,queue,re,shlex,signal,socket,subprocess,threading,time
from pathlib import Path
from remote_volume import settings,display_level,external_change,update
BASE=Path(__file__).resolve().parent
PREFIX='omasound_airplay_'
stop=False
updates=queue.Queue()
def stopping(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
def run(*args):return subprocess.check_output(args,text=True,timeout=10).strip()
def listing(kind):return json.loads(run('pactl','--format=json','list',kind))
def decode(s):return re.sub(r'\\(\d{3})',lambda m:chr(int(m.group(1))),s)
def safe_name(s):return ''.join(c for c in s if c.isprintable() and c not in "'\"\\")[:120] or 'AirPlay Speaker'
def browse():
 found={}
 for service in ('_raop._tcp','_airplay._tcp'):
  result=subprocess.run(['avahi-browse','-rtp',service],capture_output=True,text=True,timeout=10)
  if result.returncode:raise RuntimeError('AirPlay discovery failed')
  for line in result.stdout.splitlines():
   f=line.split(';',9)
   if len(f)!=10 or f[0]!='=' or f[2]!='IPv4':continue
   try:
    ip=str(ipaddress.IPv4Address(f[7]));txt=dict(x.split('=',1) for x in shlex.split(f[9]) if '=' in x)
   except (ValueError,TypeError):continue
   rawname=decode(f[3]);rid=txt.get('deviceid','').replace(':','').lower()
   if service=='_raop._tcp':
    rid=rawname.split('@',1)[0].lower();name=rawname.split('@',1)[-1]
   else:
    name=rawname
    # Audio-capable AirPlay services, including receivers without RAOP records.
    try:audio=bool(int(txt.get('features','0').split(',')[0],0)&(1<<9))
    except ValueError:audio=False
    if not audio:continue
   if not re.fullmatch('[a-f0-9]{12}',rid):rid=ip.replace('.','_')
   r=found.setdefault(rid,{'id':rid,'name':safe_name(name),'ip':ip,'port':int(f[8]),'host':f[6],'txt':{},'raop':{}})
   if service=='_raop._tcp':r['raop']=txt
   else:r.update(name=safe_name(name),txt=txt,port=int(f[8]),host=f[6],ip=ip)
 return found
def discover_loop():
 while not stop:
  try:updates.put(browse())
  except Exception as e:print('Discovery:',e,flush=True)
  for _ in range(40):
   if stop:return
   time.sleep(.5)
threading.Thread(target=discover_loop,daemon=True).start()
# Keep ownership with the discovery worker: shell reloads can kill the wrapper
# before this worker has finished restoring the physical output.
import fcntl
RUNTIME_DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
worker_lock=(RUNTIME_DIR/'worker.lock').open('a')
try:fcntl.flock(worker_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:raise SystemExit(0)
parent_pid=int(os.environ.get('OMASOUND_PARENT_PID',os.getppid()))
def watch_parent():
 while not stop:
  if os.getppid()!=parent_pid:
   stopping();return
  time.sleep(.5)
threading.Thread(target=watch_parent,daemon=True).start()
GROUP=PREFIX+'group'
modules={};receivers={};seen={};active=None;active_names=();fallback=None;failed=()
state=STATE_DIR;state.mkdir(parents=True,exist_ok=True,mode=0o700)
def load(name,default):
 try:return json.loads((state/name).read_text())
 except (FileNotFoundError,ValueError):return default
def save(name,value):
 tmp=state/('.'+name+'.'+str(os.getpid()));tmp.write_text(json.dumps(value));tmp.chmod(0o600);tmp.replace(state/name)
selection=load('selection.json',{})
resume=selection.get('members')
if resume is None:resume=[PREFIX+selection['device']] if selection.get('device') else []
initial=True;volumes=load('volumes.json',{});last_volume_save=0;last_request=load('request.json',{}).get('id')
members=[];persisted=None;mirrored={};settle_until={}

def create_sink(name,label):
 props=' '.join(k+"='"+label+"'" for k in ('device.description','node.description','node.nick'))+' monitor.channel-volumes=false'
 mid=run('pactl','load-module','module-null-sink','sink_name='+name,'rate=44100','channels=2','sink_properties="'+props+'"')
 modules[name]=mid
 targets=members if name==GROUP else [name]
 volume=display_level(targets,settings())
 run('pactl','set-sink-volume',name,str(volume)+'%')
 run('pactl','set-sink-mute',name,'1' if volume==0 else '0')
 mirrored[name]=(volume,volume==0)
 settle_until[name]=time.monotonic()+3
def move(destination,source=None):
 for s in listing('sink-inputs'):
  if source is not None and s['sink']!=source:continue
  app=s.get('properties',{}).get('application.name')
  if app and app!='EasyEffects':subprocess.run(['pactl','move-sink-input',str(s['index']),destination],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def stop_sender():
 global active,active_names
 if active and active.poll() is None:
  active.terminate()
  try:active.wait(12)
  except subprocess.TimeoutExpired:active.kill();active.wait()
 active=None;active_names=()
def restore():
 sinks=listing('sinks');names={s['name'] for s in sinks}
 target=fallback if fallback in names else next((s['name'] for s in sinks if not s['name'].startswith(PREFIX)),None)
 if target:run('pactl','set-default-sink',target);move(target)
def choose(requested):
 global members
 members=list(dict.fromkeys(n for n in requested if n in receivers))[:8]
 save('group.json',members)
 if not members:restore()
 else:
  name=members[0] if len(members)==1 else GROUP
  if name==GROUP and GROUP not in modules:create_sink(GROUP,'AirPlay group')
  run('pactl','set-default-sink',name);move(name)
def chosen(default):
 if default==GROUP:return tuple(n for n in members if n in receivers)
 return (default,) if default in receivers else ()
def sync_volume_metadata(default):
 targets=list(chosen(default));config=settings()
 if config.get('linked') and len(targets)>1 and len({display_level([n],config) for n in targets})>1:
  update('link',value=True,members=targets)
 for sink in listing('sinks'):
  name=sink['name']
  if name not in modules:continue
  targets=list(chosen(default)) if name==GROUP else [name]
  if not targets:continue
  config=settings();volume=display_level(targets,config)
  desired=(volume,volume==0)
  channels=list(sink.get('volume',{}).values())
  actual_volume=round(sum(c['value'] for c in channels)/len(channels)/65536*100) if channels else 0
  actual=(actual_volume,sink['mute'])
  action=external_change(mirrored.get(name),actual,desired) if name==default and time.monotonic()>settle_until.get(name,0) else None
  if action:
   update(action[0],value=action[1],members=targets)
   volume=display_level(targets,settings());desired=(volume,volume==0)
  if actual[0]!=desired[0]:run('pactl','set-sink-volume',name,str(desired[0])+'%')
  if actual[1]!=desired[1]:run('pactl','set-sink-mute',name,'1' if desired[1] else '0')
  mirrored[name]=desired
try:
 while not stop:
  sinks=listing('sinks');names={s['name'] for s in sinks};default=run('pactl','get-default-sink')
  if not default.startswith(PREFIX):fallback=default
  if time.monotonic()-last_volume_save>10:
   for s in sinks:
    if s['name'] in modules:
     channels=list(s.get('volume',{}).values())
     if channels:volumes[s['name']]=round(sum(c['value'] for c in channels)/len(channels)/65536*100)
   save('volumes.json',volumes);last_volume_save=time.monotonic()
  try:
   found=updates.get_nowait();now=time.monotonic()
   for rid,r in found.items():
    name=PREFIX+rid;receivers[name]=r;seen[name]=now
    if name not in modules or name not in names:
     create_sink(name,r['name']);print('Discovered:',r['name'],r['ip'],flush=True)
   for name in list(receivers):
    if now-seen.get(name,0)>45:
     if name in chosen(default):stop_sender()
     if default==name:restore()
     subprocess.run(['pactl','unload-module',modules.pop(name)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
     receivers.pop(name,None);seen.pop(name,None)
     if default==GROUP and name in members:choose(members)
   if initial:
    initial=False
    if resume:choose(resume)
  except queue.Empty:pass
  request=load('request.json',{})
  if request.get('id') and request['id']!=last_request:
   last_request=request['id']
   if isinstance(request.get('members'),list):
    stop_sender();choose(request['members']);failed=();save('ack.json',{'id':last_request})
  default=run('pactl','get-default-sink');desired=chosen(default)
  if active and active.poll() is not None:
   failed=active_names
   if desired==active_names:restore();desired=()
   stop_sender()
  if desired!=active_names:
   stop_sender()
   if desired and desired!=failed:
    active_names=desired
    if len(desired)==1:
     args=['/usr/bin/python3',str(BASE/'sender.py'),json.dumps(receivers[desired[0]]),desired[0]]
    else:
     args=['/usr/bin/python3',str(BASE/'group.py'),json.dumps([receivers[n] for n in desired]),GROUP]
    active=subprocess.Popen(args,start_new_session=True)
    print('Selected:',', '.join(receivers[n]['name'] for n in desired),flush=True)
   elif not desired:failed=()
  if desired!=persisted:
   save('selection.json',{'members':list(desired)});persisted=desired
  sync_volume_metadata(run('pactl','get-default-sink'))
  time.sleep(.7)
finally:
 try:
  if run('pactl','get-default-sink') in modules:restore()
 except Exception:pass
 stop_sender()
 for mid in modules.values():subprocess.run(['pactl','unload-module',mid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
