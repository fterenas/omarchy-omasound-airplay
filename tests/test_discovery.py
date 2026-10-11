import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
source=(Path(__file__).resolve().parents[1]/'bin'/'discovery.py').read_text()
ns={'__file__':str(Path(__file__).resolve().parents[1]/'bin'/'discovery.py')}
exec(source[:source.index('threading.Thread')],ns)
class DiscoveryTests(unittest.TestCase):
 def browse(self,raop,airplay):
  with patch.object(ns['subprocess'],'run',side_effect=[SimpleNamespace(returncode=0,stdout=raop),SimpleNamespace(returncode=0,stdout=airplay)]):
   return ns['browse']()
 def test_dual_services_merge_with_full_name(self):
  r=self.browse(r'=;wifi;IPv4;AABBCCDDEEFF\064Dining\032Room;x;local;Dining.local;192.168.1.2;7000;"am=AudioAccessory6,1" "cn=0,1,2,3"',r'=;wifi;IPv4;Dining\032Room;x;local;Dining.local;192.168.1.2;7000;"deviceid=AA:BB:CC:DD:EE:FF" "features=0x200" "osvers=27.0"')
  self.assertEqual(len(r),1);speaker=r['aabbccddeeff']
  self.assertEqual(speaker['name'],'Dining Room');self.assertEqual(speaker['txt']['osvers'],'27.0');self.assertEqual(speaker['raop']['cn'],'0,1,2,3')
 def test_audio_only_and_airplay_only_are_both_listed(self):
  r=self.browse('=;wifi;IPv4;AABBCCDDEEFF@Old Speaker;x;local;old.local;192.168.1.2;5000;"cn=0,1"','=;wifi;IPv4;TV;x;local;tv.local;192.168.1.3;7000;"deviceid=11:22:33:44:55:66" "features=0x200"')
  self.assertEqual(len(r),2);self.assertEqual(r['aabbccddeeff']['name'],'Old Speaker')
 def test_video_only_ipv6_and_malformed_records_are_ignored(self):
  r=self.browse('=;wifi;IPv6;AABBCCDDEEFF@Speaker;x;local;a.local;fe80::1;7000;"cn=1"','\n'.join(['=;wifi;IPv4;Video;x;local;v.local;192.168.1.4;7000;"features=0x1"','=;wifi;IPv4;Broken;x;local;b.local;bad;7000;"features=0x200"','incomplete']))
  self.assertEqual(r,{})
 def test_discovery_failure_preserves_existing_list(self):
  with patch.object(ns['subprocess'],'run',return_value=SimpleNamespace(returncode=1,stdout='')):
   self.assertRaises(RuntimeError,ns['browse'])
if __name__=='__main__':unittest.main()
