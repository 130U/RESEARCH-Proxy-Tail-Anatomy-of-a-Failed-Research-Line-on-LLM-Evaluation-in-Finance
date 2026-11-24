"""Atomic-result I/O regression tests using real temporary files and injected locks."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from research.planning import run_localization as runner


def sharing_error(code):
    error = PermissionError(13, 'simulated Windows replacement denial')
    error.winerror = code
    return error


class LocalizationWriteTests(unittest.TestCase):
    def test_one_transient_denial_then_actual_atomic_replacement(self):
        original_replace = Path.replace
        for code in (5, 32, 33):
            with self.subTest(winerror=code), TemporaryDirectory() as directory:
                output = Path(directory) / 'result.json'
                output.write_text('{"status":"old"}', encoding='utf-8')
                error = sharing_error(code)
                attempts = []

                def replace_once(source, destination):
                    attempts.append((source, destination))
                    if len(attempts) == 1:
                        raise error
                    return original_replace(source, destination)

                expected = {'status': 'complete', 'value': 'mathematics α≤β'}
                with patch.object(runner, 'OUTPUT', output), \
                     patch.object(Path, 'replace', autospec=True, side_effect=replace_once), \
                     patch.object(runner.time, 'sleep') as sleep:
                    runner._write(expected)
                self.assertEqual(json.loads(output.read_text(encoding='utf-8')), expected)
                self.assertEqual(len(attempts), 2)
                sleep.assert_called_once_with(0.025)
                self.assertFalse(output.with_suffix('.json.tmp').exists())

    def test_persistent_denial_raises_and_preserves_old_committed_state(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            old_bytes = b'{"status":"incomplete"}\n'
            output.write_bytes(old_bytes)
            error = sharing_error(5)
            with patch.object(runner, 'OUTPUT', output), \
                 patch.object(Path, 'replace', autospec=True, side_effect=error) as replace, \
                 patch.object(runner.time, 'sleep') as sleep:
                with self.assertRaises(PermissionError) as caught:
                    runner._write({'status': 'complete'})
            self.assertIs(caught.exception, error)
            self.assertEqual(replace.call_count, 6)
            delays = [call.args[0] for call in sleep.call_args_list]
            self.assertEqual(delays, [0.025, 0.05, 0.1, 0.2, 0.4])
            self.assertLess(sum(delays), 1)
            self.assertEqual(output.read_bytes(), old_bytes)
            self.assertEqual(json.loads(output.with_suffix('.json.tmp').read_text(encoding='utf-8')),
                             {'status': 'complete'})

    def test_other_errors_are_not_retried_or_swallowed(self):
        errors = [sharing_error(87), PermissionError(13, 'no explicit Windows code'),
                  OSError(28, 'no space left')]
        for error in errors:
            with self.subTest(error=repr(error)), TemporaryDirectory() as directory:
                output = Path(directory) / 'result.json'
                output.write_text('{"status":"old"}', encoding='utf-8')
                with patch.object(runner, 'OUTPUT', output), \
                     patch.object(Path, 'replace', autospec=True, side_effect=error) as replace, \
                     patch.object(runner.time, 'sleep') as sleep:
                    with self.assertRaises(type(error)) as caught:
                        runner._write({'status': 'complete'})
                self.assertIs(caught.exception, error)
                self.assertEqual(replace.call_count, 1)
                sleep.assert_not_called()
                self.assertEqual(json.loads(output.read_text(encoding='utf-8')), {'status': 'old'})


if __name__ == '__main__':
    unittest.main()
