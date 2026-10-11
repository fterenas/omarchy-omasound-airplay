import unittest
from remote_volume import display_level,external_change
class VolumeMetadataTests(unittest.TestCase):
 def test_single_and_group_display(self):
  config={'levels':{'a':30,'b':70}}
  self.assertEqual(display_level(['a'],config),30)
  self.assertEqual(display_level(['a','b'],config),50)
 def test_receiver_change_wins_over_stale_local_zero(self):
  self.assertIsNone(external_change((0,True),(0,True),(43,False)))
 def test_master_slider_and_mute_actions(self):
  self.assertEqual(external_change((43,False),(55,False),(43,False)),('master',55))
  self.assertEqual(external_change((43,False),(43,True),(43,False)),('mute',True))
  self.assertEqual(external_change((0,True),(0,False),(0,True)),('mute',False))
if __name__=='__main__':unittest.main()
