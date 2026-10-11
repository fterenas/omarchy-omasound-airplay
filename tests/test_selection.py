import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
source=(Path(__file__).resolve().parents[1]/'bin'/'speaker_select.py').read_text()
ns={'__file__':str(Path(__file__).resolve().parents[1]/'bin'/'speaker_select.py')}
with tempfile.TemporaryDirectory() as initial_state:
 with patch('paths.STATE_DIR',Path(initial_state)):
  exec(source[:source.index("if __name__")],ns)
class SelectionTests(unittest.TestCase):
 def test_single_receiver_is_checked(self):
  with patch.object(ns['subprocess'],'check_output',return_value='omasound_airplay_112233445566\n'):
   self.assertEqual(ns['current'](),['omasound_airplay_112233445566'])
 def test_builtin_output_clears_checkboxes(self):
  with patch.object(ns['subprocess'],'check_output',return_value='alsa_output.example\n'):
   self.assertEqual(ns['current'](),[])
 def test_group_reports_exact_members(self):
  with tempfile.TemporaryDirectory() as d:
   old=ns['STATE'];ns['STATE']=Path(d)
   (Path(d)/'group.json').write_text(json.dumps(['omasound_airplay_112233445566','omasound_airplay_223344556677']))
   try:
    with patch.object(ns['subprocess'],'check_output',return_value='omasound_airplay_group\n'):
     self.assertEqual(len(ns['current']()),2)
   finally:ns['STATE']=old
if __name__=='__main__':unittest.main()
