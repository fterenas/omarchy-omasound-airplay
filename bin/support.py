from paths import STATE_DIR, RUNTIME_DIR, SENDER
import ipaddress,json,os,subprocess,time
from pathlib import Path
from remote_volume import level
BASE=Path(__file__).resolve().parent
STATE=STATE_DIR
def run(*args):return subprocess.check_output(args,text=True,timeout=10).strip()
def timing(receiver):
 homepod=receiver['txt'].get('model',receiver['raop'].get('am','')).startswith('AudioAccessory')
 parts=receiver['txt'].get('features','0').split(',')
 try:features=int(parts[0],0)|(int(parts[1],0)<<32 if len(parts)>1 else 0)
 except ValueError:features=0
 return homepod,homepod or bool(features&(1<<41))
def authorize(receiver,children,cancelled):
 ip=str(ipaddress.IPv4Address(receiver['ip']))
 homepod,ptp=timing(receiver)
 config=Path('/etc/ufw/ufw.conf')
 if ptp and config.exists() and 'ENABLED=yes' in config.read_text():
  STATE.mkdir(parents=True,exist_ok=True,mode=0o700)
  allowed=STATE/('firewall-'+ip+'.json')
  if not allowed.exists():
   subprocess.run(['notify-send','OmaSound AirPlay','Allow timing traffic from '+receiver['name']+' in the administrator prompt.'])
   # UFW itself validates the rule. Capture its duplicate-rule response so uninstall
   # never claims ownership of a rule that was already there.
   auth=subprocess.Popen(['pkexec','/usr/bin/ufw','allow','from',ip,'to','any','port','319:320','proto','udp','comment','OmaSound AirPlay'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,'LC_ALL':'C'});children.append(auth)
   while auth.poll() is None and not cancelled():time.sleep(.2)
   if cancelled():raise InterruptedError()
   output=auth.communicate()[0].decode(errors='replace')
   if auth.returncode:raise RuntimeError('Firewall authorization was cancelled: '+output.strip())
   created='Rule added' in output and 'Skipping adding existing rule' not in output
   temporary=allowed.with_suffix('.tmp')
   temporary.write_text(json.dumps({'ip':ip,'created':created}));temporary.chmod(0o600);temporary.replace(allowed)
 return json.loads(run('ip','-j','route','get',ip))[0]['prefsrc']
def command(receiver,local,fifo,shared=False):
 homepod,_=timing(receiver)
 args=[str(SENDER),'--protocol','auto','--port',str(receiver['port']),'--volume',str(level(receiver)),'--debug','3','--name',receiver['name'],'--hostname',receiver['host'],'--if',local,'--txt',' '.join(k+'='+v for k,v in receiver['txt'].items()),'--cmdpipe',str(fifo)]
 if homepod:args+=['--ap2-native','--timing','ptp']
 if shared:args+=['--ptp-shared']
 for key in ('et','md','am','pk','pw','cn'):
  if key in receiver['raop']:args+=['--'+key,receiver['raop'][key]]
 return args+[str(ipaddress.IPv4Address(receiver['ip']))]
def close_children(children):
 for p in reversed(children):
  if p.poll() is None:p.terminate()
 deadline=time.monotonic()+2
 for p in reversed(children):
  if p.poll() is None:
   try:p.wait(max(.01,deadline-time.monotonic()))
   except subprocess.TimeoutExpired:p.kill();p.wait()
