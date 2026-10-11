#!/usr/bin/env python3
"""Optional dependency cleanup before removing the plugin checkout."""
import ipaddress,json,subprocess,sys
from paths import STATE_DIR,SENDER
from setup import privileged
ID='io.github.fterenas.omasound-airplay'
def main():
 print('Disable OmaSound and remove its dedicated sender. Speaker settings and shared packages are kept.')
 if input('Continue? [y/N] ').strip().lower() not in ('y','yes'):return
 subprocess.run(['omarchy','plugin','disable',ID],check=True)
 # Give the discovery worker time to restore local output and close sender processes.
 import time;time.sleep(15)
 if SENDER.exists():privileged('/usr/bin/rm','--',str(SENDER))
 for receipt in sorted(STATE_DIR.glob('firewall-*.json')):
  data=json.loads(receipt.read_text())
  if not data.get('created'):continue
  ip=str(ipaddress.IPv4Address(data['ip']))
  print('OmaSound added UDP 319–320 from '+ip+'. Other apps might now use this rule.')
  if input('Remove this timing rule? [y/N] ').strip().lower() in ('y','yes'):
   privileged('/usr/bin/ufw','--force','delete','allow','from',ip,'to','any','port','319:320','proto','udp')
   receipt.unlink()
 print('Dependency cleanup complete. You can now remove the plugin through Omarchy settings.')
if __name__=='__main__':
 try:main()
 except (Exception,KeyboardInterrupt) as e:print('Cleanup stopped:',e);raise SystemExit(1)
