#!/usr/bin/env python3
from paths import STATE_DIR, RUNTIME_DIR, SENDER
import fcntl,json,os,re,sys
from pathlib import Path
STATE=STATE_DIR
PATH=STATE/'speaker-volumes.json'
PREFIX='omasound_airplay_'
def settings():
 try:return json.loads(PATH.read_text())
 except (FileNotFoundError,ValueError):return {'linked':False,'levels':{}}
def level(receiver):
 return max(0,min(100,int(settings().get('levels',{}).get(PREFIX+receiver['id'],40))))
def display_level(names,config):
 values=[max(0,min(100,int(config.get('levels',{}).get(n,40)))) for n in names]
 return (sum(values)+len(values)//2)//len(values) if values else 0
def external_change(previous,actual,desired):
 if previous is None or desired!=previous:return None
 if actual[0]!=previous[0]:return ('master',actual[0])
 if actual[1]!=previous[1]:return ('mute',actual[1])
 return None
def selected():
 from speaker_select import current
 return current()
def update(action,name=None,value=None,members=None):
 STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
 with (STATE/'speaker-volumes.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  config=settings();levels=config.setdefault('levels',{})
  members=selected() if members is None else members
  if action=='link':
   config['linked']=bool(value)
   if value and members:
    values=[max(0,min(100,int(levels.get(n,40)))) for n in members]
    volume=(sum(values)+len(values)//2)//len(values)
    for n in members:levels[n]=volume
  elif action=='master':
   volume=max(0,min(100,int(value)))
   for n in members:levels[n]=volume
  elif action=='mute':
   remembered=config.setdefault('unmute_levels',{})
   for n in members:
    if value:
     if levels.get(n,40)>0:remembered[n]=levels.get(n,40)
     levels[n]=0
    else:levels[n]=remembered.get(n,40)
  elif action=='level':
   if not re.fullmatch(PREFIX+'(?:[a-f0-9]{12}|[0-9_]+)',name):raise ValueError('Invalid speaker')
   volume=max(0,min(100,int(value)))
   targets=members if config.get('linked') and name in members else [name]
   for n in targets:levels[n]=volume
  elif action=='selection' and config.get('linked') and members:
   volume=levels.get(members[0],40)
   for n in members:levels[n]=volume
  tmp=STATE/('.speaker-volumes.'+str(os.getpid()))
  tmp.write_text(json.dumps(config));tmp.chmod(0o600);tmp.replace(PATH)
  return config
if __name__=='__main__':
 if sys.argv[1]=='status':print(json.dumps(settings()))
 elif sys.argv[1]=='level':print(json.dumps(update('level',sys.argv[2],int(sys.argv[3]))))
 elif sys.argv[1]=='link':print(json.dumps(update('link',value=sys.argv[2]=='1')))
 else:raise SystemExit(2)
