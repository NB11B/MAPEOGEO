import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CommandLineTests(unittest.TestCase):
    def invoke(self, *arguments):
        return subprocess.run([sys.executable, '-m', 'ngc_geometry_lab', *map(str,arguments)], capture_output=True, text=True)

    def test_help(self):
        result = self.invoke('--help')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('analyze', result.stdout)

    def test_example_generation_analysis_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            observation = Path(directory)/'observations.json'
            truth = Path(directory)/'truth.json'
            analysis = Path(directory)/'analysis.json'
            result = self.invoke('generate','--out',observation,'--truth-out',truth,'--cases','6','--shots','8192')
            self.assertEqual(result.returncode, 0, result.stderr)
            result = self.invoke('analyze','--input',observation,'--out',analysis)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(analysis.read_text())
            self.assertEqual(payload['data_kind'], 'synthetic')
            self.assertEqual(len(payload['cases']), 6)
            original = analysis.read_bytes()
            rejected = self.invoke('analyze','--input',observation,'--out',analysis)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(analysis.read_bytes(), original)

    def test_bad_data_reports_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'bad.json'
            path.write_text('{"schema":"wrong"}')
            result = self.invoke('analyze','--input',path,'--out',Path(directory)/'answer.json')
            self.assertEqual(result.returncode, 2)
            self.assertIn('error', result.stderr.lower())
            self.assertNotIn('Traceback', result.stderr)

    def test_truth_and_observation_paths_must_differ(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'same.json'
            result = self.invoke('generate','--out',path,'--truth-out',path,'--cases','2')
            self.assertEqual(result.returncode, 2)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
