"""Own one discovery worker until the shell closes its stdin or terminates us."""
import os, selectors, signal, subprocess, sys
from pathlib import Path
from paths import RUNTIME_DIR
from setup import health

def main():
 if health():return 1
 RUNTIME_DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
 stopping=False
 def stop(*_):
  nonlocal stopping
  stopping=True
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 sel=selectors.DefaultSelector();sel.register(sys.stdin,selectors.EVENT_READ)
 worker=subprocess.Popen([sys.executable,str(Path(__file__).with_name('discovery.py'))],start_new_session=True,env={**os.environ,"OMASOUND_PARENT_PID":str(os.getpid())})
 try:
  while not stopping and worker.poll() is None:
   if sel.select(.5):
    if not os.read(sys.stdin.fileno(),1024):break
 finally:
  if worker.poll() is None:
   worker.terminate()
   try:worker.wait(15)
   except subprocess.TimeoutExpired:
    os.killpg(worker.pid,signal.SIGKILL);worker.wait()
  sel.close()
 return worker.returncode or 0
if __name__=='__main__':raise SystemExit(main())
