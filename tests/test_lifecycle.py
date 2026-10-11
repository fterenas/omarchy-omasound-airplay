"""Exercise real worker shutdown after its wrapper disappears, with fake audio tools."""
import os, subprocess, sys, tempfile, time, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class LifecycleTests(unittest.TestCase):
 def test_worker_exits_when_wrapper_is_killed(self):
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);tools=tmp/'tools';tools.mkdir();runtime=tmp/'runtime';runtime.mkdir(mode=0o700)
   pactl=tools/'pactl'
   pactl.write_text('#!'+sys.executable+'\nimport sys,json\nargs=sys.argv[1:]\nif args==["get-default-sink"]:print("alsa_output.test")\nelif args==["--format=json","list","sinks"]:print(json.dumps([{"name":"alsa_output.test","index":1}]))\nelif "list" in args:print("[]")\n')
   pactl.chmod(0o755)
   avahi=tools/'avahi-browse';avahi.write_text('#!/bin/sh\nexit 0\n');avahi.chmod(0o755)
   wrapper=tmp/'wrapper.py'
   wrapper.write_text('import os,subprocess,sys,time\nfrom pathlib import Path\np=subprocess.Popen([sys.executable,sys.argv[1]],env={**os.environ,"OMASOUND_PARENT_PID":str(os.getpid())})\nPath(sys.argv[2]).write_text(str(p.pid))\ntime.sleep(60)\n')
   env={**os.environ,'PATH':str(tools)+':'+os.environ['PATH'],'XDG_STATE_HOME':str(tmp/'state'),'XDG_RUNTIME_DIR':str(runtime)}
   log=(tmp/'log').open('w')
   parent=subprocess.Popen([sys.executable,str(wrapper),str(ROOT/'bin/discovery.py'),str(tmp/'pid')],env=env,stdout=log,stderr=log)
   pid=None
   try:
    for _ in range(50):
     if (tmp/'pid').exists():break
     time.sleep(.05)
    pid=int((tmp/'pid').read_text());time.sleep(.8)
    self.assertEqual(parent.poll(),None)
    self.assertNotEqual(Path(f'/proc/{pid}/stat').read_text().split()[2],'Z')
    parent.kill();parent.wait()
    for _ in range(80):
     status=Path(f'/proc/{pid}/stat')
     if not status.exists() or status.read_text().split()[2]=='Z':break
     time.sleep(.05)
    else:self.fail('Discovery worker survived its wrapper')
    log.flush();self.assertNotIn('Traceback',(tmp/'log').read_text())
   finally:
    if parent.poll() is None:parent.kill();parent.wait()
    if pid:
     try:os.kill(pid,15)
     except ProcessLookupError:pass
    log.close()
if __name__=='__main__':unittest.main()
