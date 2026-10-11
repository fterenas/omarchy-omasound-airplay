#!/usr/bin/env python3
"""Explicit first-run setup; nothing privileged happens on plugin installation."""
import hashlib, json, os, platform, shutil, stat, subprocess, sys, urllib.request
from pathlib import Path
from paths import CACHE_DIR, HASHES, SENDER, VERSION
COMMANDS = ('avahi-browse','pactl','parec','ip','notify-send','pkexec','getcap')
PACKAGES = ('avahi','libpulse','iproute2','libnotify','polkit','libcap')

def digest(path):
 with path.open('rb') as src:
  return hashlib.file_digest(src,'sha256').hexdigest()

def health():
 errors=[f'Missing {c}' for c in COMMANDS if not shutil.which(c)]
 expected=HASHES.get(platform.machine())
 if expected is None:errors.append('Supported architectures: x86_64 and aarch64')
 try:
  metadata=SENDER.stat()
  if metadata.st_uid!=0 or metadata.st_mode & (stat.S_IWGRP|stat.S_IWOTH):errors.append('Sender must be owned by root and not writable by other users')
  if expected and digest(SENDER)!=expected:errors.append('Sender checksum does not match the pinned release')
  if shutil.which('getcap') and 'cap_net_bind_service=ep' not in subprocess.check_output(['getcap',str(SENDER)],text=True):errors.append('Sender needs timing-port permission')
 except (OSError,subprocess.SubprocessError):errors.append('AirPlay sender is not installed')
 return errors

def privileged(*args):
 # Use the terminal password prompt during setup; receiver connections have no terminal.
 prefix=['sudo'] if sys.stdin.isatty() else ['pkexec']
 subprocess.run(prefix+list(args),check=True)

def setup():
 arch=platform.machine()
 if arch not in HASHES:raise RuntimeError('This release supports x86_64 and aarch64 Linux only.')
 print('OmaSound AirPlay setup\n')
 print('Installs missing audio/discovery packages, enables Avahi, and installs verified cliairplay v'+VERSION+'.')
 print('The root-owned sender receives permission to bind AirPlay timing ports (UDP 319–320).')
 print('When you connect a speaker, an enabled UFW firewall may ask to allow UDP 319–320 from that speaker only.\n')
 if input('Continue? [y/N] ').strip().lower() not in ('y','yes'):return
 if any(not shutil.which(c) for c in COMMANDS):
  privileged('/usr/bin/pacman','-S','--needed',*PACKAGES)
 privileged('/usr/bin/systemctl','enable','--now','avahi-daemon.service')
 CACHE_DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
 asset='cliairplay-linux-'+arch
 target=CACHE_DIR/asset
 temporary=CACHE_DIR/(asset+'.download')
 try:
  url=f'https://github.com/music-assistant/airplay-cli/releases/download/v{VERSION}/{asset}'
  with urllib.request.urlopen(url,timeout=60) as response, temporary.open('wb') as dest:shutil.copyfileobj(response,dest)
  temporary.chmod(0o600)
  if digest(temporary)!=HASHES[arch]:raise RuntimeError('Download checksum mismatch. Nothing has been installed.')
  temporary.replace(target)
 finally:temporary.unlink(missing_ok=True)
 privileged('/usr/bin/install','-d','-o','root','-g','root','-m','0755',str(SENDER.parent))
 privileged('/usr/bin/install','-o','root','-g','root','-m','0755',str(target),str(SENDER))
 if digest(SENDER)!=HASHES[arch]:raise RuntimeError('Installed sender checksum mismatch; timing permission was not granted.')
 privileged('/usr/bin/setcap','cap_net_bind_service=ep',str(SENDER))
 errors=health()
 if errors:raise RuntimeError('; '.join(errors))
 print('\nSetup complete. Open Audio and check the speakers you want to use. Discovery starts within 10 seconds.')

def main():
 if '--check' in sys.argv:
  errors=health();print(json.dumps({'ready':not errors,'issues':errors}));return bool(errors)
 try:setup()
 except (Exception,KeyboardInterrupt) as e:print('\nSetup stopped:',e);return 1
 finally:
  if sys.stdin.isatty():input('\nPress Enter to close. ')
 return 0
if __name__=='__main__':raise SystemExit(main())
