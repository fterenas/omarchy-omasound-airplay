import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import remote_volume as v
A='omasound_airplay_112233445566';B='omasound_airplay_223344556677';C='omasound_airplay_aabbccddeeff'
class VolumeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.oldstate,self.oldpath=v.STATE,v.PATH
  v.STATE=Path(self.temp.name);v.PATH=v.STATE/'speaker-volumes.json'
 def tearDown(self):v.STATE,v.PATH=self.oldstate,self.oldpath;self.temp.cleanup()
 def test_independent_levels(self):
  v.update('level',A,35,members=[A,B]);v.update('level',B,70,members=[A,B])
  self.assertEqual(v.settings()['levels'],{A:35,B:70})
 def test_link_sets_and_keeps_equal_without_changing_unselected(self):
  v.update('level',A,35,members=[A,B]);v.update('level',B,70,members=[A,B]);v.update('level',C,20,members=[A,B])
  c=v.update('link',value=True,members=[A,B]);self.assertEqual([c['levels'][n] for n in (A,B)],[53,53])
  c=v.update('level',B,65,members=[A,B]);self.assertEqual([c['levels'][n] for n in (A,B,C)],[65,65,20])
 def test_three_speakers_meet_at_average(self):
  for n,value in [(A,20),(B,60),(C,100)]:v.update('level',n,value,members=[A,B,C])
  c=v.update('link',value=True,members=[A,B,C])
  self.assertEqual([c['levels'][n] for n in (A,B,C)],[60,60,60])
 def test_disabling_sync_preserves_levels(self):
  v.update('level',A,30,members=[A,B]);v.update('level',B,70,members=[A,B])
  v.update('link',value=True,members=[A,B])
  c=v.update('link',value=False,members=[A,B])
  self.assertFalse(c['linked']);self.assertEqual([c['levels'][n] for n in (A,B)],[50,50])
 def test_joining_linked_group_inherits_current_level(self):
  v.update('level',A,55,members=[A]);v.update('link',value=True,members=[A]);v.update('selection',members=[A,B])
  self.assertEqual(v.settings()['levels'][B],55)
if __name__=='__main__':unittest.main()
