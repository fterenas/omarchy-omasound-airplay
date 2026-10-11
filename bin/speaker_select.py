#!/usr/bin/env python3
from paths import STATE_DIR, RUNTIME_DIR, SENDER
import json,os,re,subprocess,sys,time,uuid
from pathlib import Path
STATE=STATE_DIR;PREFIX='omasound_airplay_';GROUP=PREFIX+'group'
STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
def read(name,default):
 try:return json.loads((STATE/name).read_text())
 except (FileNotFoundError,ValueError):return default
def atomic(name,value):
 tmp=STATE/('.'+name+'.'+str(os.getpid()))
 tmp.write_text(json.dumps(value));tmp.chmod(0o600);tmp.replace(STATE/name)
def current():
 pending=read('request.json',{})
 if pending.get('id')!=read('ack.json',{}).get('id') and time.time()-pending.get('time',0)<5:
  return pending.get('members',[])
 default=subprocess.check_output(['pactl','get-default-sink'],text=True,timeout=3).strip()
 if default==GROUP:return read('group.json',[])
 return [default] if re.fullmatch(PREFIX+'(?:[a-f0-9]{12}|[0-9_]+)',default) else []
def main():
 if sys.argv[1]=='status':print(json.dumps(current()))
 elif sys.argv[1] in ('toggle','set'):
  pattern=PREFIX+'(?:[a-f0-9]{12}|[0-9_]+)'
  if sys.argv[1]=='set':members=list(dict.fromkeys(sys.argv[2:]))
  else:
   name=sys.argv[2]
   if not re.fullmatch(pattern,name):raise SystemExit(2)
   members=current()
   if name in members:members.remove(name)
   else:members.append(name)
  if len(members)>8 or any(not re.fullmatch(pattern,n) for n in members):raise SystemExit(2)
  from remote_volume import update
  update('selection',members=members)
  atomic('request.json',{'id':str(uuid.uuid4()),'time':time.time(),'members':members})
  print(json.dumps(members))
 else:raise SystemExit(2)
if __name__=='__main__':main()
