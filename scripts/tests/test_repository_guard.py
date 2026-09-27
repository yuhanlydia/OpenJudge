import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('guard',Path(__file__).parents[1]/'repository-guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
class GuardTests(unittest.TestCase):
 def test_private_draft_rejected_anywhere(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'draft.json').write_text(json.dumps({'report_id':'r','editorial_state':'draft_private'}))
   self.assertTrue(guard.inspect_files(d,['draft.json']))
 def test_fixture_allowed_only_under_tests(self):
  with tempfile.TemporaryDirectory() as d:
   Path(d,'fixture.json').write_text('{"is_fixture":true}')
   self.assertTrue(guard.inspect_files(d,['fixture.json']))
   Path(d,'tests').mkdir();Path(d,'tests/fixture.json').write_text('{"is_fixture":true}')
   self.assertFalse(guard.inspect_files(d,['tests/fixture.json']))
 def test_private_path_is_rejected(self):
  self.assertTrue(guard.inspect_files('.', ['.cache/report.json']))
