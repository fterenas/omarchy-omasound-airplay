#!/usr/bin/env python3
from paths import STATE_DIR, RUNTIME_DIR, SENDER
import ipaddress,json,os,selectors,signal,subprocess,sys,time
from pathlib import Path
from support import authorize,command,close_children
from remote_volume import level
BASE=Path(__file__).resolve().parent
receiver=json.loads(sys.argv[1]);sink=sys.argv[2]
ip=str(ipaddress.IPv4Address(receiver['ip']))
stop=False
children=[]
def stopping(*_):
 global stop
 stop=True
signal.signal(signal.SIGTERM,stopping);signal.signal(signal.SIGINT,stopping)
def check(*args):return subprocess.check_output(args,text=True,timeout=10).strip()
state=STATE_DIR
state.mkdir(parents=True,exist_ok=True,mode=0o700)
fifo=RUNTIME_DIR/('omasound-airplay-'+receiver['id']+'.fifo')
fd=None;sender=None
try:
 local=authorize(receiver,children,lambda:stop)
 if fifo.exists():fifo.unlink()
 os.mkfifo(fifo,0o600);fd=os.open(fifo,os.O_RDWR|os.O_NONBLOCK)
 capture=subprocess.Popen(['parec','--device='+sink+'.monitor','--format=s16le','--rate=44100','--channels=2','--latency-msec=50'],stdout=subprocess.PIPE);children.append(capture)
 last_volume=level(receiver)
 args=command(receiver,local,fifo)
 sender=subprocess.Popen(args,stdin=capture.stdout,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);children.append(sender);capture.stdout.close()
 os.set_blocking(sender.stdout.fileno(),False)
 sel=selectors.DefaultSelector();sel.register(sender.stdout,selectors.EVENT_READ)
 buf=b'';ready=False;audio=False;started=False;connected=False;deadline=time.monotonic()+30
 while not stop:
  if sender.poll() is not None:raise RuntimeError('AirPlay sender exited '+str(sender.returncode))
  if capture.poll() is not None:raise RuntimeError('Audio capture stopped')
  if not connected and time.monotonic()>deadline:raise RuntimeError('AirPlay connection timed out')
  if connected:
   volume=level(receiver)
   if volume!=last_volume:
    os.write(fd,f"VOLUME={volume}\n".encode());last_volume=volume
  for key,_ in sel.select(.25):
   data=os.read(key.fileobj.fileno(),8192)
   buf+=data
   while b'\n' in buf:
    line,buf=buf.split(b'\n',1);line=line.decode(errors='replace')
    print(line,flush=True)
    if '[STATUS] clock_ready' in line and ('state=ready' in line or 'mode=ntp' in line):ready=True
    if '[STATUS] route protocol=raop' in line:ready=True
    if '[STATUS] audio ' in line:audio=True
    if ready and audio and not started:
     os.write(fd,b'START_UNIX_MS=0\nACTION=START\n');started=True
    if '[STATUS] started' in line:connected=True
except InterruptedError:pass
except Exception as e:
 print('Connection error:',e,flush=True)
 subprocess.run(['notify-send','-u','critical','AirPlay Audio',receiver['name']+': '+str(e)])
 sys.exit(1)
finally:
 if sender and sender.poll() is None and fd is not None:
  try:os.write(fd,b'ACTION=STOP\n');sender.wait(2)
  except (OSError,subprocess.TimeoutExpired):pass
 close_children(children)
 if fd is not None:os.close(fd)
 if fifo.exists():fifo.unlink()
