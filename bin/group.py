#!/usr/bin/env python3
from paths import STATE_DIR, RUNTIME_DIR, SENDER
import json,os,selectors,signal,subprocess,sys,threading,time
from pathlib import Path
from support import BASE,authorize,command,timing,close_children
from remote_volume import level
receivers=json.loads(sys.argv[1]);sink=sys.argv[2]
stop=False
children=[];streams=[];pipes=[];capture=None;clock=None
relay_error=[]
ready_file=RUNTIME_DIR/'omasound-group-ready.json'
def stopping(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
def relay():
 try:
  while not stop:
   pcm=capture.stdout.read(4096)
   if not pcm:break
   for stream in streams:
    stream['p'].stdin.write(pcm);stream['p'].stdin.flush()
 except (OSError,BrokenPipeError) as e:
  if not stop:relay_error.append(str(e))
try:
 locals=[authorize(r,children,lambda:stop) for r in receivers]
 if len(set(locals))!=1:raise RuntimeError('Selected speakers must be reachable through the same network interface')
 local=locals[0]
 if any(timing(r)[1] for r in receivers):
  clock=subprocess.Popen([str(SENDER),'--ptp-daemon','--if',local,'--debug','3'],stdout=subprocess.DEVNULL,stderr=None);children.append(clock)
  time.sleep(.6)
  if clock.poll() is not None:raise RuntimeError('The shared AirPlay clock could not start')
 sel=selectors.DefaultSelector()
 for r in receivers:
  fifo=RUNTIME_DIR/('omasound-group-'+r['id']+'.fifo')
  if fifo.exists():fifo.unlink()
  os.mkfifo(fifo,0o600);fd=os.open(fifo,os.O_RDWR|os.O_NONBLOCK);pipes.append((fifo,fd))
  p=subprocess.Popen(command(r,local,fifo,shared=True),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);children.append(p)
  os.set_blocking(p.stdout.fileno(),False)
  stream={'p':p,'fd':fd,'name':r['name'],'buf':b'','ready':False,'audio':False,'started':None,'receiver':r,'volume':level(r)}
  streams.append(stream);sel.register(p.stdout,selectors.EVENT_READ,stream)
 capture=subprocess.Popen(['parec','--device='+sink+'.monitor','--format=s16le','--rate=44100','--channels=2','--latency-msec=50'],stdout=subprocess.PIPE);children.append(capture)
 threading.Thread(target=relay,daemon=True).start()
 deadline=time.monotonic()+35;commanded=False;aligned=False;target=None;align_count=0
 while not stop:
  if clock and clock.poll() is not None:raise RuntimeError('The shared AirPlay clock stopped')
  if relay_error:raise RuntimeError('Audio fanout stopped: '+relay_error[0])
  if capture.poll() is not None:raise RuntimeError('Audio capture stopped')
  for stream in streams:
   if stream['p'].poll() is not None:raise RuntimeError(stream['name']+' disconnected')
  if not aligned and time.monotonic()>deadline:raise RuntimeError('Speakers did not become ready together')
  if aligned:
   for stream in streams:
    volume=level(stream['receiver'])
    if volume!=stream['volume']:
     os.write(stream['fd'],f"VOLUME={volume}\n".encode());stream['volume']=volume
  for key,_ in sel.select(.2):
   stream=key.data;stream['buf']+=os.read(key.fileobj.fileno(),8192)
   while b'\n' in stream['buf']:
    raw,stream['buf']=stream['buf'].split(b'\n',1);line=raw.decode(errors='replace')
    print(stream['name']+': '+line,flush=True)
    if '[STATUS] clock_ready' in line and ('state=ready' in line or 'mode=ntp' in line):stream['ready']=True
    if '[STATUS] route protocol=raop' in line:stream['ready']=True
    if '[STATUS] audio ' in line:stream['audio']=True
    if '[STATUS] started' in line:
     fields=dict(x.split('=',1) for x in line.split() if '=' in x)
     stream['started']=int(fields['at_unix_ms'])
  if not commanded and all(s['ready'] and s['audio'] for s in streams):
   target=int(time.time()*1000)+1500
   for s in streams:os.write(s['fd'],f'START_UNIX_MS={target}\nACTION=START\n'.encode())
   commanded=True
  if commanded and not aligned and all(s['started'] is not None for s in streams):
   starts=[s['started'] for s in streams]
   if max(starts)-min(starts)<=2:
    aligned=True
    ready_file.write_text(json.dumps({'pid':os.getpid(),'names':[s['name'] for s in streams],'start_unix_ms':starts}))
    print('GROUP_READY '+json.dumps({'names':[s['name'] for s in streams],'start_unix_ms':starts}),flush=True)
   else:
    align_count+=1
    if align_count>2:raise RuntimeError('Speakers could not agree on a synchronized start')
    target=max(max(starts)+1000,int(time.time()*1000)+1500)
    for s in streams:
     s['started']=None;os.write(s['fd'],f'START_UNIX_MS={target}\nACTION=START\n'.encode())
except InterruptedError:pass
except Exception as e:
 print('Group connection error:',e,flush=True)
 subprocess.run(['notify-send','-u','critical','AirPlay Audio',str(e)])
 sys.exit(1)
finally:
 try:
  if json.loads(ready_file.read_text()).get('pid')==os.getpid():ready_file.unlink()
 except (FileNotFoundError,ValueError):pass
 stop=True
 for fifo,fd in pipes:
  try:os.write(fd,b'ACTION=STOP\n')
  except OSError:pass
 close_children(children)
 for fifo,fd in pipes:
  os.close(fd)
  if fifo.exists():fifo.unlink()
