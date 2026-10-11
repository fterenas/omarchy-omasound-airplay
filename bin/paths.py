"""Shared, user-specific paths. No files are created by importing this module."""
import os
from pathlib import Path
STATE_DIR = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state')))/'omasound-airplay'
CACHE_DIR = Path(os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache')))/'omasound-airplay'
RUNTIME_DIR = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))/'omasound-airplay'
SENDER = Path('/usr/local/lib/omasound-airplay/cliairplay')
VERSION = '0.5.5'
HASHES = {
 'x86_64': 'd5302f0b9f24fd8a045a75bf919c1345af38c88487d817928ddb91edc475af07',
 'aarch64': '57f362ab09c01e069f6691abcef193bb5e49ff8146feb697881e166a153a6c01',
}
